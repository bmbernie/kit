# Provenance

## Canonical accepted freeze

ZeroLab v0.8d was frozen after final cold-boot acceptance.

```text
Archive: /var/lib/zerolab/baselines/20260928-v0.8d.tar.gz
SHA-256: 2e7d2af814c7269afd9c188a0af49c815250292f56274ab4d0f45e7e5e9785c1
Release state: ACCEPTED
```

The freeze captured the ZeroLab source, configuration, systemd units, selected NetworkManager profiles, read-only storage image and validation evidence. It deliberately excluded credential-bearing Wi-Fi, Bluetooth and SSH material.

## Documentation-source bundle

This repository was generated from the subsequent documentation-source export derived only from the canonical freeze. The export removed bytecode, development backup files, boot journals, device-specific runtime network evidence and the 16 MiB storage image payload.

See `manifests/docsource.sha256` for the uploaded documentation-source bundle hash used to create this tree.

## Accepted software environment

- Raspbian GNU/Linux 13 (trixie)
- accepted kernel: `6.18.50+rpt-rpi-v6`
- architecture: `armv6l`

Selected accepted package versions are recorded in `manifests/accepted-packages.tsv`.

## Third-party driver

The minimal Waveshare driver snapshot is stored under `src/zerolab/display/vendor/waveshare_epd/`. `SOURCE.txt` identifies the upstream repository/driver and `SHA256SUMS` records the exact accepted file hashes. The upstream permission notices remain in the Python source headers.

## Publication-only deltas

The public tree is not byte-for-byte identical to the accepted appliance source because device-specific configuration must not be published. See `CHANGELOG.md` for the intentionally small sanitization/configurability delta.
