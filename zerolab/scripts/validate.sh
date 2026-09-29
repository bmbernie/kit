#!/bin/bash
set -eu -o pipefail

echo '=== ZeroLab validation ==='

command -v zerolab >/dev/null
command -v zerolab-health >/dev/null

test -e /dev/spidev0.0
test "$(vcgencmd get_throttled)" = 'throttled=0x0'

for unit in zerolab.service zerolab-display.service; do
    test "$(systemctl is-enabled "$unit")" = 'enabled'
    test "$(systemctl is-active "$unit")" = 'active'
done

zerolab status --json | python3 -c '
import json, sys
x=json.load(sys.stdin)
assert x["gadget_present"] is True
assert x["udc_state"] == "configured"
assert x["usb0"] is True
assert "10.13.37.1/30" in x["usb_ipv4"]
print("PASS: gadget configured and RNDIS management address present")
'

SCAN=$(i2cdetect -y 1)
printf '%s\n' "$SCAN"
if grep -qE '30:.*(^|[[:space:]])32([[:space:]]|$)' <<<"$SCAN"; then
    echo 'PASS: PiSugar RTC 0x32 present'
else
    echo 'INFO: PiSugar RTC 0x32 not visible'
fi
if grep -qE '70:.*(^|[[:space:]])75([[:space:]]|$)' <<<"$SCAN"; then
    echo 'PASS: PiSugar PowerIC 0x75 present'
else
    echo 'INFO: PiSugar PowerIC 0x75 not visible in current power state'
fi

zerolab-health

LOG=$(journalctl -u zerolab-display.service -b --no-pager -l)
grep -Fq 'physical refresh complete: FULL' <<<"$LOG"
if grep -Fq 'GPIO busy' <<<"$LOG"; then
    echo 'FAIL: display GPIO contention detected' >&2
    exit 1
fi

echo 'PASS: display startup full-base refresh observed'

if systemctl is-enabled --quiet zerolab-netfailover.service; then
    test "$(systemctl is-active zerolab-netfailover.service)" = 'active'
    zerolab-netfailover --status
fi

echo 'PASS: throttled=0x0'
echo '=== ZeroLab validation complete ==='
