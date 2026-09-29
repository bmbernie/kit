# Security and publication notes

Use this kit only on systems, radio environments, and networks you own or are explicitly authorized to test.

The publication tree intentionally excludes:

- `/etc/pwnagotchi/config.toml` from the accepted device;
- `/etc/pwnagotchi/.wpa_sec_db`;
- captured handshake material;
- API keys and passwords;
- private SSIDs/BSSIDs and local allow/deny lists;
- SSH private keys and host keys;
- Bluetooth pairing/link keys;
- device-specific network addresses used during validation.

The example configuration disables WPA-SEC and WiGLE and leaves their credentials blank. Enabling either integration can cause locally collected data to be sent to a third-party service; review those services and your authorization before enabling them.

Do not treat the source manifest as proof that every deployment secret has been removed from future changes. Run `scripts/check-publication.sh`, inspect the full Git diff, and use a dedicated secret scanner before publishing.
