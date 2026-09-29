# Pwnagotchi (w/ improvements)

This directory contains my configuration overlay for the [Pwnagotchi](https://github.com/jayofelony/pwnagotchi).  

Similar to the original project, by evilsocket, my pwnagotchi uses a pisugar 2 battery to provide power while "in the field" as well as a waveshare 2.13 inch e-ink display.

# Improvements

The overlay addresses the startup behavior that was validated on the accepted device: Bettercap is allowed to start only after NetworkManager is available; `wlan0` is allowed to settle before a monitor interface is created; `wlan0mon` must remain stable; Pwnagotchi waits for the Bettercap API; pwngrid readiness is gated; and repeated Bettercap startup failures are bounded by systemd start-rate limiting.

## What is included

- Bettercap safe-launch wrapper and bounded restart policy.
- systemd ordering/readiness drop-ins for Bettercap, Pwnagotchi, and pwngrid-peer.
- Pwnagotchi launcher behavior that avoids unnecessary Bettercap restarts.
- NetworkManager policy for the Pwnagotchi Wi-Fi interfaces.
- Log rotation and `i2c-dev` module configuration.
- A credential-free `config.toml` example.
- The accepted modified WPA-SEC and WiGLE plugin files, kept separately as upstream-derived GPL material.
- Installation, validation, troubleshooting, security, and provenance documentation.

## Installation

Start with a compatible Pwnagotchi installation, review [`docs/installation.md`](docs/installation.md), then apply this overlay. The plugin replacements are intentionally opt-in because they are upstream-derived files tied to the accepted Pwnagotchi/Python layout.

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/hardening.md`](docs/hardening.md)
- [`docs/installation.md`](docs/installation.md)
- [`docs/networking.md`](docs/networking.md)
- [`docs/plugins.md`](docs/plugins.md)
- [`docs/security-notes.md`](docs/security-notes.md)
- [`docs/troubleshooting.md`](docs/troubleshooting.md)
- [`docs/validation.md`](docs/validation.md)
- [`docs/provenance.md`](docs/provenance.md)
