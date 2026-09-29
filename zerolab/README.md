# ZeroLab

ZeroLab is a Raspberry Pi Zero W security-lab gadget platform. The accepted v0.8d build exposes composable USB gadget functions, preserves a dedicated RNDIS management path, supports Wi-Fi-primary/Bluetooth-PAN fallback networking, reports PiSugar2 power telemetry, and renders live state on a Waveshare 2.13-inch V2 e-paper display.

## Accepted hardware/software baseline

- Raspberry Pi Zero W Rev 1.1 / BCM2835 / ARMv6
- Raspberry Pi OS Lite 32-bit, Raspbian 13 (trixie)
- accepted kernel: `6.18.50+rpt-rpi-v6`
- PiSugar2 1200 mAh battery board
- Waveshare 2.13-inch V2 e-paper HAT
- USB gadget management network: `10.13.37.1/30` on the Pi, host side normally `10.13.37.2/30`

## Features

| Area | v0.8d behavior |
| --- | --- |
| USB Ethernet | RNDIS, stable `usb0`, static `10.13.37.1/30` |
| USB serial | ACM on `/dev/ttyGS0` |
| USB HID | bounded keyboard function on `/dev/hidg0` |
| USB storage | optional read-only FAT mass-storage function |
| Wi-Fi | primary uplink/management network |
| Bluetooth | PAN fallback after bounded Wi-Fi-association failure |
| Power | PiSugar2 RTC/PowerIC telemetry, battery voltage/current and SOC estimate |
| Display | inverted 250×122 dashboard, full startup base + partial updates |
| Controller | profile switching is serialized and fail-closed |

## Quick start

Read [`docs/installation.md`](docs/installation.md) before installing. The short form is:

```bash
sudo ./scripts/install.sh --user "$USER" --usb-vid 0xVVVV --usb-pid 0xPPPP --phone-mac AA:BB:CC:DD:EE:FF
sudo reboot
```

The phone must be paired/trusted separately before Bluetooth PAN failover can succeed.

After reboot:

```bash
zerolab status
zerolab-health
zerolab profiles
sudo zerolab up full
```

## USB profiles

`serial`, `ethernet`, `composite`, `hid`, `full`, `storage`, and `full-storage` are available interactively. The accepted boot wrapper intentionally allows only `serial`, `ethernet`, `composite`, `hid`, and `full` as automatic boot profiles. See [`docs/profiles.md`](docs/profiles.md).

## Dashboard

The accepted dashboard shows:

```text
b@<hostname>:~ $                        BAT 96%
------------------------------------------------
  WiFi: 192.168.x.x        | reserved pane
    BT: --                 | for future use
 RNDIS: 10.13.37.1         |
------------------------------------------------
FULL                              UP RNDIS ACM HID
```

`BAT` changes to `CHG` when the stateful PiSugar detector observes charging. Normal state changes use partial e-paper refresh; a full refresh is forced periodically to limit ghosting.

## Important caveats

ZeroLab deliberately ships without a USB VID/PID. The installer requires `--usb-vid` and `--usb-pid`, and runtime profiles read those values from `/etc/zerolab/zerolab.conf`. Use only identifiers you are authorized to use.

The public packaging also makes the displayed prompt username configurable. The accepted appliance displayed `b@zero:~ $`; the installer writes the selected account into `/etc/zerolab/display.env`.

## Documentation

- [Architecture](docs/architecture.md)
- [Hardware](docs/hardware.md)
- [Installation](docs/installation.md)
- [USB profiles](docs/profiles.md)
- [Networking and failover](docs/networking.md)
- [PiSugar power/telemetry](docs/power.md)
- [E-paper display](docs/display.md)
- [Validation matrix](docs/validation.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Security/publication notes](docs/security-notes.md)
- [Provenance](docs/provenance.md)
