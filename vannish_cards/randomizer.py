import random
from typing import TypeVar

from .config import get_base_color, index
from .data_types import Background, BaseColor, Rarity
from .render import RenderConfig

KT = TypeVar("KT")


def choose_variant_with_probability(options: dict[KT, int]) -> KT:
    return random.choices(
        population=list(options.keys()), weights=list(options.values()), k=1
    )[0]


def random_render_config() -> RenderConfig:
    total_players = []

    for _, player_nicknames in index["players"].items():
        total_players.extend(player_nicknames)

    base_colors: dict[BaseColor, int] = index["chances"]["base_colors"]
    # player_rarities: dict[PlayerRarity, int] = index["chances"]["players"]
    backgrounds: dict[Background, int] = index["chances"]["backgrounds"]
    rarities: dict[Rarity, int] = index["chances"]["rarities"]

    base_color_name: BaseColor = choose_variant_with_probability(base_colors)
    base_color: str = get_base_color(base_color_name)
    # player_rarity: PlayerRarity = choose_variant_with_probability(player_rarities)
    background: Background = choose_variant_with_probability(backgrounds)
    rarity: Rarity = choose_variant_with_probability(rarities)
    player: str = random.choice(total_players)

    return RenderConfig(
        base_color=base_color,
        background_type=background,
        rarity=rarity,
        nickname=player,
        number=None,
    )
