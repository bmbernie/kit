# kit

`kit` is a collection of reproducible, small information-security hardware builds and hardening overlays.

Each kit carries its own provenance, installation/recovery procedure, validation notes, hardware or platform constraints, and publication-sanitization boundary.

## Current kits

- [`zerolab/`](zerolab/) — Raspberry Pi Zero W USB gadget platform with RNDIS, ACM serial, bounded HID keyboard support, optional read-only mass storage, Wi-Fi-to-Bluetooth PAN failover, PiSugar2 telemetry, and a Waveshare 2.13-inch V2 e-paper status display.
- [`pwnagotchi/`](pwnagotchi/) — sanitized hardening/configuration overlay derived from the accepted Pwnagotchi 2.9.5.9 `final-201303` build, including Bettercap startup hardening, readiness gates, bounded restart policy, and separated upstream-derived plugin modifications.
