#!/usr/bin/env python3

from collections import deque
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from PIL import Image


sys.path.insert(
    0,
    "/usr/local/lib/zerolab/display/vendor",
)

from waveshare_epd import epd2in13_V2


ZEROLAB = "/usr/local/sbin/zerolab"

RENDERER = (
    "/usr/local/lib/zerolab/display/"
    "dashboard_once.py"
)

IP = "/usr/sbin/ip"
IW = "/usr/sbin/iw"
I2CGET = "/usr/sbin/i2cget"

RUN_DIR = Path(
    "/run/zerolab-display"
)

FRAME_TMP = (
    RUN_DIR / "frame.tmp.png"
)

FRAME = (
    RUN_DIR / "frame.png"
)

LOCK_FILE = (
    "/run/lock/zerolab-display-hw.lock"
)


POLL_INTERVAL = 5.0
BATTERY_SAMPLE_INTERVAL = 5.0
BATTERY_DISPLAY_INTERVAL = 300.0

STARTUP_SETTLE = 5.0

FULL_AFTER_PARTIALS = 20
FULL_MAX_AGE = 6 * 60 * 60


stopping = False
manual_refresh = False


def log(message):
    stamp = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print(
        f"{stamp} zerolab-display: "
        f"{message}",
        flush=True,
    )


def stop_handler(signum, frame):
    global stopping
    stopping = True


def reload_handler(signum, frame):
    global manual_refresh
    manual_refresh = True


def alarm_handler(signum, frame):
    raise TimeoutError(
        "e-paper operation timed out"
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


def run_json(*args):
    raw = run(*args)

    if not raw:
        return None

    try:
        return json.loads(raw)

    except json.JSONDecodeError:
        return None


def interface_ipv4(interface):
    raw = run(
        IP,
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

        index = fields.index(
            "inet"
        )

        if index + 1 < len(fields):
            return (
                fields[index + 1]
                .split("/", 1)[0]
            )

    return None


def wifi_associated():
    raw = run(
        IW,
        "dev",
        "wlan0",
        "link",
    )

    if not raw:
        return False

    return any(
        line.strip().startswith(
            "Connected to "
        )
        for line in raw.splitlines()
    )


def collect_nonbattery():
    status = run_json(
        ZEROLAB,
        "status",
        "--json",
    )

    if status is None:
        status = {}

    return {
        "profile":
            status.get("profile"),

        "udc_state":
            status.get("udc_state"),

        "functions":
            tuple(
                sorted(
                    status.get(
                        "functions",
                        [],
                    )
                )
            ),

        "wifi_associated":
            wifi_associated(),

        "wifi_ip":
            interface_ipv4(
                "wlan0"
            ),

        "bt_ip":
            interface_ipv4(
                "bnep0"
            ),

        "rndis_ip":
            interface_ipv4(
                "usb0"
            ),
    }


def read_i2c(register):
    raw = run(
        I2CGET,
        "-y",
        "1",
        "0x75",
        register,
    )

    if raw is None:
        return None

    try:
        return int(
            raw,
            16,
        )

    except ValueError:
        return None


def decode_voltage(high, low):
    if high is None or low is None:
        return None

    if high & 0x20:
        raw = (
            ((high | 0xC0) << 8)
            + low
        )

        if raw & 0x8000:
            raw -= 0x10000

        mv = (
            2600.0
            - raw * 0.26855
        )

    else:
        raw = (
            ((high & 0x1F) << 8)
            + low
        )

        mv = (
            2600.0
            + raw * 0.26855
        )

    return mv / 1000.0


def battery_probe():
    low = read_i2c("0xa2")
    high = read_i2c("0xa3")
    reg55 = read_i2c("0x55")

    voltage = decode_voltage(
        high,
        low,
    )

    direct_plugged = None

    if reg55 is not None:
        direct_plugged = bool(
            reg55 & 0x10
        )

    return {
        "voltage": voltage,
        "direct_plugged":
            direct_plugged,
    }


class ChargeDetector:
    """
    Stateful IP5209 charging detector.

    PiSugar's older-model implementation determines
    charging from a rising voltage history rather than
    from instantaneous current.

    If the direct 0x55 plug indication is ever observed
    true, we remember that this hardware supports it and
    can subsequently use both edges directly.
    """

    def __init__(self):
        self.voltages = deque(
            maxlen=6
        )

        self.state = False

        self.direct_supported = False

        self.rising_count = 0


    def update(self, probe):
        old_state = self.state

        voltage = probe.get(
            "voltage"
        )

        direct = probe.get(
            "direct_plugged"
        )

        if direct is True:
            self.direct_supported = True
            self.state = True
            self.rising_count = 0

        elif (
            self.direct_supported
            and direct is False
        ):
            self.state = False
            self.rising_count = 0

        elif isinstance(
            voltage,
            (int, float),
        ):
            self.voltages.append(
                float(voltage)
            )

            if len(
                self.voltages
            ) >= 3:
                oldest = (
                    self.voltages[0]
                )

                newest = (
                    self.voltages[-1]
                )

                average = (
                    sum(self.voltages)
                    / len(self.voltages)
                )

                #
                # Mirrors the PiSugar/IP5209
                # charging criterion:
                #
                # oldest < average < newest
                #

                rising = (
                    oldest
                    < average
                    < newest
                )

                if rising:
                    self.rising_count += 1

                    #
                    # Require two rising observations
                    # before entering CHG to suppress
                    # single-sample voltage noise.
                    #

                    if self.rising_count >= 2:
                        self.state = True

                else:
                    #
                    # Falling/flat voltage immediately
                    # exits CHG. This gives prompt
                    # charger-unplug behavior.
                    #

                    self.rising_count = 0
                    self.state = False

        return (
            self.state
            != old_state
        )


def generate_frame(charging):
    RUN_DIR.mkdir(
        mode=0o755,
        parents=True,
        exist_ok=True,
    )

    try:
        FRAME_TMP.unlink()
    except FileNotFoundError:
        pass

    env = os.environ.copy()

    env[
        "ZEROLAB_DISPLAY_CHARGING"
    ] = (
        "1"
        if charging
        else "0"
    )

    proc = subprocess.run(
        [
            "/usr/bin/python3",
            RENDERER,
            "--save-frame",
            str(FRAME_TMP),
        ],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=45,
    )

    if proc.stdout:
        for line in proc.stdout.splitlines():
            log(
                f"renderer: {line}"
            )

    if proc.returncode != 0:
        if proc.stderr:
            for line in proc.stderr.splitlines():
                log(
                    f"renderer-error: "
                    f"{line}"
                )

        raise RuntimeError(
            "frame generation failed: "
            f"{proc.returncode}"
        )

    if not FRAME_TMP.is_file():
        raise RuntimeError(
            "renderer did not produce frame"
        )

    os.replace(
        FRAME_TMP,
        FRAME,
    )

    with Image.open(
        FRAME
    ) as source:
        image = source.convert(
            "1"
        )

        image.load()

    if image.size != (
        250,
        122,
    ):
        raise RuntimeError(
            "unexpected frame geometry: "
            f"{image.size}"
        )

    return image


class Panel:
    def __init__(self):
        self.epd = (
            epd2in13_V2.EPD()
        )

        self.initialized = False
        self.partial_count = 0
        self.last_full = None


    def _buffer(
        self,
        image,
    ):
        return self.epd.getbuffer(
            image
        )


    def full_base(
        self,
        image,
    ):
        log(
            "physical refresh: FULL base"
        )

        signal.alarm(45)

        try:
            result = self.epd.init(
                self.epd.FULL_UPDATE
            )

            if result not in (
                0,
                None,
            ):
                raise RuntimeError(
                    "FULL init failed: "
                    f"{result}"
                )

            self.epd.displayPartBaseImage(
                self._buffer(
                    image
                )
            )

            result = self.epd.init(
                self.epd.PART_UPDATE
            )

            if result not in (
                0,
                None,
            ):
                raise RuntimeError(
                    "PART init failed: "
                    f"{result}"
                )

        finally:
            signal.alarm(0)

        self.initialized = True
        self.partial_count = 0

        self.last_full = (
            time.monotonic()
        )

        log(
            "physical refresh complete: FULL"
        )


    def partial(
        self,
        image,
    ):
        if not self.initialized:
            self.full_base(
                image
            )
            return

        log(
            "physical refresh: PARTIAL"
        )

        signal.alarm(45)

        try:
            self.epd.displayPartial(
                self._buffer(
                    image
                )
            )

        finally:
            signal.alarm(0)

        self.partial_count += 1

        log(
            "physical refresh complete: "
            f"PARTIAL "
            f"({self.partial_count}/"
            f"{FULL_AFTER_PARTIALS})"
        )


    def full_due(self):
        if not self.initialized:
            return True

        if (
            self.partial_count
            >= FULL_AFTER_PARTIALS
        ):
            return True

        if self.last_full is None:
            return True

        return (
            time.monotonic()
            - self.last_full
            >= FULL_MAX_AGE
        )


    def refresh(
        self,
        image,
        reason,
        force_full=False,
    ):
        if (
            force_full
            or self.full_due()
        ):
            log(
                f"refresh reason: "
                f"{reason}; mode=FULL"
            )

            self.full_base(
                image
            )

        else:
            log(
                f"refresh reason: "
                f"{reason}; mode=PARTIAL"
            )

            self.partial(
                image
            )


    def sleep(self):
        if not self.initialized:
            return

        log(
            "placing panel in deep sleep"
        )

        try:
            signal.alarm(15)

            self.epd.sleep()

        except Exception as exc:
            log(
                "panel sleep warning: "
                f"{exc}"
            )

        finally:
            signal.alarm(0)

        self.initialized = False


def sleep_short():
    deadline = (
        time.monotonic()
        + POLL_INTERVAL
    )

    while (
        not stopping
        and time.monotonic()
        < deadline
    ):
        time.sleep(
            min(
                0.25,
                deadline
                - time.monotonic(),
            )
        )


def main():
    global manual_refresh

    signal.signal(
        signal.SIGTERM,
        stop_handler,
    )

    signal.signal(
        signal.SIGINT,
        stop_handler,
    )

    signal.signal(
        signal.SIGUSR1,
        reload_handler,
    )

    signal.signal(
        signal.SIGALRM,
        alarm_handler,
    )

    lock = open(
        LOCK_FILE,
        "a+",
        encoding="utf-8",
    )

    fcntl.flock(
        lock.fileno(),
        fcntl.LOCK_EX,
    )

    panel = Panel()
    detector = ChargeDetector()

    log(
        "starting v0.8d "
        "stateful power/display controller"
    )

    try:
        time.sleep(
            STARTUP_SETTLE
        )

        nonbattery = (
            collect_nonbattery()
        )

        probe = battery_probe()

        detector.update(
            probe
        )

        log(
            "battery probe: "
            f"voltage={probe['voltage']} "
            f"direct={probe['direct_plugged']} "
            f"charging={detector.state}"
        )

        image = generate_frame(
            detector.state
        )

        panel.refresh(
            image,
            "startup",
            force_full=True,
        )

        last_nonbattery = (
            nonbattery
        )

        next_battery_sample = (
            time.monotonic()
            + BATTERY_SAMPLE_INTERVAL
        )

        next_battery_display = (
            time.monotonic()
            + BATTERY_DISPLAY_INTERVAL
        )

        while not stopping:
            now = time.monotonic()

            nonbattery = (
                collect_nonbattery()
            )

            reason = None

            #
            # A manual reload always forces an
            # immediate hardware battery sample
            # before generating the new frame.
            #

            sample_due = (
                manual_refresh
                or now
                >= next_battery_sample
            )

            charging_changed = False

            if sample_due:
                probe = battery_probe()

                charging_changed = (
                    detector.update(
                        probe
                    )
                )

                log(
                    "battery probe: "
                    f"voltage={probe['voltage']} "
                    f"direct={probe['direct_plugged']} "
                    f"charging={detector.state}"
                )

                next_battery_sample = (
                    time.monotonic()
                    + BATTERY_SAMPLE_INTERVAL
                )

            if manual_refresh:
                reason = "manual"

            elif (
                nonbattery
                != last_nonbattery
            ):
                reason = (
                    "network/gadget state"
                )

            elif charging_changed:
                reason = (
                    "charging state"
                )

            elif (
                now
                >= next_battery_display
            ):
                reason = (
                    "battery periodic"
                )

            if reason is not None:
                image = generate_frame(
                    detector.state
                )

                panel.refresh(
                    image,
                    reason,
                )

                last_nonbattery = (
                    nonbattery
                )

                manual_refresh = False

                if (
                    reason
                    == "battery periodic"
                ):
                    next_battery_display = (
                        time.monotonic()
                        + BATTERY_DISPLAY_INTERVAL
                    )

            sleep_short()

    finally:
        panel.sleep()

        fcntl.flock(
            lock.fileno(),
            fcntl.LOCK_UN,
        )

        lock.close()

        log(
            "stopped"
        )


if __name__ == "__main__":
    main()
