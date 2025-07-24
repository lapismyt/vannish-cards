import asyncio
import os
from uuid import uuid4

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)
from aiogram.types import Chat, FSInputFile, InlineKeyboardButton, InputMediaPhoto, User
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hcode, hlink, text
from loguru import logger
from sqlmodel import Session

from .bot import bot
from .config import PAGE_LIMIT, config, get_base_color, hex_to_base_color, index, names
from .data_types import (
    BackgroundEnum,
    BaseColorEnum,
    OpenCard,
    OpenCardsCollection,
    PlayerRarityEnum,
    RarityEnum,
)
from .database import (
    SavedCard,
    SavedUser,
    add_card,
    add_user,
    get_card_by_number,
    get_last_number_card,
    get_user_by_id,
    get_user_cards,
    update_last_card_time,
)
from .randomizer import random_render_config
from .render import RenderConfig, render

gen_card_lock = asyncio.Lock()


async def send_cards_collection(
    session: Session,
    user: SavedUser,
    message_id: int,
    edit_message: bool = False,
    page: int = 1,
):
    cards: list[SavedCard] = get_user_cards(session, user.user_id)
    if len(cards) == 0:
        logger.error("No cards: empty list")
        await bot.send_message(
            config["chat_id"], "Нет карточек", reply_to_message_id=message_id
        )
        return

    start_index = (page * PAGE_LIMIT) - PAGE_LIMIT
    end_index = start_index + PAGE_LIMIT

    if start_index > len(cards):
        if edit_message:
            await bot.edit_message_text(
                chat_id=config["chat_id"],
                text="Карточки закончились",
                message_id=message_id,
            )
        else:
            await bot.send_message(
                config["chat_id"],
                "Карточки закончились",
                reply_to_message_id=message_id,
            )
        return

    if end_index > len(cards):
        end_index = len(cards)

    # logger.info(f"Start index: {start_index}, end index: {end_index}")

    page_cards = cards[start_index:end_index]

    if len(page_cards) == 0:
        logger.error("No cards: empty page")
        if edit_message:
            await bot.edit_message_text(
                chat_id=config["chat_id"], text="Нет карточек", message_id=message_id
            )
        else:
            await bot.send_message(
                config["chat_id"], "Нет карточек", reply_to_message_id=message_id
            )
        return

    kb = InlineKeyboardBuilder()
    for card in page_cards:
        if card.card_id is None:
            continue
        kb.row(
            InlineKeyboardButton(
                text=f"{card.number} / {card.nickname}",
                callback_data=OpenCard(card_id=card.card_id).pack(),
            )
        )

    end_btns = []
    if page > 1:
        end_btns.append(
            InlineKeyboardButton(
                text="<-",
                callback_data=OpenCardsCollection(
                    owner_id=user.user_id, page=page - 1
                ).pack(),
            )
        )

    if end_index < len(cards):
        end_btns.append(
            InlineKeyboardButton(
                text="->",
                callback_data=OpenCardsCollection(
                    owner_id=user.user_id, page=page + 1
                ).pack(),
            )
        )

    if len(end_btns) > 0:
        kb.row(*end_btns)

    if edit_message:
        await bot.edit_message_text(
            chat_id=config["chat_id"],
            text="Список карточек:",
            reply_markup=kb.as_markup(),
            message_id=message_id,
        )
    else:
        await bot.send_message(
            config["chat_id"],
            "Список карточек:",
            reply_markup=kb.as_markup(),
            reply_to_message_id=message_id,
        )
    return


async def send_card_info(
    session: Session,
    card_number: int,
    message_id: int,
    direct: bool = True,
    user_id: int | None = None,
):
    if user_id is None and direct:
        raise ValueError("Direct message must have user_id")

    card: SavedCard | None = get_card_by_number(session, card_number)
    if card is None:
        return await bot.send_message(
            config["chat_id"], "Карточка не найдена", reply_to_message_id=message_id
        )

    if not os.path.exists(f"output/{card.number}.png"):
        await bot.send_chat_action(config["chat_id"], "upload_photo")

        render_config = RenderConfig(
            base_color=get_base_color(card.base_color.value),
            background_type=card.background.value,
            rarity=card.rarity.value,
            nickname=card.nickname,
            number=card.number,
        )

        rendered = render(render_config)

        rendered.save(f"output/{card.number}.png")

    try:
        await bot.send_photo(
            chat_id=config["chat_id"] if not direct else user_id,  # type: ignore
            photo=FSInputFile(f"output/{card.number}.png"),
            caption=get_card_desciption_html(session, card),
            reply_to_message_id=message_id if not direct else None,
            parse_mode="HTML",
        )
    except (TelegramForbiddenError, TelegramNotFound, TelegramBadRequest) as exc:
        logger.warning(repr(exc))
        return False

    return True

    # if direct:
    #     await bot.send_message(card.user_id, f"Карточка #{card.number} отправлена в лс!", reply_to_message_id=message_id)


async def render_custom_card(message_id: int, render_config: RenderConfig, chat_id: int = config["chat_id"]):
    tmsg = await bot.send_message(
        chat_id, "Создаю рендер...", reply_to_message_id=message_id
    )

    rendered = render(render_config)

    uid = str(uuid4())

    rendered.save(f"output/{uid}.png")

    # await bot.send_photo(
    #     chat_id=config["chat_id"],
    #     photo=FSInputFile(f"output/{uid}.png"),
    #     caption=text(hbold("Render UUID:"), hcode(uid)),
    #     reply_to_message_id=message_id,
    #     parse_mode="HTML",
    # )
    await tmsg.edit_media(
        media=InputMediaPhoto(
            media=FSInputFile(f"output/{uid}.png"),
            caption=text(hbold("Render UUID:"), hcode(uid)),
            parse_mode="HTML",
        ),
    )


async def gen_and_send_card(session: Session, user: SavedUser, message_id: int):
    await bot.send_chat_action(config["chat_id"], "upload_photo")
    msg = await bot.send_message(
        config["chat_id"], "Создаю карточку...", reply_to_message_id=message_id
    )

    async with gen_card_lock:
        last_card = get_last_number_card(session)
        if last_card is None:
            number: int = 1
        else:
            if last_card.number is None:
                number: int = 1
            else:
                number: int = last_card.number + 1

        render_config = random_render_config()
        render_config.number = number

        # logger.info(f"Color: {render_config.base_color}")

        rendered = render(render_config)

        if not isinstance(render_config.base_color, str):
            logger.error(f"Invalid base color: {render_config.base_color}")
            raise ValueError("Invalid base color")

        rendered.save(f"output/{number}.png")

        card = SavedCard(
            user_id=user.user_id,
            nickname=render_config.nickname,
            number=number,
            rarity=RarityEnum(render_config.rarity),
            base_color=BaseColorEnum(hex_to_base_color(render_config.base_color)),
            background=BackgroundEnum(render_config.background_type),
        )

        await msg.edit_media(
            media=InputMediaPhoto(
                media=FSInputFile(f"output/{render_config.number}.png"),
                caption=get_card_desciption_html(session, card),
                parse_mode="HTML",
            ),
        )

        add_card(session, card)
        update_last_card_time(session, user.user_id)


async def handle_chat(chat: Chat, enable_private: bool = False) -> bool:
    logger.info(chat.id)

    if chat.type == "private" and enable_private:
        logger.info("Private chat, enabled")
        return True

    if chat.type == "private":
        try:
            await bot.send_message(
                chat.id,
                text("Это бот для чата", hlink("ВАННИШ", "https://t.me/vannishUSE")),
                parse_mode="HTML",
            )
        except (TelegramForbiddenError, TelegramNotFound):
            pass
        return False

    if chat.id != config["chat_id"]:
        try:
            await bot.send_message(chat.id, "Я не могу работать в этом чате!")
        except (TelegramForbiddenError, TelegramNotFound):
            pass

        await bot.leave_chat(chat.id)
        return False

    return True


async def handle_user(session: Session, user: User | None) -> bool:
    if user is None:
        return True
    if user.id == 42777:
        return False
    # print(user.id)
    saved_user: SavedUser | None = get_user_by_id(session, user.id)
    if saved_user is None:
        new_user = SavedUser(user_id=user.id, username=user.username)
        add_user(session, new_user)
        return True
    return True


def player_rarity_by_nickname(nickname: str) -> PlayerRarityEnum | None:
    for player_rarity, player_nicknames in index["players"].items():
        if nickname in player_nicknames:
            return PlayerRarityEnum(player_rarity)
    return None


def get_card_desciption(session: Session, card: SavedCard) -> str:
    msg = f"Номер: #{card.number}\n"

    msg += f"Игрок: {card.nickname}\n"

    base_color_chance = index["chances"]["base_colors"][card.base_color.value]
    msg += (
        f"Цвет: {names['base_colors'][card.base_color.value]} ({base_color_chance}%)\n"
    )

    background_chance = index["chances"]["backgrounds"][card.background.value]
    msg += (
        f"Фон: {names['backgrounds'][card.background.value]} ({background_chance}%)\n"
    )

    rarity_chance = index["chances"]["rarities"][card.rarity.value]
    msg += f"Редкость: {names['rarities'][card.rarity.value]} ({rarity_chance}%)\n"

    owner = get_user_by_id(session, card.user_id)

    if owner is None:
        logger.info(card.user_id)
        return msg

    msg += (
        f"Владелец: {owner.username if owner.username is not None else owner.user_id}\n"
    )

    return msg


def get_card_desciption_html(session: Session, card: SavedCard) -> str:
    # msg = f"Номер: {hcode(str(card.number))}\n"
    msg = text(hbold("Номер:"), "#" + str(card.number), "\n")

    # msg += f"Игрок: {card.nickname}\n"
    msg += text(hbold("Игрок:"), hcode(card.nickname), "\n")

    base_color_chance = index["chances"]["base_colors"][card.base_color.value]
    # msg += f"Цвет: {names['base_colors'][card.base_color.value]} ({base_color_chance}%)\n"
    msg += text(
        hbold("Цвет:"),
        hcode(names["base_colors"][card.base_color.value]),
        f"({base_color_chance}%)\n",
    )

    background_chance = index["chances"]["backgrounds"][card.background.value]
    # msg += f"Фон: {names['backgrounds'][card.background.value]} ({background_chance}%)\n"
    msg += text(
        hbold("Фон:"),
        hcode(names["backgrounds"][card.background.value]),
        f"({background_chance}%)\n",
    )

    rarity_chance = index["chances"]["rarities"][card.rarity.value]
    # msg += f"Редкость: {names['rarities'][card.rarity.value]} ({rarity_chance}%)\n"
    msg += text(
        hbold("Редкость:"),
        hcode(names["rarities"][card.rarity.value]),
        f"({rarity_chance}%)\n",
    )

    owner = get_user_by_id(session, card.user_id)

    if owner is None:
        logger.info(card.user_id)
        return msg

    if owner.username is not None:
        link = f"https://t.me/{owner.username}"
    else:
        link = f"tg://openmessage?user_id={owner.user_id}"

    msg += text(
        hbold("Владелец:"),
        hlink(
            str(owner.username if owner.username is not None else owner.user_id), link
        ),
        "\n",
    )

    return msg
