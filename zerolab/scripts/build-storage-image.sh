#!/bin/bash
set -eu -o pipefail

OUT=${1:-/var/lib/zerolab/images/zerolab-readonly-v0.4.img}
SIZE_MIB=${ZEROLAB_STORAGE_MIB:-16}
LABEL=${ZEROLAB_STORAGE_LABEL:-ZEROLAB}

if [ "$(id -u)" -ne 0 ]; then
    echo 'run as root (or use sudo)' >&2
    exit 1
fi

command -v mkfs.fat >/dev/null
command -v truncate >/dev/null

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT" "$OUT.sha256"
truncate -s "${SIZE_MIB}M" "$OUT"
mkfs.fat -F 16 -n "$LABEL" "$OUT" >/dev/null
chmod 0444 "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
chmod 0444 "$OUT.sha256"

echo "created: $OUT"
cat "$OUT.sha256"
echo 'NOTE: this is a replacement blank image; it is not byte-identical to the accepted v0.4 image.'
