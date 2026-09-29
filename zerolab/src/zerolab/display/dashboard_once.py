#!/usr/bin/env python3

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


sys.path.insert(
    0,
    "/usr/local/lib/zerolab/display/vendor",
)

HEALTH = "/usr/local/sbin/zerolab-health"

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

FONT_SANS_BOLD = (
    FONT_DIR + "/DejaVuSans-Bold.ttf"
)

FONT_MONO = (
    FONT_DIR + "/DejaVuSansMono.ttf"
)

FONT_MONO_BOLD = (
    FONT_DIR + "/DejaVuSansMono-Bold.ttf"
)


BACKGROUND = 0
FOREGROUND = 255

PROMPT_USER = os.environ.get("ZEROLAB_PROMPT_USER", "b")


class DisplayTimeout(Exception):
    pass


def alarm_handler(signum, frame):
    raise DisplayTimeout(
        "display operation timed out"
    )


def run(*args):
    proc = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if proc.returncode != 0:
        return None

    return proc.stdout.strip()


def interface_ipv4(interface):
    ip_cmd = (
        shutil.which("ip")
        or "/usr/sbin/ip"
    )

    raw = run(
        ip_cmd,
        "-4",
        "-o",
        "addr",
        "show",
        "dev",
        interface,
        "scope",
        "global",
    )

    if not raw:
        return None

    for line in raw.splitlines():
        fields = line.split()

        if "inet" not in fields:
            continue

        index = fields.index("inet")

        if index + 1 < len(fields):
            return (
                fields[index + 1]
                .split("/", 1)[0]
            )

    return None


def wifi_ipv4():
    iw_cmd = (
        shutil.which("iw")
        or "/usr/sbin/iw"
    )

    raw = run(
        iw_cmd,
        "dev",
        "wlan0",
        "link",
    )

    if not raw:
        return None

    connected = any(
        line.strip().startswith(
            "Connected to "
        )
        for line in raw.splitlines()
    )

    if not connected:
        return None

    return interface_ipv4(
        "wlan0"
    )


def gadget_labels(functions):
    functions = set(
        functions or []
    )

    mappings = (
        ("rndis.", "RNDIS"),
        ("acm.", "ACM"),
        ("hid.", "HID"),
        ("mass_storage.", "STOR"),
    )

    labels = []

    for prefix, label in mappings:
        if any(
            item.startswith(prefix)
            for item in functions
        ):
            labels.append(label)

    return labels


def truetype(path, size):
    return ImageFont.truetype(
        path,
        size=size,
    )


def text_width(draw, text, face):
    box = draw.textbbox(
        (0, 0),
        text,
        font=face,
    )

    return box[2] - box[0]


def fitted_font(
    draw,
    text,
    path,
    maximum_width,
    start_size,
    minimum_size=8,
):
    for size in range(
        start_size,
        minimum_size - 1,
        -1,
    ):
        face = truetype(
            path,
            size,
        )

        if text_width(
            draw,
            text,
            face,
        ) <= maximum_width:
            return face

    return truetype(
        path,
        minimum_size,
    )


def centered_y(
    draw,
    top,
    bottom,
    text,
    face,
):
    box = draw.textbbox(
        (0, 0),
        text,
        font=face,
    )

    glyph_height = (
        box[3] - box[1]
    )

    band_height = (
        bottom - top + 1
    )

    return (
        top
        + (
            band_height
            - glyph_height
        ) // 2
        - box[1]
    )


def main():
    raw = run(
        HEALTH,
        "--json",
    )

    if not raw:
        raise RuntimeError(
            "zerolab-health failed"
        )

    health = json.loads(raw)

    zerolab = (
        health.get("zerolab")
        or {}
    )

    pisugar = (
        health.get("pisugar")
        or {}
    )

    functions = (
        zerolab.get("functions")
        or []
    )

    hostname = socket.gethostname()

    prompt_text = (
        f"{PROMPT_USER}@"
        f"{hostname}:~ $"
    )

    wifi_ip = wifi_ipv4()

    bt_ip = interface_ipv4(
        "bnep0"
    )

    has_rndis = any(
        item.startswith("rndis.")
        for item in functions
    )

    rndis_ip = (
        interface_ipv4("usb0")
        if has_rndis
        else None
    )

    percentage = pisugar.get(
        "battery_percent_estimate"
    )

    charging_override = os.environ.get(
        "ZEROLAB_DISPLAY_CHARGING"
    )

    if charging_override == "1":
        charging = True
    elif charging_override == "0":
        charging = False
    else:
        charging = (
            pisugar.get(
                "battery_charging"
            )
            is True
        )

    battery_prefix = (
        "CHG"
        if charging
        else "BAT"
    )

    if percentage is None:
        battery_text = (
            f"{battery_prefix} --"
        )
    else:
        battery_text = (
            f"{battery_prefix} "
            f"{round(percentage):.0f}%"
        )

    profile = str(
        zerolab.get("profile")
        or "-"
    ).upper()

    usb_state = (
        "UP"
        if zerolab.get(
            "udc_state"
        ) == "configured"
        else "DOWN"
    )

    gadgets = gadget_labels(
        functions
    )

    gadget_text = (
        " ".join(gadgets)
        if gadgets
        else "NONE"
    )

    footer_left = profile

    footer_right = (
        f"{usb_state} "
        f"{gadget_text}"
    )

    print(
        json.dumps(
            {
                "prompt":
                    prompt_text,
                "wifi_ip":
                    wifi_ip,
                "bt_ip":
                    bt_ip,
                "rndis_ip":
                    rndis_ip,
                "battery_percent":
                    percentage,
                "charging":
                    charging,
                "profile":
                    profile,
                "usb_state":
                    usb_state,
                "gadgets":
                    gadgets,
                "center_split_x":
                    167,
            },
            indent=2,
        )
    )

    # Waveshare 2.13 V2 native geometry is 122x250.
    # ZeroLab renders the UI in landscape as 250x122.
    #
    # These constants deliberately avoid constructing an
    # EPD object during frame-only rendering.
    PANEL_WIDTH = 122
    PANEL_HEIGHT = 250

    width = PANEL_HEIGHT
    height = PANEL_WIDTH

    image = Image.new(
        "1",
        (
            width,
            height,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(
        image
    )

    #
    # Approved outer geometry:
    #
    # Header: 24 px
    # Center: 74 px
    # Footer: 24 px
    #

    TOP_BAND = 24
    BOTTOM_BAND = 24

    TOP_SEPARATOR = TOP_BAND

    BOTTOM_START = (
        height - BOTTOM_BAND
    )

    BOTTOM_SEPARATOR = (
        BOTTOM_START - 1
    )

    #
    # Center-pane split:
    #
    # 250 px total width.
    # Split at x=167 gives approximately:
    #
    # left:  2/3
    # right: 1/3
    #

    CENTER_SPLIT_X = 167

    #
    # Border.
    #

    draw.rectangle(
        (
            0,
            0,
            width - 1,
            height - 1,
        ),
        outline=FOREGROUND,
    )

    #
    # Header.
    #

    battery_font = truetype(
        FONT_MONO_BOLD,
        14,
    )

    battery_width = text_width(
        draw,
        battery_text,
        battery_font,
    )

    prompt_max_width = (
        width
        - battery_width
        - 24
    )

    prompt_font = fitted_font(
        draw,
        prompt_text,
        FONT_MONO_BOLD,
        prompt_max_width,
        15,
        10,
    )

    prompt_y = centered_y(
        draw,
        0,
        TOP_BAND - 1,
        prompt_text,
        prompt_font,
    )

    battery_y = centered_y(
        draw,
        0,
        TOP_BAND - 1,
        battery_text,
        battery_font,
    )

    draw.text(
        (
            6,
            prompt_y,
        ),
        prompt_text,
        font=prompt_font,
        fill=FOREGROUND,
    )

    draw.text(
        (
            width
            - battery_width
            - 6,
            battery_y,
        ),
        battery_text,
        font=battery_font,
        fill=FOREGROUND,
    )

    draw.line(
        (
            5,
            TOP_SEPARATOR,
            width - 6,
            TOP_SEPARATOR,
        ),
        fill=FOREGROUND,
    )

    #
    # Center vertical divider.
    #

    draw.line(
        (
            CENTER_SPLIT_X,
            TOP_SEPARATOR + 1,
            CENTER_SPLIT_X,
            BOTTOM_SEPARATOR - 1,
        ),
        fill=FOREGROUND,
    )

    #
    # Network rows.
    #
    # All network information stays
    # inside the left 2/3 pane.
    #

    rows = (
        (
            "WiFi",
            wifi_ip or "--",
        ),
        (
            "BT",
            bt_ip or "--",
        ),
        (
            "RNDIS",
            rndis_ip or "--",
        ),
    )

    row_strings = [
        f"{label:>5}: {value}"
        for label, value in rows
    ]

    longest_row = max(
        row_strings,
        key=len,
    )

    left_text_width = (
        CENTER_SPLIT_X - 14
    )

    row_font = fitted_font(
        draw,
        longest_row,
        FONT_MONO,
        left_text_width,
        14,
        11,
    )

    y_positions = (
        32,
        52,
        72,
    )

    for row_text, y in zip(
        row_strings,
        y_positions,
    ):
        draw.text(
            (
                7,
                y,
            ),
            row_text,
            font=row_font,
            fill=FOREGROUND,
        )

    #
    # Right 1/3 pane intentionally
    # reserved for a future logo,
    # state glyphs, or other indicator.
    #

    #
    # Footer separator.
    #

    draw.line(
        (
            5,
            BOTTOM_SEPARATOR,
            width - 6,
            BOTTOM_SEPARATOR,
        ),
        fill=FOREGROUND,
    )

    #
    # Footer.
    #

    for size in range(
        12,
        7,
        -1,
    ):
        footer_font = truetype(
            FONT_MONO_BOLD,
            size,
        )

        left_width = text_width(
            draw,
            footer_left,
            footer_font,
        )

        right_width = text_width(
            draw,
            footer_right,
            footer_font,
        )

        if (
            left_width
            + right_width
            + 10
            <= width - 12
        ):
            break

    footer_y = centered_y(
        draw,
        BOTTOM_START,
        height - 1,
        footer_left + footer_right,
        footer_font,
    )

    draw.text(
        (
            6,
            footer_y,
        ),
        footer_left,
        font=footer_font,
        fill=FOREGROUND,
    )

    right_width = text_width(
        draw,
        footer_right,
        footer_font,
    )

    draw.text(
        (
            width
            - right_width
            - 6,
            footer_y,
        ),
        footer_right,
        font=footer_font,
        fill=FOREGROUND,
    )

    #
    # Established panel orientation.
    #

    image = image.rotate(
        180
    )

    # Frame-only mode is used by the persistent
    # display service. It renders the approved UI
    # without touching the physical e-paper panel.
    if (
        len(sys.argv) == 3
        and sys.argv[1] == "--save-frame"
    ):
        image.save(
            sys.argv[2],
            format="PNG",
        )

        print(
            f"PASS: frame saved: {sys.argv[2]}"
        )

        return

    # Physical-render mode only.
    #
    # This import intentionally occurs after the frame-only
    # return so --save-frame never opens SPI or claims GPIO.
    from waveshare_epd import epd2in13_V2

    epd = epd2in13_V2.EPD()

    if (
        epd.width,
        epd.height,
    ) != (
        PANEL_WIDTH,
        PANEL_HEIGHT,
    ):
        raise RuntimeError(
            "unexpected panel geometry: "
            f"{epd.width}x{epd.height}"
        )

    signal.signal(
        signal.SIGALRM,
        alarm_handler,
    )

    signal.alarm(45)

    slept = False

    try:
        result = epd.init(
            epd.FULL_UPDATE
        )

        if result not in (
            0,
            None,
        ):
            raise RuntimeError(
                "EPD init returned "
                f"{result}"
            )

        epd.display(
            epd.getbuffer(
                image
            )
        )

        print(
            "PASS: final-layout "
            "dashboard full refresh"
        )

        time.sleep(1)

        epd.sleep()

        slept = True

        print(
            "PASS: panel deep sleep"
        )

    finally:
        signal.alarm(0)

        if not slept:
            try:
                epd2in13_V2.epdconfig.module_exit(
                    cleanup=True
                )
            except Exception:
                pass


if __name__ == "__main__":
    main()
