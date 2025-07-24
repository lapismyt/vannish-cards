from enum import Enum
from typing import Literal, TypeAlias, TypedDict

from aiogram.filters.callback_data import CallbackData

Rarity: TypeAlias = Literal["common", "rare", "epic", "mythic", "legendary"]
BaseColor: TypeAlias = Literal[
    "white", "red", "orange", "yellow", "green", "cyan", "blue", "purple"
]
PlayerRarity: TypeAlias = Literal["often", "common", "rare"]
Background: TypeAlias = Literal[
    "squares", "circles", "triangles", "diamonds", "crystals", "lines"
]


class PlayerRarityEnum(str, Enum):
    OFTEN = "often"
    COMMON = "common"
    RARE = "rare"


class BackgroundEnum(str, Enum):
    SQUARES = "squares"
    CIRCLES = "circles"
    TRIANGLES = "triangles"
    DIAMONDS = "diamonds"
    CRYSTALS = "crystals"
    LINES = "lines"


class RarityEnum(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    MYTHIC = "mythic"
    LEGENDARY = "legendary"


class BaseColorEnum(str, Enum):
    WHITE = "white"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    CYAN = "cyan"
    BLUE = "blue"
    PURPLE = "purple"


RgbColor = tuple[int, int, int]
RgbaColor = tuple[int, int, int, int]
RgbOrRgbaColor = RgbColor | RgbaColor


class Config(TypedDict):
    bot_token: str
    database_uri: str
    owner_id: list[int]
    chat_id: int
    pool_size: int


class Chances(TypedDict):
    base_colors: dict[BaseColor, int]
    players: dict[PlayerRarity, int]
    backgrounds: dict[Background, int]
    rarities: dict[Rarity, int]


class Index(TypedDict):
    chances: Chances
    players: dict[PlayerRarity, list[str]]
    base_colors: dict[BaseColor, str]


class DetailNames(TypedDict):
    rarities: dict[Rarity, str]
    base_colors: dict[BaseColor, str]
    backgrounds: dict[Background, str]


class OpenCardsCollection(CallbackData, prefix="open_collection"):
    owner_id: int
    page: int = 1


class OpenCard(CallbackData, prefix="open_card"):
    card_id: int
