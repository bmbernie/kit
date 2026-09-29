# E-paper dashboard

## Hardware

The accepted panel is a Waveshare 2.13-inch V2 using the upstream `epd2in13_V2` Python driver.

Native panel geometry: `122x250`.
ZeroLab landscape framebuffer: `250x122`, rotated 180 degrees for the tested physical HAT orientation.

## Layout

The accepted UI is inverted (black background, white content):

- 24 px header
- 74 px center
- 24 px footer
- center vertical split at x=167 (approximately 2/3 + 1/3)

Header:

- left: shell-style prompt `<user>@<hostname>:~ $`
- right: `BAT nn%` or `CHG nn%`

Center-left:

- right-justified `WiFi:` label + left-justified address
- right-justified `BT:` label + left-justified address
- right-justified `RNDIS:` label + left-justified address

Center-right is intentionally reserved for a future logo/glyph/state visualization.

Footer:

- left: selected operating profile (`FULL`, etc.)
- right: UDC state plus active gadget functions (`UP RNDIS ACM HID`, etc.)

## Fonts

- prompt: DejaVu Sans Mono Bold
- BAT/CHG: DejaVu Sans Mono Bold
- network rows: DejaVu Sans Mono
- footer: DejaVu Sans Mono Bold

## Hardware ownership

The frame renderer has a `--save-frame` mode that does not import the Waveshare hardware module. The persistent service is the sole GPIO/SPI owner. This avoids the `GPIO busy` contention that occurs when multiple processes instantiate `gpiozero` pins for the HAT simultaneously.

## Refresh policy

- startup: FULL base refresh
- normal network/gadget state changes: PARTIAL
- BAT/CHG transition: PARTIAL
- manual `systemctl reload zerolab-display.service`: PARTIAL after immediate battery sample
- periodic battery display update: PARTIAL
- after 20 partials: next update is FULL
- after six hours without a full refresh: next update is FULL
- service shutdown: deep sleep

A full refresh visibly flashes the screen multiple times; that is normal e-paper waveform behavior. Partial refresh is used for routine state changes to reduce flashing.

## Manual refresh

```bash
sudo zerolab-display-render
```

The wrapper reloads the systemd service, which signals only the main controller process.
