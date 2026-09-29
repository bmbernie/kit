#!/usr/bin/env python3

import subprocess
import sys


I2CGET = "/usr/sbin/i2cget"

READS = {
    "rtc": ("0x32", "0x00"),
    "power-a2": ("0x75", "0xa2"),
    "power-a3": ("0x75", "0xa3"),
    "power-a4": ("0x75", "0xa4"),
    "power-a5": ("0x75", "0xa5"),
    "power-55": ("0x75", "0x55"),
}


def main():
    if len(sys.argv) != 2:
        print(
            "usage: pisugar_read.py "
            "{rtc|power-a2|power-a3|power-a4|power-a5|power-55}",
            file=sys.stderr,
        )
        return 2

    operation = sys.argv[1]

    if operation not in READS:
        print(
            f"operation not permitted: {operation}",
            file=sys.stderr,
        )
        return 2

    address, register = READS[operation]

    proc = subprocess.run(
        [
            I2CGET,
            "-y",
            "1",
            address,
            register,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if proc.returncode != 0:
        if proc.stderr:
            print(
                proc.stderr.strip(),
                file=sys.stderr,
            )
        return proc.returncode

    print(proc.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
