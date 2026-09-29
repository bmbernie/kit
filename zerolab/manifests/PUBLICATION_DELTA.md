# Public packaging delta from frozen v0.8d

The public tree intentionally differs from the canonical private freeze only where publication/reproduction requires sanitization or parameterization.

1. `display/dashboard_once.py`: `PROMPT_USER` may be supplied via `ZEROLAB_PROMPT_USER`; compatibility default remains `b`.
2. `systemd/zerolab-display.service`: optional `/etc/zerolab/display.env` is loaded.
3. Device-specific Bluetooth MAC and NetworkManager UUIDs are absent from public examples and generated at install time.
4. PiSugar sudoers username is templated and generated at install time.
5. Python bytecode and `*.pre-*` development backups are excluded.
6. Accepted 16 MiB storage image payload is excluded; only its accepted hash remains. `scripts/build-storage-image.sh` produces a replacement blank FAT16 image.
7. Runtime journals and device-specific network evidence are not published.
8. USB VID/PID values from the accepted private appliance are not published. Profiles read user-supplied `USB_VID`/`USB_PID` from `/etc/zerolab/zerolab.conf` and fail closed when they are not configured.
9. `scripts/set-usb-identity.sh` updates runtime configuration instead of rewriting source profile files.

The canonical accepted freeze remains the authority for exact appliance provenance.
