# Publication checklist

Before the first public GitHub push:

- [x] Original `kit` / ZeroLab / integration code licensed under MIT.
- [ ] Keep `licenses/GPL-3.0.txt` and all third-party source notices intact.
- [x] ZeroLab profile scripts contain no hard-coded USB VID/PID; installer/runtime configuration requires user-supplied authorized values.
- [ ] Run `zerolab/scripts/check-publication.sh`.
- [ ] Run `pwnagotchi/scripts/check-publication.sh`.
- [ ] Run the root secret/value scan on the complete staged Git diff.
- [ ] Confirm there is no Wi-Fi PSK/profile, Bluetooth pairing/link key, SSH key, API credential, captured handshake, `.wpa_sec_db`, or private Pwnagotchi `config.toml`.
- [ ] Keep the accepted private ZeroLab storage image out of Git; build it locally or attach a separately reviewed release artifact.
- [ ] Keep Pwnagotchi-derived plugin files separated/attributed as upstream GPL material.
- [ ] Review installers on disposable media before describing them as portable beyond the accepted hardware baseline.
- [ ] Review every generated manifest after the final repository files are staged.
- [ ] Create the public remote only after the staged tree passes manual review and secret scanning.
