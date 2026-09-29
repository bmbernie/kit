# WPA-SEC and WiGLE plugin material

The accepted final artifact contained modified copies of Pwnagotchi's default WPA-SEC and WiGLE plugins. The publication tree keeps them under:

```text
upstream/modified-plugins/wpa-sec.py
upstream/modified-plugins/wigle.py
```

They are upstream-derived GPL material, not original `kit` source.

## WPA-SEC runtime state

The live accepted artifact also contained `/etc/pwnagotchi/.wpa_sec_db`, a SQLite database used by the WPA-SEC plugin to track handshake upload status. That database is deliberately **not** included in this repository.

The plugin can transmit captured handshake material to the configured WPA-SEC endpoint. The included configuration template keeps the plugin disabled and the API key empty.

## WiGLE

The WiGLE plugin can upload geolocated wireless observations to WiGLE when configured. The included template keeps it disabled and contains no credential.

## Installation policy

The overlay installer does not install either modified plugin unless `--install-plugin-patches` is supplied explicitly. This separation makes the build-specific service hardening independently usable and prevents silent replacement of upstream plugin code on installations that may have a different Pwnagotchi version.
