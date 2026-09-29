#!/usr/bin/env bash
set -eu -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_PLUGINS=0

if [[ ${1:-} == '--install-plugin-patches' ]]; then
    INSTALL_PLUGINS=1
    shift
fi

if (( $# != 0 )); then
    echo 'usage: install-overlay.sh [--install-plugin-patches]' >&2
    exit 2
fi

if (( EUID != 0 )); then
    echo 'run as root' >&2
    exit 1
fi

for path in \
    /usr/bin/pwnlib \
    /etc/systemd/system; do
    test -e "$path" || {
        echo "missing base prerequisite: $path" >&2
        exit 1
    }
done

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="/var/backups/kit-pwnagotchi/$STAMP"
mkdir -p "$BACKUP"

backup_target() {
    local target="$1"
    if [[ -e "$target" || -L "$target" ]]; then
        local rel="${target#/}"
        mkdir -p "$BACKUP/$(dirname "$rel")"
        cp -a "$target" "$BACKUP/$rel"
    fi
}

install_file() {
    local src="$1" target="$2" mode="$3"
    backup_target "$target"
    install -D -o root -g root -m "$mode" "$src" "$target"
}

install_file "$ROOT/overlay-bin/bettercap-launcher-safe" /usr/local/sbin/bettercap-launcher-safe 0755
install_file "$ROOT/overlay-bin/pwnagotchi-wait-bettercap" /usr/local/sbin/pwnagotchi-wait-bettercap 0755
install_file "$ROOT/overlay-bin/pwnagotchi-wait-pwngrid" /usr/local/sbin/pwnagotchi-wait-pwngrid 0755
install_file "$ROOT/overlay-bin/pwnagotchi-launcher" /usr/bin/pwnagotchi-launcher 0755

install_file "$ROOT/config/NetworkManager/90-pwnagotchi-dns.conf" /etc/NetworkManager/conf.d/90-pwnagotchi-dns.conf 0644
install_file "$ROOT/config/NetworkManager/90-pwnagotchi-wifi-unmanaged.conf" /etc/NetworkManager/conf.d/90-pwnagotchi-wifi-unmanaged.conf 0644
install_file "$ROOT/config/logrotate/pwnagotchi-local" /etc/logrotate.d/pwnagotchi-local 0644
install_file "$ROOT/config/modules-load/i2c-dev.conf" /etc/modules-load.d/i2c-dev.conf 0644

for rel in \
    bettercap.service.d/10-networkmanager-order.conf \
    bettercap.service.d/20-safe-launcher.conf \
    bettercap.service.d/30-restart-limit.conf \
    pwnagotchi.service.d/10-bettercap-readiness.conf \
    pwnagotchi.service.d/15-pwngrid-readiness.conf \
    pwngrid-peer.service.d/10-bettercap-readiness.conf; do
    install_file "$ROOT/systemd/$rel" "/etc/systemd/system/$rel" 0644
done

install_file "$ROOT/config/config.toml.example" /etc/pwnagotchi/config.toml.kit-example 0644

if (( INSTALL_PLUGINS )); then
    SITE=/opt/.pwn/lib/python3.13/site-packages/pwnagotchi/plugins/default
    test -d "$SITE" || {
        echo "plugin target not found: $SITE" >&2
        exit 1
    }
    install_file "$ROOT/upstream/modified-plugins/wpa-sec.py" "$SITE/wpa-sec.py" 0644
    install_file "$ROOT/upstream/modified-plugins/wigle.py" "$SITE/wigle.py" 0644
fi

systemctl daemon-reload

cat <<EOF
PASS: Pwnagotchi kit overlay installed
Backup: $BACKUP
Plugin patches installed: $INSTALL_PLUGINS

Review /etc/pwnagotchi/config.toml.kit-example and your live config,
then restart services during a maintenance window and validate.
EOF
