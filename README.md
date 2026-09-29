# kit

`kit` is a collection of reproducible, small information-security hardware builds and hardening overlays.

Each kit carries its own provenance, installation/recovery procedure, validation notes, hardware or platform constraints, and publication-sanitization boundary.

## Current kits

- [`zerolab/`](zerolab/) — Raspberry Pi Zero W USB gadget platform with RNDIS, ACM serial, bounded HID keyboard support, optional read-only mass storage, Wi-Fi-to-Bluetooth PAN failover, PiSugar2 telemetry, and a Waveshare 2.13-inch V2 e-paper status display.
- [`pwnagotchi/`](pwnagotchi/) — sanitized hardening/configuration overlay derived from the accepted Pwnagotchi 2.9.5.9 `final-201303` build, including Bettercap startup hardening, readiness gates, bounded restart policy, and separated upstream-derived plugin modifications.

## Repository status

This repository is the **public release** of the sanitized `kit` publication tree. Original `kit`, ZeroLab, integration, documentation, and hardening material is licensed under MIT. Pwnagotchi-derived plugin files remain subject to their upstream GPL terms; Waveshare driver files retain their upstream permission notice.

The accepted private artifacts are not committed. Publication trees are rebuilt from frozen/sanitized source bundles with secrets and runtime databases excluded.

## Publication principles

- Keep device credentials and network identity out of Git.
- Prefer reproducible builders/scripts to opaque binary artifacts.
- Preserve third-party notices and source provenance.
- Keep upstream-derived code visibly separated from original integration code.
- Treat validation evidence as version-specific; do not generalize one hardware acceptance result to every Raspberry Pi/Wi-Fi combination.

See [`PUBLICATION_CHECKLIST.md`](PUBLICATION_CHECKLIST.md) for the publication criteria to apply before future public releases or substantial publication-tree updates.
