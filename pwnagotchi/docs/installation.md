# Installation

## Scope

This package is a hardening overlay for the accepted Pwnagotchi 2.9.5.9 environment. Install Pwnagotchi through the upstream project first. The overlay assumes the base installation already provides Bettercap, `/usr/bin/pwnlib`, Pwnagotchi's systemd units, and the runtime Python environment.

The exact board model is not encoded by the sanitized source artifact, so this publication draft does not claim that the overlay is universally validated across Raspberry Pi models or Wi-Fi chipsets.

## Review before installation

Inspect the tree and run:

```bash
./scripts/check-publication.sh
./scripts/validate-overlay.sh
```

The first checks the repository for known private-state filenames and obvious populated credential assignments. The second checks the overlay's internal file set and shell syntax.

## Apply the hardening overlay

From `kit/pwnagotchi`:

```bash
sudo ./scripts/install-overlay.sh
```

By default the installer applies only the integration/hardening layer. It does **not** overwrite the installed WPA-SEC or WiGLE plugins.

To install the accepted modified upstream plugin files as well:

```bash
sudo ./scripts/install-overlay.sh --install-plugin-patches
```

Use that option only when the target Pwnagotchi/Python layout matches the accepted build sufficiently for those files to be appropriate. The accepted paths used Python 3.13.

## Configuration

The installer places a sanitized template at:

```text
/etc/pwnagotchi/config.toml.kit-example
```

It does not overwrite `/etc/pwnagotchi/config.toml`. Copy/merge settings manually and keep real credentials outside version control.

## After installation

Reload systemd and restart the affected services during a maintenance window. A typical validation sequence is:

```bash
sudo systemctl daemon-reload
sudo systemctl restart bettercap.service
sudo systemctl restart pwngrid-peer.service
sudo systemctl restart pwnagotchi.service

sudo systemctl status bettercap.service --no-pager -l
sudo systemctl status pwngrid-peer.service --no-pager -l
sudo systemctl status pwnagotchi.service --no-pager -l

ip -br link
ss -ltn
```

Then use [`scripts/validate-live.sh`](../scripts/validate-live.sh) for bounded runtime checks.

## Backups

`install-overlay.sh` creates a timestamped backup directory under `/var/backups/kit-pwnagotchi/` before replacing existing target files. Keep that directory until the target has survived cold-boot validation.
