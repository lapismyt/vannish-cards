import json

import toml

from .data_types import BaseColor, Config, DetailNames, Index

PAGE_LIMIT = 6
WIDTH = 1360
HEIGHT = 1927


with open("config.toml", "r") as f:
    config: Config = Config(**toml.load(f))

with open("index.json", "r") as f:
    index: Index = json.load(f)

with open("lang.json", "r") as f:
    names: DetailNames = json.load(f)


def get_base_color(base_color_name: BaseColor) -> str:
    return index["base_colors"][base_color_name]


def hex_to_base_color(hex: str) -> BaseColor:
    for base_color_name, base_color_hex in index["base_colors"].items():
        if hex == base_color_hex:
            return base_color_name
    raise ValueError(f"Invalid hex color: {hex}")
