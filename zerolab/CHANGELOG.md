# Changelog

## v0.8d — accepted appliance baseline

Validated end-to-end:

- `full` cold-boot profile with RNDIS + ACM + HID
- optional read-only mass storage and `full-storage`
- RNDIS management at `10.13.37.1/30`
- Wi-Fi-primary / Bluetooth-PAN failover and recovery
- bounded PiSugar register helper and health telemetry
- stateful BAT/CHG detection for the tested PiSugar2 revision
- Waveshare 2.13-inch V2 dashboard
- full startup e-paper base refresh plus partial state updates
- automatic display tracking of Wi-Fi, Bluetooth and RNDIS state
- final true cold-boot acceptance with all services active and `throttled=0x0`

Canonical frozen archive SHA-256:

`2e7d2af814c7269afd9c188a0af49c815250292f56274ab4d0f45e7e5e9785c1`

## Public-repository packaging delta

The repository tree is derived from the accepted v0.8d source, with publication-only sanitization/configurability changes:

- device-specific Bluetooth MAC removed from examples
- NetworkManager UUIDs are generated at install time
- PiSugar sudoers target user is generated at install time
- displayed prompt username is read from `ZEROLAB_PROMPT_USER` with `b` as the compatibility default
- e-paper systemd unit reads optional `/etc/zerolab/display.env`
- Python bytecode and development `*.pre-*` backups are excluded
- the accepted 16 MiB storage image is excluded; a builder script creates a replacement blank read-only image

Core gadget, failover, health and display logic otherwise comes from the accepted freeze.
