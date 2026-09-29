#!/bin/bash
set -eu -o pipefail

CONF=/etc/zerolab/zerolab.conf

PROFILE="$(
    awk -F= '
        $1 == "BOOT_PROFILE" {
            print $2
            exit
        }
    ' "$CONF"
)"

case "$PROFILE" in
    serial|ethernet|composite|hid|full)
        ;;
    *)
        echo "Invalid ZeroLab boot profile: $PROFILE" >&2
        exit 1
        ;;
esac

echo "ZeroLab boot profile: $PROFILE"

# The DWC2 UDC is created asynchronously during boot.
for _ in $(seq 1 40); do
    if compgen -G '/sys/class/udc/*' >/dev/null; then
        break
    fi

    sleep 0.5
done

if ! compgen -G '/sys/class/udc/*' >/dev/null; then
    echo 'No USB Device Controller appeared' >&2
    exit 1
fi

exec /usr/local/sbin/zerolab up "$PROFILE"
