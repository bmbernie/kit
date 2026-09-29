#!/bin/bash
set -eu -o pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo 'run as root (or use sudo)' >&2
    exit 1
fi

systemctl disable --now zerolab-display.service 2>/dev/null || true
systemctl disable --now zerolab-netfailover.service 2>/dev/null || true
systemctl disable --now zerolab.service 2>/dev/null || true
/usr/local/sbin/zerolab down 2>/dev/null || true

rm -f \
    /etc/systemd/system/zerolab.service \
    /etc/systemd/system/zerolab-netfailover.service \
    /etc/systemd/system/zerolab-display.service \
    /etc/sudoers.d/zerolab-health-pisugar \
    /usr/local/sbin/zerolab \
    /usr/local/sbin/zerolab-hid \
    /usr/local/sbin/zerolab-health \
    /usr/local/sbin/zerolab-netfailover \
    /usr/local/sbin/zerolab-display-render

rm -rf /usr/local/lib/zerolab /etc/zerolab
rm -f \
    /etc/NetworkManager/system-connections/zerolab-usb.nmconnection \
    /etc/NetworkManager/system-connections/zerolab-phone-tether.nmconnection

systemctl daemon-reload
nmcli connection reload 2>/dev/null || true

echo 'ZeroLab files/services removed.'
echo 'Boot config lines enabling I2C, SPI and DWC2 peripheral mode were intentionally left in place.'
echo 'Installed Debian packages and any generated storage image were also left in place.'
