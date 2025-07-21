from PIL import ImageFont

# images: dict[str, Image.Image] = {}


# img = Image.open("assets/outline.png")
# images["assets/outline.png"] = img
# img = Image.open("assets/center.png")
# images["assets/center.png"] = img
# img = Image.open("assets/base.png")
# images["assets/base.png"] = img


# for rarity in index["chances"]["rarities"].keys():
#     img = Image.open(f"assets/rarity/{rarity}.png")
#     images[f"assets/rarity/{rarity}.png"] = img

# for background in index["chances"]["backgrounds"].keys():
#     img = Image.open(f"assets/background/{background}.png")
#     images[f"assets/background/{background}.png"] = img

# for player_rarity in index["players"].keys():
#     for player in index["players"][player_rarity]:
#         skin_img = Image.open(f"assets/skin/{player}.png")
#         images[f"assets/skin/{player}.png"] = skin_img

#         nickname_img = Image.open(f"assets/nickname/{player}.png")
#         images[f"assets/nickname/{player}.png"] = nickname_img


number_font = ImageFont.truetype("assets/font/DOSIyagiBoldface.ttf", size=58)
