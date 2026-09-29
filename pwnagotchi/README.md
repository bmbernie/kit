# Pwnagotchi hardening kit

This directory packages the accepted hardening/configuration overlay from a Pwnagotchi 2.9.5.9 build. It is **not** a complete Pwnagotchi operating-system image and it does not replace the upstream installation procedure.

The overlay addresses the startup behavior that was validated on the accepted device: Bettercap is allowed to start only after NetworkManager is available; `wlan0` is allowed to settle before a monitor interface is created; `wlan0mon` must remain stable; Pwnagotchi waits for the Bettercap API; pwngrid readiness is gated; and repeated Bettercap startup failures are bounded by systemd start-rate limiting.

## Accepted source

The publication tree is derived from the sanitized export of:

```text
pwnagotchi-final-20260926-201303.tar.gz
SHA-256: a183fae8ce88b7722878278cbd4c3ed83b0352f5c53ef0c7b0e9386a610cdfe9
```

The sanitized documentation-source bundle used to build this tree is identified in [`docs/provenance.md`](docs/provenance.md).

## What is included

- Bettercap safe-launch wrapper and bounded restart policy.
- systemd ordering/readiness drop-ins for Bettercap, Pwnagotchi, and pwngrid-peer.
- Pwnagotchi launcher behavior that avoids unnecessary Bettercap restarts.
- NetworkManager policy for the Pwnagotchi Wi-Fi interfaces.
- Log rotation and `i2c-dev` module configuration.
- A credential-free `config.toml` example.
- The accepted modified WPA-SEC and WiGLE plugin files, kept separately as upstream-derived GPL material.
- Installation, validation, troubleshooting, security, and provenance documentation.

## What is intentionally not included

The publication source excludes the original private `config.toml`, the WPA-SEC runtime database, captured handshakes, API keys, passwords, Wi-Fi credentials, device identity material, and SSH/Bluetooth keys.

The accepted build contained `/etc/pwnagotchi/.wpa_sec_db`; that runtime database was removed before this publication source was generated.

## Installation model

Start with a compatible Pwnagotchi installation, review [`docs/installation.md`](docs/installation.md), then apply this overlay. The plugin replacements are intentionally opt-in because they are upstream-derived files tied to the accepted Pwnagotchi/Python layout.

## Safety and authorization

Use Pwnagotchi only on networks and radio environments where you have authorization. WPA-SEC and WiGLE integrations can transmit data to third-party services; they are disabled in the included example configuration until you deliberately configure them.

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
