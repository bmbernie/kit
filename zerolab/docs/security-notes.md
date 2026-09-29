# Security and publication notes

## Secrets excluded from the accepted freeze

The freeze process deliberately excluded:

- Wi-Fi credential profile
- `/var/lib/bluetooth` link/pairing keys
- SSH host keys
- user `authorized_keys`
- private keys

The public repository additionally replaces the accepted phone MAC and NetworkManager UUIDs with installation-time values/placeholders.

## USB identifiers

The accepted laboratory gadget profiles use temporary IDs, including Raspberry Pi-owned values in several profiles. They are **not assigned to ZeroLab**. Do not ship a product using those IDs. Obtain/use identifiers you are authorized to use and update every profile consistently.

## HID boundary

The repository contains a literal-text HID keyboard engine because HID is one of the tested gadget functions. Keep testing bounded to hosts you control. The repository intentionally does not include credential theft, persistence, destructive payloads, or unattended attack automation.

## Mass storage

The LUN is configured read-only to the host. If you replace the builder or image, preserve the read-only ConfigFS setting unless you intentionally accept the integrity risks of writable USB mass storage.

## Network failover

The Bluetooth PAN profile is device-specific. Pairing data itself is not stored here. Treat the phone MAC as configuration, not as a reusable credential.

## Public-repo preflight

Run:

```bash
./scripts/check-publication.sh
```

before any public push. It checks for values from the accepted private build that should not appear in the sanitized repository and for obvious private-key material.
