#!/usr/bin/env python3

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time


PROFILE_DIR = Path("/usr/local/lib/zerolab/profiles")
GADGET = Path("/sys/kernel/config/usb_gadget/zerolab")
UDC_CLASS = Path("/sys/class/udc")
LOCK_PATH = Path("/run/lock/zerolab.lock")

PROFILES = {
    "serial": PROFILE_DIR / "serial-up",
    "ethernet": PROFILE_DIR / "ethernet-up",
    "composite": PROFILE_DIR / "composite-up",
    "hid": PROFILE_DIR / "hid-up",
    "full": PROFILE_DIR / "full-up",
    "full-storage": PROFILE_DIR / "full-storage-up",
    "storage": PROFILE_DIR / "storage-up",
}

DOWN = PROFILE_DIR / "down"


def require_root():
    if os.geteuid() != 0:
        raise SystemExit(
            "zerolab controller must run as root; "
            "use: sudo zerolab ..."
        )


def run(cmd, check=True):
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def lock_controller():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)

    fp = LOCK_PATH.open("a+")

    try:
        fcntl.flock(
            fp.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        fp.close()
        raise SystemExit(
            "another ZeroLab operation is already running"
        )

    return fp


def udc_name():
    devices = sorted(UDC_CLASS.iterdir())

    if not devices:
        return None

    if len(devices) != 1:
        return ",".join(x.name for x in devices)

    return devices[0].name


def udc_state():
    name = udc_name()

    if not name or "," in name:
        return None

    path = UDC_CLASS / name / "state"

    try:
        return path.read_text().strip()
    except OSError:
        return None


def gadget_functions():
    functions = GADGET / "functions"

    if not functions.is_dir():
        return []

    return sorted(
        p.name
        for p in functions.iterdir()
        if p.is_dir()
    )


def infer_profile():
    funcs = set(gadget_functions())

    if not GADGET.exists():
        return "down"

    known = {
        frozenset({"acm.usb0"}): "serial",
        frozenset({"rndis.usb0"}): "ethernet",
        frozenset({"acm.usb0", "rndis.usb0"}): "composite",
        frozenset({"hid.usb0"}): "hid",
        frozenset({"acm.usb0", "hid.usb0", "rndis.usb0"}): "full",
        frozenset({"mass_storage.usb0"}): "storage",
        frozenset({
            "acm.usb0",
            "hid.usb0",
            "mass_storage.usb0",
            "rndis.usb0",
        }): "full-storage",
    }

    return known.get(frozenset(funcs), "unknown")

def usb_ipv4():
    result = run(
        ["ip", "-j", "-4", "addr", "show", "dev", "usb0"],
        check=False,
    )

    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    addresses = []

    for interface in data:
        for addr in interface.get("addr_info", []):
            if addr.get("family") == "inet":
                addresses.append(
                    f"{addr['local']}/{addr['prefixlen']}"
                )

    return addresses


def networkmanager_state():
    result = run(
        [
            "nmcli",
            "-t",
            "-f",
            "GENERAL.STATE,GENERAL.CONNECTION",
            "device",
            "show",
            "usb0",
        ],
        check=False,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def throttled():
    result = run(
        ["vcgencmd", "get_throttled"],
        check=False,
    )

    if result.returncode:
        return None

    return result.stdout.strip()


def status_dict():
    return {
        "profile": infer_profile(),
        "gadget_present": GADGET.exists(),
        "functions": gadget_functions(),
        "udc": udc_name(),
        "udc_state": udc_state(),
        "ttyGS0": Path("/dev/ttyGS0").exists(),
        "hidg0": Path("/dev/hidg0").exists(),
        "usb0": Path("/sys/class/net/usb0").exists(),
        "usb_ipv4": usb_ipv4(),
        "networkmanager": networkmanager_state(),
        "power": throttled(),
    }


def print_status(as_json=False):
    status = status_dict()

    if as_json:
        print(json.dumps(status, indent=2))
        return

    print(f"Profile:       {status['profile']}")
    print(f"Gadget:        {'present' if status['gadget_present'] else 'absent'}")
    print(
        "Functions:     "
        + (
            ", ".join(status["functions"])
            if status["functions"]
            else "-"
        )
    )
    print(f"UDC:           {status['udc'] or '-'}")
    print(f"UDC state:     {status['udc_state'] or '-'}")
    print(f"ttyGS0:        {'yes' if status['ttyGS0'] else 'no'}")
    print(f"hidg0:         {'yes' if status['hidg0'] else 'no'}")
    print(f"usb0:          {'yes' if status['usb0'] else 'no'}")
    print(
        "USB IPv4:      "
        + (
            ", ".join(status["usb_ipv4"])
            if status["usb_ipv4"]
            else "-"
        )
    )
    print(
        "NetworkManager:"
        + (
            f" {status['networkmanager']}"
            if status["networkmanager"]
            else " -"
        )
    )
    print(f"Power:         {status['power'] or '-'}")


def execute_script(path):
    result = subprocess.run(
        [str(path)],
        text=True,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def command_down():
    execute_script(DOWN)


def command_up(profile):
    target = PROFILES[profile]

    current = infer_profile()

    if current == profile:
        print(
            f"ZeroLab profile '{profile}' is already active"
        )
        return

    if current != "down":
        print(f"Stopping current profile: {current}")
        execute_script(DOWN)
        time.sleep(1)

    print(f"Starting profile: {profile}")

    try:
        execute_script(target)
    except BaseException:
        # Fail closed. Do not leave a partial gadget.
        subprocess.run(
            [str(DOWN)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raise


def command_profiles():
    for name in PROFILES:
        print(name)


def main():
    parser = argparse.ArgumentParser(
        prog="zerolab",
        description="ZeroLab USB gadget controller",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    status_parser = sub.add_parser(
        "status",
        help="show current gadget state",
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )

    sub.add_parser(
        "profiles",
        help="list available profiles",
    )

    up_parser = sub.add_parser(
        "up",
        help="activate a profile",
    )
    up_parser.add_argument(
        "profile",
        choices=sorted(PROFILES),
    )

    sub.add_parser(
        "down",
        help="tear down the active gadget",
    )

    args = parser.parse_args()

    if args.command == "status":
        print_status(args.json)
        return

    if args.command == "profiles":
        command_profiles()
        return

    require_root()

    lock = lock_controller()

    try:
        if args.command == "up":
            command_up(args.profile)
        elif args.command == "down":
            command_down()
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    main()
