#!/bin/bash
set -eu -o pipefail

ZEROLAB_GADGET=/sys/kernel/config/usb_gadget/zerolab
ZEROLAB_CONFIG=${ZEROLAB_CONFIG:-/etc/zerolab/zerolab.conf}

zerolab_udc()
{
    basename "$(readlink -f /sys/class/udc/*)"
}

zerolab_require_clean()
{
    test ! -e "$ZEROLAB_GADGET"
}

zerolab_unbind()
{
    if [ -e "$ZEROLAB_GADGET/UDC" ]; then
        printf '' > "$ZEROLAB_GADGET/UDC"
    fi
}

zerolab_require_usb_identity()
{
    if [ ! -r "$ZEROLAB_CONFIG" ]; then
        echo "ZeroLab config is missing or unreadable: $ZEROLAB_CONFIG" >&2
        return 1
    fi

    ZEROLAB_USB_VID="$(
        awk -F= '$1 == "USB_VID" { print $2; exit }' "$ZEROLAB_CONFIG"
    )"

    ZEROLAB_USB_PID="$(
        awk -F= '$1 == "USB_PID" { print $2; exit }' "$ZEROLAB_CONFIG"
    )"

    if ! printf '%s\n' "$ZEROLAB_USB_VID" | grep -Eq '^0x[0-9A-Fa-f]{4}$'; then
        echo 'USB_VID is not configured; expected 0xNNNN in /etc/zerolab/zerolab.conf' >&2
        return 1
    fi

    if ! printf '%s\n' "$ZEROLAB_USB_PID" | grep -Eq '^0x[0-9A-Fa-f]{4}$'; then
        echo 'USB_PID is not configured; expected 0xNNNN in /etc/zerolab/zerolab.conf' >&2
        return 1
    fi
}

zerolab_apply_usb_identity()
{
    gadget=${1:?missing gadget path}

    : "${ZEROLAB_USB_VID:?call zerolab_require_usb_identity first}"
    : "${ZEROLAB_USB_PID:?call zerolab_require_usb_identity first}"

    printf '%s\n' "$ZEROLAB_USB_VID" > "$gadget/idVendor"
    printf '%s\n' "$ZEROLAB_USB_PID" > "$gadget/idProduct"
}
