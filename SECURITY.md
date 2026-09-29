# Security notes

These projects are intended for systems, radio environments, and networks you own or are explicitly authorized to test.

## Repository hygiene

Do not commit Wi-Fi PSKs, Bluetooth pairing/link keys, SSH keys, private keys, API credentials, captured handshake material, WPA-SEC runtime databases, or device-specific secrets.

## ZeroLab

- HID support is a bounded literal-text keyboard engine, not a payload framework.
- The mass-storage gadget is read-only from the USB host side.
- Bluetooth failover is based on Wi-Fi association state, not Internet reachability.
- ZeroLab does not ship a default USB VID/PID. Installation requires `USB_VID` and `USB_PID` values that you are authorized to use; they are stored in `/etc/zerolab/zerolab.conf` rather than hard-coded in profile scripts.

## Pwnagotchi

- Use capture/monitor functionality only where authorized.
- WPA-SEC and WiGLE integrations can transmit collected data to third-party services; the publication template leaves them disabled with empty credentials.
- The live `.wpa_sec_db` and private `config.toml` from the accepted device are excluded from the public tree.
- The Bettercap start limit is an intentional failure-containment mechanism; do not raise it merely to mask a persistent radio/firmware failure.

If a credential or sensitive capture is accidentally committed, remove it from repository history as appropriate and rotate/revoke the affected secret.
