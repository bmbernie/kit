# Hardware

## Accepted bill of materials

- Raspberry Pi Zero W Rev 1.1
- microSD card (accepted build used approximately 16 GB)
- PiSugar2 standard 1200 mAh battery board
- Waveshare 2.13-inch V2 e-paper HAT
- micro-USB data cable for the Pi Zero USB gadget port
- appropriate cable/supply for the PiSugar charging connector
- optional phone/device supporting Bluetooth PAN/NAP for fallback networking

## Waveshare GPIO/SPI mapping

The accepted Waveshare Raspberry Pi driver uses:

| Function | BCM GPIO |
| --- | ---: |
| SPI CE0 / CS | 8 |
| SPI MOSI | 10 |
| SPI SCLK | 11 |
| Reset | 17 |
| Display power | 18 |
| Busy | 24 |
| Data/command | 25 |

SPI0 must be enabled. The accepted panel geometry is 122×250 natively and the ZeroLab UI renders it as a rotated 250×122 landscape framebuffer.

## PiSugar I2C

The accepted hardware exposed:

- `0x32` — RTC
- `0x75` — PowerIC while the PiSugar power section was active

The PowerIC may be absent when the Pi is powered only through its own USB connector and PiSugar output is off. The health collector treats that as a legitimate hardware state rather than a fatal error.

## Power/charging topology

Supported tested arrangement:

```text
host PC  ---> Pi Zero USB gadget/data port
charger  ---> PiSugar charging port
```

Do not hot-plug the e-paper HAT onto an energized GPIO header. Shut down and remove PiSugar output before attaching/removing the HAT.
