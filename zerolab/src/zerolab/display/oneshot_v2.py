#!/usr/bin/env python3

import signal
import sys
import time

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

sys.path.insert(
    0,
    "/usr/local/lib/zerolab/display/vendor",
)

from waveshare_epd import epd2in13_V2


class DisplayTimeout(Exception):
    pass


def timeout_handler(signum, frame):
    raise DisplayTimeout(
        "display operation exceeded 45 seconds"
    )


def font(size):
    try:
        return ImageFont.load_default(
            size=size
        )
    except TypeError:
        return ImageFont.load_default()


def centered(draw, canvas_width, y, text, face):
    box = draw.textbbox(
        (0, 0),
        text,
        font=face,
    )

    width = box[2] - box[0]

    draw.text(
        (
            (canvas_width - width) // 2,
            y,
        ),
        text,
        font=face,
        fill=0,
    )


signal.signal(
    signal.SIGALRM,
    timeout_handler,
)

signal.alarm(45)

epd = None
slept = False

try:
    epd = epd2in13_V2.EPD()

    if (epd.width, epd.height) != (122, 250):
        raise RuntimeError(
            "unexpected panel geometry: "
            f"{epd.width}x{epd.height}"
        )

    print(
        f"Panel geometry: "
        f"{epd.width}x{epd.height}"
    )

    print("Initializing FULL_UPDATE")

    result = epd.init(
        epd.FULL_UPDATE
    )

    if result not in (0, None):
        raise RuntimeError(
            f"EPD init returned {result}"
        )

    # Landscape canvas: 250x122.
    image = Image.new(
        "1",
        (
            epd.height,
            epd.width,
        ),
        255,
    )

    draw = ImageDraw.Draw(image)

    width, height = image.size

    draw.rectangle(
        (
            0,
            0,
            width - 1,
            height - 1,
        ),
        outline=0,
    )

    title = font(36)
    small = font(15)

    centered(
        draw,
        width,
        25,
        "ZEROLAB",
        title,
    )

    centered(
        draw,
        width,
        73,
        "WAVESHARE 2.13 V2",
        small,
    )

    centered(
        draw,
        width,
        96,
        "FULL REFRESH",
        small,
    )

    # Previous installation used a 180-degree
    # orientation for this physical HAT.
    image = image.rotate(180)

    print("Sending framebuffer")

    epd.display(
        epd.getbuffer(image)
    )

    print(
        "PASS: full-refresh command completed"
    )

    time.sleep(1)

    print("Entering panel deep sleep")

    epd.sleep()
    slept = True

    print(
        "PASS: panel entered deep sleep"
    )

except BaseException:
    if epd is not None and not slept:
        try:
            epd2in13_V2.epdconfig.module_exit(
                cleanup=True
            )
        except Exception:
            pass

    raise

finally:
    signal.alarm(0)
