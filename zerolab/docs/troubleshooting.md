# Troubleshooting

## No `/dev/spidev0.*`

Check `/boot/firmware/config.txt` contains:

```text
dtparam=spi=on
```

Then reboot. `spi_bcm2835` and `spidev` should be loaded and `/dev/spidev0.0` / `.1` should exist.

## Display service reports `GPIO busy`

Only the persistent display service should instantiate the Waveshare hardware driver. Frame-only rendering must not import the hardware module. Check for stray diagnostic/demo processes and stop them before restarting the service.

```bash
ps aux | grep -E 'dashboard_once|oneshot_v2|zerolab/display'
sudo systemctl restart zerolab-display.service
```

## Full refresh flashes repeatedly

Expected for the e-paper full waveform. Routine updates should log `mode=PARTIAL`. A full update is intentionally used at startup and periodically for ghosting control.

## `CHG` does not change immediately

On the tested PiSugar revision, charging is inferred from voltage history rather than a reliable direct plug bit. Allow several samples. A service reload forces an immediate new sample:

```bash
sudo systemctl reload zerolab-display.service
```

## `0x75` missing from `i2cdetect`

If the Pi is powered through its own USB connector while the PiSugar output is off, the PiSugar PowerIC may be absent while the RTC at `0x32` remains visible. Re-test while PiSugar is actively powering the Pi.

## Bluetooth PAN does not activate

Check:

```bash
zerolab-netfailover --status
bluetoothctl info AA:BB:CC:DD:EE:FF
nmcli connection show zerolab-phone-tether
journalctl -u zerolab-netfailover.service -b
```

The phone must be paired, bonded/trusted, and expose NAP. The failover service also has startup grace and retry cooldown timers.

## Wi-Fi Internet is broken but Bluetooth does not start

This is intentional. v0.8d tests Wi-Fi **association**, not Internet reachability.

## RNDIS host cannot reach `10.13.37.1`

Confirm `usb0` exists and the host has `10.13.37.2/30` with no gateway/DNS. On the Pi:

```bash
zerolab status
ip -4 -br addr show dev usb0
nmcli connection show zerolab-usb
```

## Storage profile fails

Build/install the expected image and checksum:

```bash
sudo ./scripts/build-storage-image.sh
```

The profile intentionally refuses to attach a backing image whose SHA-256 check fails.
