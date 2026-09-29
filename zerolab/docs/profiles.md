# USB gadget profiles

The controller command is:

```bash
zerolab profiles
sudo zerolab up <profile>
sudo zerolab down
zerolab status
```

## Profiles

| Profile | Functions | Typical host devices |
| --- | --- | --- |
| `serial` | ACM | serial/COM port |
| `ethernet` | RNDIS | USB Ethernet |
| `composite` | RNDIS + ACM | Ethernet + serial |
| `hid` | HID keyboard | keyboard |
| `full` | RNDIS + ACM + HID | Ethernet + serial + keyboard |
| `storage` | read-only mass storage | removable disk |
| `full-storage` | RNDIS + ACM + HID + read-only storage | all four functions |

`down` is a teardown operation rather than an activation profile.

## Boot profiles

The accepted `boot.sh` permits only:

- `serial`
- `ethernet`
- `composite`
- `hid`
- `full`

`storage` and `full-storage` remain operator-selected modes. This avoids automatically presenting a disk during every boot.

## USB identity

Activation profiles do not contain a hard-coded USB VID/PID. They read `USB_VID` and `USB_PID` from `/etc/zerolab/zerolab.conf` and fail closed when either value is absent or malformed. Configure values you are authorized to use during installation:

```bash
sudo ./scripts/install.sh --user b --usb-vid 0xVVVV --usb-pid 0xPPPP
```

Or update an installed appliance:

```bash
sudo ./scripts/set-usb-identity.sh 0xVVVV 0xPPPP
```

The accepted RNDIS function uses fixed locally administered MAC addresses:

- gadget: `02:13:37:00:00:01`
- host: `02:13:37:00:00:02`

The Pi side is statically addressed `10.13.37.1/30` and the host side is normally configured as `10.13.37.2/30` with no gateway or DNS.

## HID engine

`zerolab-hid` is intentionally bounded:

```bash
sudo zerolab-hid release
sudo zerolab-hid type 'hello world'
```

The engine validates all characters before transmitting, limits per-key delay to a bounded range, and sends release reports after every key and on cleanup paths. It is not an arbitrary HID payload executor.

## Storage

The mass-storage LUN sets `ro=1`, `removable=1`, and `cdrom=0`. The backing image hash is verified before profile activation.
