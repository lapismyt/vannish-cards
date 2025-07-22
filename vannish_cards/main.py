import asyncio
from datetime import datetime, timedelta

from aiogram import F
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackQueryFilter
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ErrorEvent,
    Message,
)
from loguru import logger
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from .bot import bot, dp
from .bot_utils import (
    gen_and_send_card,
    handle_chat,
    handle_user,
    render_custom_card,
    send_card_info,
    send_cards_collection,
)
from .config import config, get_base_color
from .data_types import Background, OpenCard, OpenCardsCollection, Rarity
from .database import (
    SavedUser,
    add_user,
    get_user_by_id,
    get_user_by_username,
    update_username,
)
from .filters import validate_user_id, validate_username
from .render import RenderConfig


@dp.chat_member()
async def chat_member(update: ChatMemberUpdated, engine: Engine):
    session = Session(engine)

    if not await handle_chat(update.chat):
        return

    from_user = update.from_user
    if from_user is None:
        return
    if not await handle_user(session, from_user):
        return

    if update.old_chat_member.status in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
    ) and update.new_chat_member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.RESTRICTED,
    ):
        user = get_user_by_id(session, update.new_chat_member.user.id)
        if user is None:
            new_user = SavedUser(
                user_id=update.from_user.id, username=update.from_user.username
            )

            add_user(session, new_user)
            return

    if update.old_chat_member.user.username != update.new_chat_member.user.username:
        update_username(
            session,
            update.new_chat_member.user.id,
            update.new_chat_member.user.username,
        )


@dp.my_chat_member()
async def my_chat_member(update: ChatMemberUpdated, engine: Engine):
    if not await handle_chat(update.chat):
        return

    if update.chat.type == "private":
        return


@dp.message(Command("start"))
async def start(message: Message, engine: Engine):
    session = Session(engine)
    # print(message.chat.id)

    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return

    if not await handle_chat(message.chat):
        return
    from_user = message.from_user
    if from_user is None:
        return
    if not await handle_user(session, from_user):
        return
    # await bot.send_message(message.chat.id, "Привет!")


@dp.message(Command("коллекция", "collection", "карточки", "cards", prefix="/!."))
async def check_collection(message: Message, engine: Engine):
    session = Session(engine)

    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return

    if not await handle_chat(message.chat):
        return
    from_user = message.from_user
    if from_user is None:
        return
    if not await handle_user(session, from_user):
        return
    if message.text is None:
        return
    args: list[str] = message.text.split()
    session = Session(engine)
    if len(args) == 1:
        user: SavedUser | None = get_user_by_id(session, from_user.id)
        if user is None:
            logger.error("User not found")
            return await message.reply("Пользователь не найден!")
    elif args[1].startswith("@"):
        username = args[1][1:]
        if not validate_username(username):
            return await message.reply("Некорректный юзернейм!")
        user: SavedUser | None = get_user_by_username(session, username)
        if user is None:
            return await message.reply("Пользователь не найден!")

    else:
        user_id = args[1]
        if not validate_user_id(user_id):
            return await message.reply("Некорректный ID!")
        user_id = int(user_id)
        user: SavedUser | None = get_user_by_id(session, user_id)
        if user is None:
            return await message.reply("Пользователь не найден!")

    return await send_cards_collection(session, user, message.message_id)


@dp.message(Command("card", "карточка", prefix="/!."))
async def simple_card(message: Message, engine: Engine):
    
    if message.text is None:
        return
    if len(message.text.split()) == 1:
        return await take_card(message, engine)
    return await check_card(message, engine)


@dp.message(
    Command("инфо_карточки", "card_info", "check_card", "карт_инфо", prefix="/!.")
)
async def check_card(message: Message, engine: Engine):
    session = Session(engine)

    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return

    # print(message.chat.id)
    if not await handle_chat(message.chat):
        return
    if not await handle_user(session, message.from_user):
        return
    if message.text is None:
        return
    if len(message.text.split()) == 1:
        return
    args: list[str] = message.text.split()
    if not args[1].isdigit():
        return
    card_number = int(args[1])

    await send_card_info(session, card_number, message.message_id)


@dp.message(
    Command(
        "взять_карточку", "get_card", "получить_карточку", "take_card", prefix="/!."
    )
)
async def take_card(message: Message, engine: Engine):
    session = Session(engine)

    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return

    # print(message.chat.id)
    if not await handle_chat(message.chat):
        return
    if not await handle_user(session, message.from_user):
        return

    if message.from_user is None:
        raise ValueError("User not found")

    saved_user: SavedUser | None = get_user_by_id(session, message.from_user.id)

    if saved_user is None:
        raise ValueError("User not found")

    if saved_user.last_card + timedelta(hours=6) > datetime.now():
        remaining_hours = (
            saved_user.last_card + timedelta(hours=6) - datetime.now()
        ).total_seconds() / 3600
        return await message.reply(
            f"Вы сможете получить карточку только через {round(remaining_hours, 1)} ч."
        )

    return await gen_and_send_card(session, saved_user, message.message_id)


@dp.callback_query(CallbackQueryFilter(callback_data=OpenCardsCollection))
async def cards_collection_callback(callback_query: CallbackQuery, engine: Engine):
    session = Session(engine)

    if callback_query.message is None:
        return

    # print(callback_query.message.chat.id)
    if not await handle_chat(callback_query.message.chat):
        return
    from_user = callback_query.from_user
    if from_user is None:
        return
    if not await handle_user(session, from_user):
        return

    if callback_query.data is None:
        return

    data = OpenCardsCollection.unpack(callback_query.data)
    owner = get_user_by_id(session, data.owner_id)
    if owner is None:
        return
    await send_cards_collection(
        session,
        owner,
        callback_query.message.message_id,
        edit_message=True,
        page=data.page,
    )


@dp.callback_query(CallbackQueryFilter(callback_data=OpenCard))
async def card_callback(callback_query: CallbackQuery, engine: Engine):
    session = Session(engine)

    if callback_query.message is None:
        return

    # print(callback_query.message.chat.id)
    if not await handle_chat(callback_query.message.chat):
        return
    from_user = callback_query.from_user
    if from_user is None:
        return
    if not await handle_user(session, from_user):
        return

    if callback_query.data is None:
        return

    data = OpenCard.unpack(callback_query.data)
    await send_card_info(session, data.card_id, callback_query.message.message_id)

    if isinstance(callback_query.message, Message):
        await callback_query.message.delete()


@dp.message(F.text.lower().strip() == "шанс")
async def chance(message: Message, engine: Engine):
    return await take_card(message, engine)


@dp.message(F.text.lower().startwith("карточка "))
async def card_short(message: Message, engine: Engine):
    return await check_card(message, engine)


@dp.message(F.text.lower().startswith("коллекция"))
async def collection_short(message: Message, engine: Engine):
    return await check_collection(message, engine)


@dp.message(F.text)
async def text_message(message: Message, engine: Engine):
    session = Session(engine)

    if not await handle_chat(message.chat, True):
        return

    from_user = message.from_user
    if from_user is None:
        return

    if not await handle_user(session, from_user):
        return


@dp.message(Command("render", "рендер", prefix="/!."))
async def render_card(message: Message, engine: Engine):
    session = Session(engine)

    # print(message.chat.id)
    if not await handle_chat(message.chat, True):
        return
    from_user = message.from_user
    if from_user is None:
        return
    if not await handle_user(session, from_user):
        return
    if from_user.id not in config["owner_id"]:
        return await message.reply("Только владелец может использовать эту команду")
    if message.text is None:
        return

    args: list[str] = message.text.split()
    if len(args) < 5:
        return await message.reply("Не хватает аргументов")

    if args[1].startswith("#"):
        base_color = args[1]
    else:
        base_color = get_base_color(args[1])  # type: ignore

    background_type: Background = args[2]  # type: ignore
    rarity: Rarity = args[3]  # type: ignore
    nickname: str = args[4]  # type: ignore

    if len(args) == 5:
        number: int | None = None
    else:
        if not args[5].isdigit():
            return await message.reply("Некорректный номер")
        number = int(args[5])

    render_config = RenderConfig(
        base_color=base_color,
        background_type=background_type,
        rarity=rarity,
        nickname=nickname,
        number=number,
    )

    return await render_custom_card(message.message_id, render_config)


@dp.error()
async def error_handler(error: ErrorEvent):
    logger.exception(error.exception)
    await bot.send_message(config["chat_id"], "Что-то пошло не так!")


async def main():
    # for i in range(100):
    #     render_config = random_render_config()
    #     render_config.number = i
    #     print(render_config)
    #     render(render_config).save(f"output/test/{i}.png")

    # render_config = random_render_config()
    # render_config.number = 1
    # render(render_config).show()

    if config["database_uri"].startswith("sqlite"):
        connect_args: dict = {"check_same_thread": False}
    else:
        connect_args: dict = {}

    engine: Engine = create_engine(
        config["database_uri"], connect_args=connect_args, pool_size=config["pool_size"], max_overflow=20
    )

    SQLModel.metadata.create_all(engine)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, engine=engine)


if __name__ == "__main__":
    asyncio.run(main())
