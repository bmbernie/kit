#!/bin/bash
set -eu -o pipefail

usage() {
    cat <<'USAGE'
Usage:
  sudo ./scripts/install.sh --user USER --usb-vid 0xVVVV --usb-pid 0xPPPP [--phone-mac MAC] [--boot-profile PROFILE]

Options:
  --user USER          local account allowed to use bounded PiSugar health reads
  --usb-vid 0xVVVV     USB vendor ID you are authorized to use
  --usb-pid 0xPPPP     USB product ID you are authorized to use
  --phone-mac MAC      optional paired/trusted phone for Bluetooth PAN failover
  --boot-profile NAME  serial|ethernet|composite|hid|full (default: full)
USAGE
}

USER_NAME=''
USB_VID=''
USB_PID=''
PHONE_MAC=''
BOOT_PROFILE=full

while [ "$#" -gt 0 ]; do
    case "$1" in
        --user)
            USER_NAME=${2:?missing --user value}
            shift 2
            ;;
        --usb-vid)
            USB_VID=${2:?missing --usb-vid value}
            shift 2
            ;;
        --usb-pid)
            USB_PID=${2:?missing --usb-pid value}
            shift 2
            ;;
        --phone-mac)
            PHONE_MAC=${2:?missing --phone-mac value}
            shift 2
            ;;
        --boot-profile)
            BOOT_PROFILE=${2:?missing --boot-profile value}
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo 'installer must run as root' >&2
    exit 1
fi

case "$BOOT_PROFILE" in
    serial|ethernet|composite|hid|full) ;;
    *) echo "invalid boot profile: $BOOT_PROFILE" >&2; exit 1 ;;
esac

[ -n "$USER_NAME" ] || { echo '--user is required' >&2; exit 1; }
id "$USER_NAME" >/dev/null 2>&1 || { echo "unknown user: $USER_NAME" >&2; exit 1; }

for pair in "USB_VID:$USB_VID" "USB_PID:$USB_PID"; do
    name=${pair%%:*}
    value=${pair#*:}

    if ! printf '%s\n' "$value" | grep -Eq '^0x[0-9A-Fa-f]{4}$'; then
        echo "$name is required and must look like 0x1234" >&2
        exit 1
    fi
done

if [ -n "$PHONE_MAC" ] && ! printf '%s\n' "$PHONE_MAC" | grep -Eq '^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$'; then
    echo 'invalid Bluetooth MAC format' >&2
    exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$HERE/src/zerolab"

[ -f "$SRC/controller.py" ] || { echo 'run installer from the repository checkout' >&2; exit 1; }
[ -f /boot/firmware/config.txt ] || { echo 'expected Raspberry Pi OS /boot/firmware/config.txt' >&2; exit 1; }

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
    bluez \
    dosfstools \
    fonts-dejavu-core \
    fonts-dejavu-mono \
    gpiod \
    i2c-tools \
    iw \
    network-manager \
    python3-gpiozero \
    python3-lgpio \
    python3-pil \
    python3-spidev \
    raspi-utils \
    rfkill

install -d -o root -g root -m 0755 /usr/local/lib/zerolab
cp -a "$SRC/." /usr/local/lib/zerolab/
chown -R root:root /usr/local/lib/zerolab
find /usr/local/lib/zerolab -type d -exec chmod 0755 {} +
find /usr/local/lib/zerolab -type f -name '*.py' -exec chmod 0755 {} +
find /usr/local/lib/zerolab/profiles -type f -exec chmod 0755 {} +
chmod 0755 /usr/local/lib/zerolab/common.sh /usr/local/lib/zerolab/boot.sh

ln -sfn /usr/local/lib/zerolab/controller.py /usr/local/sbin/zerolab
ln -sfn /usr/local/lib/zerolab/hid_engine.py /usr/local/sbin/zerolab-hid
ln -sfn /usr/local/lib/zerolab/health.py /usr/local/sbin/zerolab-health
ln -sfn /usr/local/lib/zerolab/netfailover.py /usr/local/sbin/zerolab-netfailover
install -o root -g root -m 0755 "$HERE/src/wrappers/zerolab-display-render" /usr/local/sbin/zerolab-display-render

install -d -o root -g root -m 0755 /etc/zerolab
cat >/etc/zerolab/zerolab.conf <<CFG
BOOT_PROFILE=$BOOT_PROFILE
USB_VID=$USB_VID
USB_PID=$USB_PID
CFG
printf 'ZEROLAB_PROMPT_USER=%s\n' "$USER_NAME" > /etc/zerolab/display.env
chmod 0644 /etc/zerolab/zerolab.conf /etc/zerolab/display.env

cat >/etc/zerolab/netfailover.conf <<CFG
# Wi-Fi -> Bluetooth failover tests association only.
WIFI_IFACE=wlan0
BT_CONNECTION=zerolab-phone-tether
PHONE_MAC=${PHONE_MAC:-UNCONFIGURED}
CHECK_INTERVAL=10
FAIL_THRESHOLD=3
RECOVER_THRESHOLD=3
BT_RETRY_COOLDOWN=60
STARTUP_GRACE=30
CFG
chmod 0644 /etc/zerolab/netfailover.conf

TMP=$(mktemp)
sed "s/@ZEROLAB_USER@/$USER_NAME/g" "$HERE/config/sudoers/zerolab-health-pisugar.template" > "$TMP"
visudo -cf "$TMP"
install -o root -g root -m 0440 "$TMP" /etc/sudoers.d/zerolab-health-pisugar
rm -f "$TMP"
visudo -cf /etc/sudoers.d/zerolab-health-pisugar

for unit in zerolab.service zerolab-netfailover.service zerolab-display.service; do
    install -o root -g root -m 0644 "$HERE/systemd/$unit" "/etc/systemd/system/$unit"
done

ensure_boot_line() {
    line=$1
    file=/boot/firmware/config.txt
    if ! grep -Fqx "$line" "$file"; then
        printf '\n# ZeroLab\n%s\n' "$line" >> "$file"
    fi
}

ensure_boot_line 'dtparam=i2c_arm=on'
ensure_boot_line 'dtparam=spi=on'
ensure_boot_line 'dtoverlay=dwc2,dr_mode=peripheral'

install -d -o root -g root -m 0700 /etc/NetworkManager/system-connections
USB_UUID=$(cat /proc/sys/kernel/random/uuid)
cat >/etc/NetworkManager/system-connections/zerolab-usb.nmconnection <<CFG
[connection]
id=zerolab-usb
uuid=$USB_UUID
type=ethernet
interface-name=usb0

[ethernet]

[ipv4]
address1=10.13.37.1/30
method=manual
never-default=true

[ipv6]
addr-gen-mode=default
method=disabled

[proxy]
CFG
chmod 0600 /etc/NetworkManager/system-connections/zerolab-usb.nmconnection

if [ -n "$PHONE_MAC" ]; then
    BT_UUID=$(cat /proc/sys/kernel/random/uuid)
    cat >/etc/NetworkManager/system-connections/zerolab-phone-tether.nmconnection <<CFG
[connection]
id=zerolab-phone-tether
uuid=$BT_UUID
type=bluetooth
autoconnect=false

[bluetooth]
bdaddr=$PHONE_MAC
type=panu

[ipv4]
method=auto
route-metric=900

[ipv6]
addr-gen-mode=default
method=disabled

[proxy]
CFG
    chmod 0600 /etc/NetworkManager/system-connections/zerolab-phone-tether.nmconnection
fi

nmcli connection reload || true
systemctl daemon-reload
systemctl enable zerolab.service zerolab-display.service

if [ -n "$PHONE_MAC" ]; then
    systemctl enable zerolab-netfailover.service
    if ! bluetoothctl info "$PHONE_MAC" 2>/dev/null | grep -q 'Paired: yes'; then
        echo "WARNING: $PHONE_MAC is not currently reported paired; pair/trust it before failover testing." >&2
    fi
else
    systemctl disable zerolab-netfailover.service >/dev/null 2>&1 || true
    echo 'Bluetooth failover left disabled because --phone-mac was not supplied.'
fi

echo
echo 'ZeroLab files installed.'
echo 'A reboot is required for SPI/I2C/DWC2 boot configuration.'
echo 'After reboot, run: sudo ./scripts/validate.sh'
echo
echo "USB identity configured: VID=$USB_VID PID=$USB_PID"
echo 'Use only identifiers you are authorized to use.'
