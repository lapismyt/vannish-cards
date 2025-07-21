from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw
from PIL.Image import Image as ImageType

from .cache import number_font
from .config import HEIGHT, WIDTH
from .data_types import Background, Rarity, RgbColor, RgbOrRgbaColor


@dataclass
class RenderConfig:
    base_color: RgbColor | str = "#203ed0"
    background_type: Background = "lines"
    rarity: Rarity = "epic"
    nickname: str = "Dungeonerrr"
    number: int | None = 1111


# def prepare_config(config: RenderConfig):
#     if isinstance(config.base_color, str):
#         base_color: tuple[int, int, int] | tuple[int, int, int, int] = (
#             ImageColor.getrgb(config.base_color)
#         )
#         config.base_color = (base_color[0], base_color[1], base_color[2])


def apply_color(img: ImageType, new_color: RgbOrRgbaColor) -> ImageType:
    modified_img = Image.new("RGBA", img.size, (0, 0, 0, 0))

    pixels: Iterable[Iterable[RgbOrRgbaColor]] | None = img.load()
    new_pixels: Iterable[Iterable[RgbOrRgbaColor]] | None = modified_img.load()

    if pixels is None or new_pixels is None:
        raise ValueError("Incorrect image format")

    for x in range(img.width):
        for y in range(img.height):
            pixel = pixels[x, y]

            if pixel[3] <= 0:
                continue

            brightness = sum(pixel[:3]) / 3

            r = int((new_color[0] / 255) * (brightness / 255) * 255)
            g = int((new_color[1] / 255) * (brightness / 255) * 255)
            b = int((new_color[2] / 255) * (brightness / 255) * 255)

            new_pixels[x, y] = (r, g, b, pixel[3])

    return modified_img


def render(config: RenderConfig) -> ImageType:
    """v1.0.2"""

    # prepare_config(config)

    if isinstance(config.base_color, str):
        base_color: RgbOrRgbaColor = ImageColor.getrgb(config.base_color)
    else:
        base_color: RgbOrRgbaColor = config.base_color

    outline = Image.open("assets/outline.png").convert("RGBA")
    outline = apply_color(outline, base_color)
    center = Image.open("assets/center.png").convert("RGBA")
    base = Image.open("assets/base.png").convert("RGBA")
    background = Image.open(f"assets/background/{config.background_type}.png").convert(
        "RGBA"
    )
    background = apply_color(background, base_color)
    skin = Image.open(f"assets/skin/{config.nickname}.png").convert("RGBA")
    nickname = Image.open(f"assets/nickname/{config.nickname}.png").convert("RGBA")
    rarity = Image.open(f"assets/rarity/{config.rarity}.png").convert("RGBA")

    img = Image.new("RGBA", base.size, (0, 0, 0, 0))

    img.paste(outline.convert("RGB"), (0, 0), outline.convert("RGBA"))
    img.paste(center.convert("RGB"), (0, 0), center.convert("RGBA"))
    img.paste(skin.convert("RGB"), (0, 0), skin.convert("RGBA"))
    img.paste(base.convert("RGB"), (0, 0), base.convert("RGBA"))
    img.paste(background.convert("RGB"), (0, 0), background.convert("RGBA"))
    img.paste(nickname.convert("RGB"), (0, 0), nickname.convert("RGBA"))
    img.paste(rarity.convert("RGB"), (0, 0), rarity.convert("RGBA"))

    if config.number is not None:
        num_img = Image.new("RGBA", base.size, (0, 0, 0, 0))
        num_draw = ImageDraw.Draw(num_img)
        num_draw.text(
            (695, 310),
            f"#{config.number}",
            fill=(255, 255, 255, 150),
            align="center",
            font=number_font,
        )

        img.paste(num_img.convert("RGB"), (0, 0), num_img.convert("RGBA"))

    return adjust_resolution(img)


def adjust_resolution(img: ImageType) -> ImageType:
    return img.resize((WIDTH, HEIGHT))


if __name__ == "__main__":
    config = RenderConfig()
    modified_image = render(config)
    modified_image.show()
