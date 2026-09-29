#!/usr/bin/env bash
set -eu -o pipefail

command -v systemctl >/dev/null
command -v ip >/dev/null
command -v ss >/dev/null

echo '=== Pwnagotchi live overlay validation ==='

for path in \
    /usr/local/sbin/bettercap-launcher-safe \
    /usr/local/sbin/pwnagotchi-wait-bettercap \
    /usr/local/sbin/pwnagotchi-wait-pwngrid \
    /usr/bin/pwnagotchi-launcher; do
    test -x "$path"
    echo "PASS: executable $path"
done

for unit in bettercap.service pwngrid-peer.service pwnagotchi.service; do
    printf '%-26s ' "$unit"
    systemctl is-active "$unit" || true
done

echo
ip -br link

echo
ss -ltn | grep -E ':(8081|8666)[[:space:]]' || true

echo
systemctl show bettercap.service \
    -p StartLimitBurst \
    -p StartLimitIntervalUSec \
    -p NRestarts \
    -p Result

echo
if [[ -e /sys/class/net/wlan0mon ]]; then
    echo 'PASS: wlan0mon exists'
else
    echo 'INFO: wlan0mon is not currently present'
fi

echo '=== Validation complete ==='
