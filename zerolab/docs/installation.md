# Installation

## Target platform

The accepted baseline was Raspberry Pi OS Lite 32-bit / Raspbian 13 (`trixie`) on a Pi Zero W (ARMv6). The repository installer assumes Debian/Raspberry Pi OS packaging and systemd.

## Before installation

1. Install Raspberry Pi OS Lite 32-bit.
2. Configure Wi-Fi and SSH using normal Raspberry Pi OS procedures.
3. Attach the PiSugar2 and Waveshare HAT while powered off.
4. If Bluetooth fallback is wanted, pair/trust the phone first. The phone must expose Bluetooth NAP/PANU service.
5. Decide which local account will be allowed to run the bounded PiSugar health reads.
6. Obtain a USB VID/PID pair you are authorized to use. ZeroLab intentionally provides no default identity.

## Install

From the `zerolab` directory:

```bash
sudo ./scripts/install.sh \
  --user b \
  --usb-vid 0xVVVV \
  --usb-pid 0xPPPP \
  --phone-mac AA:BB:CC:DD:EE:FF \
  --boot-profile full
```

If Bluetooth fallback is not yet configured, omit `--phone-mac`. The installer will install ZeroLab but leave `zerolab-netfailover.service` disabled until a phone profile is configured.

The installer:

- installs required Debian packages
- copies ZeroLab under `/usr/local/lib/zerolab`
- creates command wrappers under `/usr/local/sbin`
- writes `/etc/zerolab/zerolab.conf`, including the configured USB VID/PID
- writes a bounded sudoers file for the selected account
- configures the RNDIS NetworkManager profile
- optionally configures the Bluetooth PAN NetworkManager profile
- enables I2C, SPI0, and DWC2 peripheral mode in `/boot/firmware/config.txt`
- enables the gadget and display services
- enables network failover only when a phone MAC was supplied

Reboot after installation:

```bash
sudo reboot
```

## Pairing/trusting the Bluetooth phone

Pairing behavior varies by phone. The accepted build was paired by making the Pi discoverable/pairable and initiating pairing from the phone. After pairing, mark the device trusted:

```bash
bluetoothctl
power on
agent KeyboardDisplay
default-agent
discoverable on
pairable on
# initiate pairing from the phone, then:
trust AA:BB:CC:DD:EE:FF
quit
```

Check that the phone advertises NAP before relying on failover:

```bash
bluetoothctl info AA:BB:CC:DD:EE:FF
```

## Read-only storage image

The accepted 16 MiB image is not included in the repository. To create a replacement blank FAT16 image labeled `ZEROLAB`:

```bash
sudo ./scripts/build-storage-image.sh
```

This creates the filename expected by the accepted `storage` and `full-storage` profiles and writes a matching SHA-256 file.

## Validate

After reboot:

```bash
sudo ./scripts/validate.sh
```

Then check manually:

```bash
zerolab status
zerolab-health
zerolab-netfailover --status
```

## USB VID/PID configuration

ZeroLab intentionally contains no default USB VID/PID. Installation requires values you are authorized to use:

```bash
sudo ./scripts/install.sh \
  --user b \
  --usb-vid 0xVVVV \
  --usb-pid 0xPPPP
```

The resulting values are stored in `/etc/zerolab/zerolab.conf` as `USB_VID` and `USB_PID`. To change them later:

```bash
sudo ./scripts/set-usb-identity.sh 0xVVVV 0xPPPP
```

The new identity takes effect on the next gadget activation or reboot.
