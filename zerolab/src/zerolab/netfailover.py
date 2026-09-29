#!/usr/bin/env python3

import argparse
from pathlib import Path
import signal
import subprocess
import sys
import time


CONFIG_PATH = Path("/etc/zerolab/netfailover.conf")
running = True


def log(message):
    print(
        f"zerolab-netfailover: {message}",
        flush=True,
    )


def run(command, timeout=20):
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"

    return (
        proc.returncode,
        proc.stdout.strip(),
        proc.stderr.strip(),
    )


def load_config():
    values = {}

    for raw in CONFIG_PATH.read_text().splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise RuntimeError(
                f"invalid configuration line: {raw!r}"
            )

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    required = (
        "WIFI_IFACE",
        "BT_CONNECTION",
        "PHONE_MAC",
        "CHECK_INTERVAL",
        "FAIL_THRESHOLD",
        "RECOVER_THRESHOLD",
        "BT_RETRY_COOLDOWN",
        "STARTUP_GRACE",
    )

    missing = [
        key
        for key in required
        if key not in values
    ]

    if missing:
        raise RuntimeError(
            "missing configuration keys: "
            + ", ".join(missing)
        )

    for key in (
        "CHECK_INTERVAL",
        "FAIL_THRESHOLD",
        "RECOVER_THRESHOLD",
        "BT_RETRY_COOLDOWN",
        "STARTUP_GRACE",
    ):
        values[key] = int(values[key])

    return values


def wifi_associated(interface):
    rc, stdout, _ = run(
        ["iw", "dev", interface, "link"]
    )

    if rc != 0:
        return False

    return any(
        line.strip().startswith("Connected to ")
        for line in stdout.splitlines()
    )


def active_connections():
    rc, stdout, _ = run(
        [
            "nmcli",
            "-t",
            "-f",
            "NAME",
            "connection",
            "show",
            "--active",
        ]
    )

    if rc != 0:
        return set()

    return {
        line
        for line in stdout.splitlines()
        if line
    }


def connection_exists(name):
    rc, _, _ = run(
        [
            "nmcli",
            "connection",
            "show",
            name,
        ]
    )

    return rc == 0


def bluetooth_active(name):
    return name in active_connections()


def prepare_bluetooth():
    rc, _, stderr = run(
        ["rfkill", "unblock", "bluetooth"]
    )

    if rc != 0:
        log(
            "warning: rfkill unblock failed: "
            + (stderr or str(rc))
        )

    rc, stdout, stderr = run(
        ["bluetoothctl", "power", "on"]
    )

    if rc != 0:
        log(
            "warning: Bluetooth power-on failed: "
            + (stderr or stdout or str(rc))
        )


def bluetooth_up(name):
    prepare_bluetooth()

    rc, stdout, stderr = run(
        [
            "nmcli",
            "connection",
            "up",
            "id",
            name,
        ],
        timeout=45,
    )

    if rc == 0:
        log(
            f"Bluetooth fallback activated: {name}"
        )
        return True

    log(
        "Bluetooth fallback activation failed: "
        + (stderr or stdout or f"exit {rc}")
    )

    return False


def bluetooth_down(name):
    if not bluetooth_active(name):
        return True

    rc, stdout, stderr = run(
        [
            "nmcli",
            "connection",
            "down",
            "id",
            name,
        ],
        timeout=30,
    )

    if rc == 0:
        log(
            f"Bluetooth fallback deactivated: {name}"
        )
        return True

    log(
        "Bluetooth fallback deactivation failed: "
        + (stderr or stdout or f"exit {rc}")
    )

    return False


def handle_signal(signum, frame):
    global running
    running = False


def print_status(config):
    wifi = wifi_associated(
        config["WIFI_IFACE"]
    )

    bt = bluetooth_active(
        config["BT_CONNECTION"]
    )

    print(
        f"wifi_interface={config['WIFI_IFACE']}"
    )

    print(
        "wifi_associated="
        + ("yes" if wifi else "no")
    )

    print(
        "bluetooth_connection="
        + config["BT_CONNECTION"]
    )

    print(
        "bluetooth_active="
        + ("yes" if bt else "no")
    )

    print(
        f"phone_mac={config['PHONE_MAC']}"
    )


def controller(config):
    global running

    wifi_interface = config["WIFI_IFACE"]
    bt_connection = config["BT_CONNECTION"]

    interval = config["CHECK_INTERVAL"]
    fail_threshold = config["FAIL_THRESHOLD"]
    recover_threshold = config["RECOVER_THRESHOLD"]
    retry_cooldown = config["BT_RETRY_COOLDOWN"]
    startup_grace = config["STARTUP_GRACE"]

    if not connection_exists(bt_connection):
        log(
            "required NetworkManager profile "
            f"missing: {bt_connection}"
        )
        return 1

    signal.signal(
        signal.SIGTERM,
        handle_signal,
    )

    signal.signal(
        signal.SIGINT,
        handle_signal,
    )

    started = time.monotonic()
    last_bt_attempt = -retry_cooldown

    failures = 0
    recoveries = 0
    last_wifi_state = None

    log(
        "started "
        f"(wifi={wifi_interface}, "
        f"bluetooth={bt_connection}, "
        f"fail-threshold={fail_threshold}, "
        f"recover-threshold={recover_threshold})"
    )

    while running:
        now = time.monotonic()

        associated = wifi_associated(
            wifi_interface
        )

        bt_active = bluetooth_active(
            bt_connection
        )

        if associated != last_wifi_state:
            if associated:
                log(
                    "Wi-Fi association state: connected"
                )
            else:
                log(
                    "Wi-Fi association state: disconnected"
                )

            last_wifi_state = associated

        if associated:
            failures = 0
            recoveries += 1

            if (
                bt_active
                and recoveries >= recover_threshold
            ):
                log(
                    "Wi-Fi recovery threshold reached"
                )

                bluetooth_down(
                    bt_connection
                )

                recoveries = 0

        else:
            recoveries = 0
            failures += 1

            grace_complete = (
                now - started >= startup_grace
            )

            retry_allowed = (
                now - last_bt_attempt
                >= retry_cooldown
            )

            if (
                not bt_active
                and grace_complete
                and failures >= fail_threshold
                and retry_allowed
            ):
                log(
                    "Wi-Fi failure threshold reached; "
                    "attempting Bluetooth fallback"
                )

                last_bt_attempt = now

                bluetooth_up(
                    bt_connection
                )

                failures = 0

        time.sleep(interval)

    log("stopped")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="zerolab-netfailover"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="report state without changing anything",
    )

    args = parser.parse_args()

    try:
        config = load_config()
    except Exception as exc:
        print(
            f"zerolab-netfailover: {exc}",
            file=sys.stderr,
        )
        return 1

    if args.status:
        print_status(config)
        return 0

    return controller(config)


if __name__ == "__main__":
    raise SystemExit(main())
