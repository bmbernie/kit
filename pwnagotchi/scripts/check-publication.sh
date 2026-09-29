#!/usr/bin/env bash
set -eu -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

for forbidden in \
    'config.toml' \
    '.wpa_sec_db' \
    '*.pcap' \
    '*.pcapng' \
    '*.22000' \
    '*.hc22000'; do
    if find "$ROOT" -type f -name "$forbidden" -print -quit | grep -q .; then
        fail "forbidden publication file present: $forbidden"
    fi
done

if grep -RniE \
    --exclude='config.toml.example' \
    --exclude='check-publication.sh' \
    "(api[_-]?key|password|passwd|token|secret)[[:space:]]*=[[:space:]]*[\"'][^\"']+[\"']" \
    "$ROOT"; then
    fail 'possible populated credential assignment found'
fi


echo 'PASS: Pwnagotchi publication checks'
