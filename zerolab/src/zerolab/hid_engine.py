#!/usr/bin/env python3

import argparse
import errno
import os
from pathlib import Path
import sys
import time


HID = Path("/dev/hidg0")
REPORT_LEN = 8

MOD_SHIFT = 0x02

RETRY_ERRNOS = {
    errno.ESHUTDOWN,
    errno.ENOTCONN,
    errno.EPIPE,
}


# USB HID boot keyboard usage codes.
KEYS = {
    **{
        chr(ord("a") + i): (0x00, 0x04 + i)
        for i in range(26)
    },

    "1": (0x00, 0x1E),
    "2": (0x00, 0x1F),
    "3": (0x00, 0x20),
    "4": (0x00, 0x21),
    "5": (0x00, 0x22),
    "6": (0x00, 0x23),
    "7": (0x00, 0x24),
    "8": (0x00, 0x25),
    "9": (0x00, 0x26),
    "0": (0x00, 0x27),

    "\n": (0x00, 0x28),
    "\t": (0x00, 0x2B),
    " ":  (0x00, 0x2C),

    "-":  (0x00, 0x2D),
    "=":  (0x00, 0x2E),
    "[":  (0x00, 0x2F),
    "]":  (0x00, 0x30),
    "\\": (0x00, 0x31),
    ";":  (0x00, 0x33),
    "'":  (0x00, 0x34),
    "`":  (0x00, 0x35),
    ",":  (0x00, 0x36),
    ".":  (0x00, 0x37),
    "/":  (0x00, 0x38),

    "!":  (MOD_SHIFT, 0x1E),
    "@":  (MOD_SHIFT, 0x1F),
    "#":  (MOD_SHIFT, 0x20),
    "$":  (MOD_SHIFT, 0x21),
    "%":  (MOD_SHIFT, 0x22),
    "^":  (MOD_SHIFT, 0x23),
    "&":  (MOD_SHIFT, 0x24),
    "*":  (MOD_SHIFT, 0x25),
    "(":  (MOD_SHIFT, 0x26),
    ")":  (MOD_SHIFT, 0x27),

    "_":  (MOD_SHIFT, 0x2D),
    "+":  (MOD_SHIFT, 0x2E),
    "{":  (MOD_SHIFT, 0x2F),
    "}":  (MOD_SHIFT, 0x30),
    "|":  (MOD_SHIFT, 0x31),
    ":":  (MOD_SHIFT, 0x33),
    '"':  (MOD_SHIFT, 0x34),
    "~":  (MOD_SHIFT, 0x35),
    "<":  (MOD_SHIFT, 0x36),
    ">":  (MOD_SHIFT, 0x37),
    "?":  (MOD_SHIFT, 0x38),
}


for i in range(26):
    lower = chr(ord("a") + i)
    upper = lower.upper()

    _, key = KEYS[lower]
    KEYS[upper] = (MOD_SHIFT, key)


RELEASE = bytes(REPORT_LEN)


def require_root():
    if os.geteuid() != 0:
        raise SystemExit(
            "zerolab-hid requires root; use sudo"
        )


def require_hid():
    if not HID.exists():
        raise SystemExit(
            "/dev/hidg0 is absent; activate the HID profile first:\n"
            "  sudo zerolab up hid"
        )


def open_transport(timeout=10.0):
    deadline = time.monotonic() + timeout

    while True:
        try:
            return HID.open("wb", buffering=0)

        except OSError as exc:
            if exc.errno not in RETRY_ERRNOS:
                raise

            if time.monotonic() >= deadline:
                raise SystemExit(
                    f"HID transport did not become writable: {exc}"
                )

            time.sleep(0.25)


def write_report(hid, report, timeout=10.0):
    deadline = time.monotonic() + timeout

    while True:
        try:
            written = hid.write(report)

            if written != REPORT_LEN:
                raise OSError(
                    errno.EIO,
                    f"short HID write: {written}/{REPORT_LEN}",
                )

            return

        except OSError as exc:
            if exc.errno not in RETRY_ERRNOS:
                raise

            if time.monotonic() >= deadline:
                raise

            time.sleep(0.25)


def release_all():
    require_hid()

    with open_transport() as hid:
        write_report(hid, RELEASE)


def encode_char(ch):
    try:
        return KEYS[ch]
    except KeyError:
        raise ValueError(
            f"unsupported character: {ch!r}"
        ) from None


def type_text(text, delay):
    require_hid()

    # Validate before sending anything.
    encoded = [
        encode_char(ch)
        for ch in text
    ]

    hid = open_transport()

    try:
        write_report(hid, RELEASE)
        time.sleep(delay)

        for modifier, key in encoded:
            report = bytes([
                modifier,
                0x00,
                key,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ])

            write_report(hid, report)
            time.sleep(delay)

            write_report(hid, RELEASE)
            time.sleep(delay)

    finally:
        # Best effort release-all even after interrupted/error paths.
        try:
            write_report(hid, RELEASE, timeout=1.0)
        except OSError:
            pass

        hid.close()


def status():
    print(f"Device:  {HID}")
    print(
        f"Present: {'yes' if HID.exists() else 'no'}"
    )

    gadget = Path(
        "/sys/kernel/config/usb_gadget/zerolab/functions/hid.usb0"
    )

    print(
        f"Function: {'yes' if gadget.exists() else 'no'}"
    )


def main():
    parser = argparse.ArgumentParser(
        prog="zerolab-hid",
        description="ZeroLab bounded HID keyboard engine",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "status",
        help="show HID transport status",
    )

    sub.add_parser(
        "release",
        help="send an all-keys-released report",
    )

    type_parser = sub.add_parser(
        "type",
        help="type literal text into the focused host application",
    )

    type_parser.add_argument(
        "text",
        help="literal text to type",
    )

    type_parser.add_argument(
        "--delay",
        type=float,
        default=0.04,
        help="seconds between key reports (default: 0.04)",
    )

    args = parser.parse_args()

    if args.command == "status":
        status()
        return

    require_root()

    if args.command == "release":
        release_all()
        print("PASS: all keys released")
        return

    if args.command == "type":
        if args.delay < 0.005 or args.delay > 1.0:
            raise SystemExit(
                "--delay must be between 0.005 and 1.0 seconds"
            )

        type_text(args.text, args.delay)

        print(
            f"PASS: typed {len(args.text)} characters"
        )


if __name__ == "__main__":
    main()
