import argparse
from datetime import datetime
import os

import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup

from exceptions import URLError


SC_URL = "http://www.stripcreator.com/"
FONT_PATH = os.path.join("resources", "LiberationSans-Bold.ttf")
FONT_SIZE = 12
FONT_TITLE_SIZE = 16
FONT_META_SIZE = 12
TEXT_FG = "#000000"
TEXT_BG = "#FFFFFF"
NARRATION_BG = "#FFFF00"
SPACING = 2
BALLOON_BG = "#FFFFFF"
COMIC_BG = "#000000"
PANEL_TEXT_AREA = 111  # Width provided for text by default


def save_comic(account, id, details=False, obscenities=True):
    url = (SC_URL + "comics/{}/{}/").format(
        account,
        id
    )

    print("Acquiring", url)

    cookies = {"nsfw":1} if obscenities else {}
    r = requests.get(url, cookies=cookies)
    if r.status_code != 200:
        raise URLError("Could not read URL: {}".format(url))

    # Parse the comic's data
    html = BeautifulSoup(r.text, "html.parser")
    comic_info = parse_comic_from_html(html)
    comic_info["sc_id"] = id

    # Acquire needed images
    acquire_comic_images(comic_info)

    # Create the comic
    create_comic(comic_info)

    return True


def parse_comic_from_html(html):
    comic_info = {"panels": []}

    # Title, Author, and Date come from the header
    header = html.find("table", id="comicborder")
    comic_info["title"] = header.a.text
    comic_info["author"] = header.find_all("a")[1].text
    comic_info["date"] = datetime.strptime(
        header.find_all("b")[1].contents[-1],
        "%m-%d-%y"
    ).strftime("%Y-%m-%d")

    # Parse the comic itself
    panels = [
        html.find("td", id="panel1"),
        html.find("td", id="panel2"),
        html.find("td", id="panel3")
    ]

    panel_idx = 0
    for panel in panels:
        # Handle 1/2 panel comics
        if panel is None:
            break

        # Get panel info
        panel_info = {}

        # Background
        background = panel.attrs["background"]
        panel_info["background"] = background.replace(
            SC_URL, ""
        )

        # Narration
        narration = panel.find("span", id="nar{}".format(panel_idx + 1))
        if narration.text:
            panel_info["narration"] = narration.text

        # Dialog
        panel_info["dialog"] = {"left": {}, "right": {}}
        dialog_num = (panel_idx * 2) + 1
        dialog_left = panel.find("span", id="dialog{}".format(dialog_num))
        dialog_right = panel.find("span", id="dialog{}".format(dialog_num + 1))

        panel_info["dialog"]["left"]["text"] = dialog_left.text
        panel_info["dialog"]["right"]["text"] = dialog_right.text

        # Dialog type
        type_left = panel.find("img", id="dtail{}".format(dialog_num))
        type_right = panel.find("img", id="dtail{}".format(dialog_num + 1))

        # Convert to dialog/thought
        if "dialog" in type_left.attrs["src"]:
            type_left = "dialog"
        else:
            type_left = "thought"

        if "dialog" in type_right.attrs["src"]:
            type_right = "dialog"
        else:
            type_right = "thought"

        panel_info["dialog"]["left"]["type"] = type_left
        panel_info["dialog"]["right"]["type"] = type_right

        # Characters
        character_num = (panel_idx * 2) + 1
        character_left = panel.find(
            "img",
            id="char{}".format(character_num)
        )
        character_right = panel.find(
            "img",
            id="char{}".format(character_num + 1)
        )

        panel_info["characters"] = {}
        panel_info["characters"]["left"] = (
            character_left.attrs["src"].replace(SC_URL, "")
        )
        panel_info["characters"]["right"] = (
            character_right.attrs["src"].replace(SC_URL, "")
        )

        # Add panel_info to comic_info
        comic_info["panels"].append(panel_info)

        panel_idx += 1
    return comic_info


def acquire_comic_images(comic_info):
    image_list = ["images/balloon/upperleftcorner.gif"]

    # Populate image list
    for panel in comic_info["panels"]:
        images = [
            panel["background"],
            panel["characters"]["left"],
            panel["characters"]["right"],
            "images/" + panel["dialog"]["left"]["type"] + "-left.gif",
            "images/" + panel["dialog"]["right"]["type"] + "-right.gif"
        ]
        for image in images:
            if image not in image_list:
                image_list.append(image)

    # Download image list
    for image in image_list:
        image_url = image + ""
        if os.sep != "/":
            filepath = image.replace("/", os.sep).replace("images/",
                                                          "resources/")
        else:
            filepath = image.replace("images/", "resources/")

        # Check if the image already exists
        if not os.path.isfile(filepath):
            # Create the path
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Download the image
            r = requests.get(SC_URL + image_url)
            if r.status_code != 200:
                raise URLError(
                    "Could not read URL: {}".format(SC_URL + image_url)
                )

            with open(filepath, "wb") as image_file:
                image_file.write(r.content)
                print("Saved", filepath)
    return True


def create_comic(comic_info):
    # TODO: Actual panel width is based on dialog, 350 is min.
    # TODO: See if oversized BGs are shrunk or if they're clipped
    # 250x350 panels.
    # 7px #000 borders.
    panel_imgs = []

    # Load font -- Stripcreator uses Arial at 10px
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    font_title = ImageFont.truetype(FONT_PATH, FONT_TITLE_SIZE)
    font_meta = ImageFont.truetype(FONT_PATH, FONT_META_SIZE)

    # Assemble panels
    for panel in comic_info["panels"]:
        # Replace /images with /resources
        panel["background"] = (
            panel["background"].replace("images/", "resources/")
        )
        panel["characters"]["left"] = (
            panel["characters"]["left"].replace("images/", "resources/")
        )
        panel["characters"]["right"] = (
            panel["characters"]["right"].replace("images/", "resources/")
        )

        panel["background"] = os.path.normpath(panel["background"])
        panel["characters"]["left"] = os.path.normpath(
            panel["characters"]["left"]
        )
        panel["characters"]["right"] = os.path.normpath(
            panel["characters"]["right"]
        )

        # 103 pixels width for text normally
        widths = {"left": PANEL_TEXT_AREA, "right": PANEL_TEXT_AREA}
        # heights = {"left": 0, "right": 0}
        lines = {"left": [], "right": []}
        sizes = {"left": [], "right": []}

        max_width = {"left": 0, "right": 0}
        total_height = {"left": 0, "right": 0}

        temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))  # Temp image

        # Determine lines
        for dir in ["left", "right"]:
            old = ""
            possible = ""
            for word in panel["dialog"][dir]["text"].split(" "):
                possible = (possible + " " + word).strip()
                text_width, text_height = temp.textsize(possible,
                                                        font=font,
                                                        spacing=SPACING)
                if text_width > widths[dir]:  # Too long
                    lines[dir].append(old)
                    # Reset the line
                    old = ""
                    possible = word
                else:
                    old = possible

            # Flush the last word if needed
            lines[dir].append(possible)

        # Determine sizes
        for dir in ["left", "right"]:
            for line in lines[dir]:
                text_width, text_height = temp.textsize(line,
                                                        font=font,
                                                        spacing=SPACING)
                sizes[dir].append((text_width, text_height))
                total_height[dir] += text_height
                if text_width > max_width[dir]:
                    max_width[dir] = text_width

        # Adjust panel width/height based on dialog stretching
        panel_width = 250 + (206 - widths["left"] - widths["right"])
        panel_height = 350

        # Create a panel image
        panel_img = Image.new("RGB", (panel_width, panel_height))

        # Insert the background (tiled)
        background = Image.open(panel["background"])
        covered_y = 0
        while covered_y < panel_img.height:
            covered_x = 0
            while covered_x < panel_img.width:
                panel_img.paste(background, (covered_x, covered_y))
                covered_x += background.width

            panel_img.paste(background, (0, covered_y))
            covered_y += background.height

        for dir in ["left", "right"]:
            # Insert the character
            character = Image.open(panel["characters"][dir]).convert("RGBA")
            if dir == "left":
                x = 0
                y = panel_img.height - character.height
            elif dir == "right":
                x = panel_img.width - character.width
                y = panel_img.height - character.height
            panel_img.paste(character, (x, y), character)

            # Insert the balloon
            balloon_img = Image.new(
                "RGB",
                (max_width[dir] + 12, total_height[dir] + 12),
                BALLOON_BG
            )
            draw = ImageDraw.Draw(balloon_img)
            # Add balloon border (top, bottom, left, right)
            draw.line(
                [(0, 0), (balloon_img.width, 0)],
                fill="#000000",
                width=2
            )
            draw.line(
                [
                    (0, balloon_img.height - 2),
                    (balloon_img.width, balloon_img.height - 2)
                ],
                fill="#000000",
                width=2
            )
            draw.line(
                [(0, 0), (0, balloon_img.height)],
                fill="#000000",
                width=2
            )
            draw.line(
                [
                    (balloon_img.width - 2, 0),
                    (balloon_img.width - 2, balloon_img.height)
                ],
                fill="#000000",
                width=2
            )

            # Calculate balloon position
            balloon_coords = (x + int(dir == "left") - int(dir == "right"),
                              y - 18 - balloon_img.height)

            # Put BG in the corners (offset by balloon_coords)
            corner_img = Image.open(
                os.path.join("resources", "balloon", "upperleftcorner.gif")
            ).convert("RGBA")
            rotated = corner_img
            corners = [
                (0, balloon_img.height - 6,
                 6, balloon_img.height),  # bl
                (balloon_img.width - 6, balloon_img.height - 6,
                 balloon_img.width, balloon_img.height),  # br
                (balloon_img.width - 6, 0,
                 balloon_img.width, 6),  # tr
                (0, 0,
                 6, 6),  # tl
            ]
            for corner in corners:
                bg_corner = (
                    corner[0] + balloon_coords[0],
                    corner[1] + balloon_coords[1],
                    corner[2] + balloon_coords[0],
                    corner[3] + balloon_coords[1],
                )
                cropped = panel_img.crop(bg_corner)
                balloon_img.paste(cropped, corner)

                # Paste corner image
                rotated = rotated.rotate(90)
                balloon_img.paste(rotated, corner, rotated)

            # Insert the dialog
            dialog_img = Image.new("RGBA",
                                   (max_width[dir], total_height[dir]),
                                   TEXT_BG)
            draw = ImageDraw.Draw(dialog_img)
            y = 0
            line_idx = 0
            for line in lines[dir]:
                x = (dialog_img.width - sizes[dir][line_idx][0]) // 2
                draw.text((x, y), line, TEXT_FG, font=font, spacing=SPACING)
                y += sizes[dir][line_idx][1]
                line_idx += 1

            # Put words in balloon
            balloon_img.paste(dialog_img, (6, 6))

            # Put balloon in panel
            panel_img.paste(balloon_img, balloon_coords)

            # Put tail in panel (easier than resizing balloon_img)
            tail = Image.open(
                ("resources" + os.path.sep +
                 panel["dialog"][dir]["type"] + "-" +
                 dir + ".gif")
            ).convert("RGBA")
            panel_img.paste(
                tail,
                (
                    (balloon_coords[0] +
                     ((balloon_img.width - tail.width) // 2)),
                    (balloon_coords[1] + balloon_img.height - 2)
                ),
                tail
            )

        # Store the panel
        panel_imgs.append(panel_img)

    # Assemble comic
    width = 28  # Four 7px Borders
    height = 350 + 14 + 40 + 7  # Panel + Borders + Header + Header Top Border

    # Calculate dimensions
    for panel in panel_imgs:
        width += panel.width

    # Create Comic Image
    x = 7
    comic = Image.new("RGBA", (width, height), COMIC_BG)

    # Insert Header
    draw = ImageDraw.Draw(comic)
    draw.text((10, 19), comic_info["title"], TEXT_BG, font=font_title)

    author_size = draw.textsize("by " + comic_info["author"], font=font_meta)
    draw.text((comic.width - author_size[0] - 10, 12),
              "by " + comic_info["author"],
              TEXT_BG,
              font=font_meta)
    mdy_date = (comic_info["date"][5:7].lstrip("0") + "-" +
                comic_info["date"][8:] + "-" +
                comic_info["date"][2:4])
    date_size = draw.textsize(mdy_date, font=font_meta)
    draw.text((comic.width - date_size[0] - 10, 12 + author_size[1]),
              mdy_date,
              TEXT_BG,
              font=font_meta)

    # Insert panels
    for panel in panel_imgs:
        comic.paste(panel, (x, 54))
        x += panel.width + 7

    filename = (comic_info["author"].lower() + "-" +
                str(comic_info["sc_id"]) + ".png")
    comic.save(filename)
    print("Saved", filename)
    return True


def main():
    # Parse config
    parser = argparse.ArgumentParser(description="Stripcreator Comic Archiver")
    parser.add_argument("source",
                        help="URL of individual comic or account page: "
                        "http://www.stripcreator.com/comics/myaccount/593635 "
                        "or http://www.stripcreator.com/comics/myaccount/")
    parser.add_argument("-d", "--details",
                        help="Save detailed comic information as JSON data",
                        action="store_true")
    parser.add_argument("-g", "--g-rated",
                        help="Turn on Stripcreator's obscenity filter",
                        action="store_true")

    args = parser.parse_args()
    details = True if args.details else False
    obscenities = False if args.g_rated else False

    # Determine if source is a single strip or complete account
    source = args.source.replace("http://", "").replace("www.", "").rstrip("/")

    # Invalid URL
    if not source.startswith("stripcreator.com/comics/"):
        raise URLError(
            "URL {} is not a valid Stripcreator URL".format(args.source)
        )
    source = source.replace("stripcreator.com/comics/", "")

    # If there's a slash, it's an individual strip, otherwise an account
    if "/" in source:
        account, id = source.split("/", 1)
        save_comic(account, id, details, obscenities)
    else:
        # Save that whole account...
        print("Not yet implemented!")
        None

    return True

if __name__ == "__main__":
    main()
