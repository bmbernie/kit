#!/bin/bash
set -eu -o pipefail

usage()
{
    echo 'usage: sudo ./scripts/set-usb-identity.sh VID PID [CONFIG]' >&2
    echo 'example: sudo ./scripts/set-usb-identity.sh 0x1234 0xabcd' >&2
}

[ "$#" -ge 2 ] && [ "$#" -le 3 ] || { usage; exit 2; }

VID=$1
PID=$2
CONFIG=${3:-/etc/zerolab/zerolab.conf}

if [ "$(id -u)" -ne 0 ]; then
    echo 'must run as root' >&2
    exit 1
fi

for pair in "VID:$VID" "PID:$PID"; do
    name=${pair%%:*}
    value=${pair#*:}

    if ! printf '%s\n' "$value" | grep -Eq '^0x[0-9A-Fa-f]{4}$'; then
        echo "$name must look like 0x1234" >&2
        exit 2
    fi
done

[ -f "$CONFIG" ] || { echo "missing config: $CONFIG" >&2; exit 1; }

python3 - "$CONFIG" "$VID" "$PID" <<'PYUSB'
from pathlib import Path
import sys

path = Path(sys.argv[1])
vid = sys.argv[2]
pid = sys.argv[3]
lines = path.read_text().splitlines()
values = {"USB_VID": vid, "USB_PID": pid}
seen = set()
out = []

for line in lines:
    key = line.split("=", 1)[0] if "=" in line else None
    if key in values:
        out.append(f"{key}={values[key]}")
        seen.add(key)
    else:
        out.append(line)

for key in ("USB_VID", "USB_PID"):
    if key not in seen:
        out.append(f"{key}={values[key]}")

path.write_text("\n".join(out) + "\n")
PYUSB

chmod 0644 "$CONFIG"

echo "Configured ZeroLab USB identity: VID=$VID PID=$PID"
echo 'The new identity takes effect on the next gadget activation or reboot.'
echo 'Use only identifiers you are authorized to use.'
