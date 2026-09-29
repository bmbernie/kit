#!/bin/bash
set -eu -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BAD=0

if grep -RInE \
    --exclude-dir=.git \
    --exclude=check-publication.sh \
    -- 'BEGIN (OPENSSH|RSA|EC|DSA|PRIVATE) PRIVATE KEY' \
    "$ROOT"; then
    echo 'FAIL: private-key material detected' >&2
    BAD=1
fi

if grep -RInE \
    --exclude-dir=.git \
    --exclude=check-publication.sh \
    --exclude='*.example' \
    -- "(psk|password|passwd|api[_-]?key|token|secret)[[:space:]]*=[[:space:]]*[\"'][^\"']+[\"']" \
    "$ROOT"; then
    echo 'FAIL: possible populated credential assignment detected' >&2
    BAD=1
fi

if find "$ROOT" -type f \
    \( -name '*.pem' -o -name '*.key' -o -name 'id_rsa' -o -name 'id_ed25519' \) \
    -print -quit | grep -q .; then
    echo 'FAIL: private-key-like filename present' >&2
    BAD=1
fi


if grep -RInE \
    -- 'echo[[:space:]]+0x[0-9A-Fa-f]{4}[[:space:]]*>[[:space:]]*"\$G/id(Vendor|Product)"' \
    "$ROOT/zerolab/src/zerolab/profiles"; then
    echo 'FAIL: hard-coded USB VID/PID detected in ZeroLab profile scripts' >&2
    BAD=1
fi

if [ "$BAD" -ne 0 ]; then
    exit 1
fi

echo 'PASS: no private-key material or obvious populated credentials detected'
