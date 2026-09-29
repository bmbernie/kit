#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import subprocess
import time


HELPER = "/usr/local/lib/zerolab/pisugar_read.py"


def run(*args):
    result = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def pisugar_read(operation):
    value = run(
        "sudo",
        "-n",
        HELPER,
        operation,
    )

    if value is None:
        return None

    try:
        return int(value, 16)
    except ValueError:
        return None


def battery_current(high, low):
    if high is None or low is None:
        return None

    if high & 0x20:
        raw = (
            ((high | 0xC0) << 8)
            + low
        )

        if raw & 0x8000:
            raw -= 0x10000
    else:
        raw = (
            ((high & 0x1F) << 8)
            + low
        )

    return round(
        raw * 0.745985 / 1000.0,
        3,
    )


def battery_voltage(high, low):
    if high is None or low is None:
        return None

    if high & 0x20:
        mv = (
            2600.0
            - (((high | 0xC0) << 8) + low)
            * 0.26855
        )
    else:
        mv = (
            2600.0
            + (((high & 0x1F) << 8) + low)
            * 0.26855
        )

    return round(mv / 1000.0, 3)


PISUGAR2_1200_CURVE = (
    (4.16, 100.0),
    (4.05, 95.0),
    (4.00, 80.0),
    (3.92, 65.0),
    (3.86, 40.0),
    (3.79, 25.5),
    (3.66, 10.0),
    (3.52, 6.5),
    (3.49, 3.2),
    (3.10, 0.0),
)


def battery_percent_estimate(voltage):
    """Estimate PiSugar2 1200mAh SOC from battery voltage.

    Uses the vendor PiSugar2 voltage curve and linear
    interpolation. This stateless health collector does
    not yet apply the vendor daemon's rolling smoothing.
    """

    if voltage is None:
        return None

    curve = PISUGAR2_1200_CURVE

    if voltage >= curve[0][0]:
        return curve[0][1]

    if voltage <= curve[-1][0]:
        return curve[-1][1]

    for (v1, p1), (v2, p2) in zip(
        curve,
        curve[1:],
    ):
        if v2 <= voltage <= v1:
            result = (
                p2
                + (p1 - p2)
                * (voltage - v2)
                / (v1 - v2)
            )

            return round(result, 1)

    return None


def meminfo():
    values = {}

    try:
        lines = Path(
            "/proc/meminfo"
        ).read_text().splitlines()

        for line in lines:
            key, value = line.split(":", 1)
            values[key] = value.strip()

    except OSError:
        pass

    return {
        "total": values.get("MemTotal"),
        "available": values.get("MemAvailable"),
        "swap_total": values.get("SwapTotal"),
        "swap_free": values.get("SwapFree"),
    }


def uptime():
    try:
        seconds = float(
            Path(
                "/proc/uptime"
            ).read_text().split()[0]
        )
    except (
        OSError,
        ValueError,
        IndexError,
    ):
        return None

    return round(seconds, 1)


def zerolab_status():
    raw = run(
        "zerolab",
        "status",
        "--json",
    )

    if raw is None:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def collect_pisugar():
    rtc = pisugar_read("rtc")

    low = pisugar_read("power-a2")
    high = pisugar_read("power-a3")

    current_low = pisugar_read("power-a4")
    current_high = pisugar_read("power-a5")

    power_present = (
        low is not None
        and high is not None
    )

    reg55 = None

    if power_present:
        reg55 = pisugar_read("power-55")

    voltage = battery_voltage(
        high,
        low,
    )

    percent = battery_percent_estimate(
        voltage
    )

    current = battery_current(
        current_high,
        current_low,
    )

    # Charging state is deliberately not derived from
    # instantaneous battery current.
    #
    # The PiSugar/IP5209 implementation determines
    # charging on older hardware from voltage history.
    # That requires state across samples and therefore
    # belongs in the persistent ZeroLab power/display
    # controller rather than this stateless collector.
    charging = None

    external = None

    if reg55 is not None:
        external = bool(reg55 & 0x10)

    return {
        "rtc_present": rtc is not None,
        "power_controller_present": power_present,
        "battery_voltage_v": voltage,
        "battery_current_a": current,
        "battery_percent_estimate": percent,
        "battery_charging": charging,
        "charging_input_present": external,
    }


def collect():
    return {
        "timestamp_unix": int(time.time()),
        "zerolab": zerolab_status(),
        "pisugar": collect_pisugar(),
        "raspberry_pi": {
            "throttled": run(
                "vcgencmd",
                "get_throttled",
            ),
            "temperature": run(
                "vcgencmd",
                "measure_temp",
            ),
            "arm_clock_hz": run(
                "vcgencmd",
                "measure_clock",
                "arm",
            ),
            "uptime_seconds": uptime(),
            "memory": meminfo(),
        },
    }


def yes_no(value):
    if value is None:
        return "unknown"

    return "yes" if value else "no"


def main():
    parser = argparse.ArgumentParser(
        prog="zerolab-health",
        description=(
            "ZeroLab read-only health telemetry"
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )

    args = parser.parse_args()

    data = collect()

    if args.json:
        print(
            json.dumps(
                data,
                indent=2,
            )
        )
        return

    zl = data["zerolab"] or {}
    ps = data["pisugar"]
    pi = data["raspberry_pi"]

    voltage = ps["battery_voltage_v"]

    if voltage is None:
        voltage_text = "unavailable"
    else:
        voltage_text = f"{voltage:.3f} V"

    print(
        f"Profile:               "
        f"{zl.get('profile', '-')}"
    )

    print(
        f"UDC state:             "
        f"{zl.get('udc_state', '-')}"
    )

    print(
        f"USB IPv4:              "
        f"{', '.join(zl.get('usb_ipv4', [])) or '-'}"
    )

    print(
        f"PiSugar RTC:           "
        f"{yes_no(ps['rtc_present'])}"
    )

    print(
        f"Power controller:      "
        f"{yes_no(ps['power_controller_present'])}"
    )

    print(
        f"Battery voltage:       "
        f"{voltage_text}"
    )

    print(
        f"PiSugar charge input:  "
        f"{yes_no(ps['charging_input_present'])}"
    )

    print(
        f"Throttling:            "
        f"{pi['throttled'] or '-'}"
    )

    print(
        f"Temperature:           "
        f"{pi['temperature'] or '-'}"
    )

    print(
        f"ARM clock:             "
        f"{pi['arm_clock_hz'] or '-'}"
    )

    print(
        f"Uptime:                "
        f"{pi['uptime_seconds']} s"
    )

    print(
        "Memory available:      "
        f"{pi['memory']['available'] or '-'}"
    )


if __name__ == "__main__":
    main()
