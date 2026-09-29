# PiSugar2 power and telemetry

## Bounded register helper

`pisugar_read.py` is root-owned and only permits these read operations:

| Operation | I2C address | Register |
| --- | --- | --- |
| `rtc` | `0x32` | `0x00` |
| `power-a2` | `0x75` | `0xA2` |
| `power-a3` | `0x75` | `0xA3` |
| `power-a4` | `0x75` | `0xA4` |
| `power-a5` | `0x75` | `0xA5` |
| `power-55` | `0x75` | `0x55` |

The helper uses `i2cget` only; arbitrary register writes are not exposed.

## Health fields

`zerolab-health --json` reports:

- RTC presence
- PowerIC presence
- battery voltage
- battery current
- voltage-curve SOC estimate
- hardware charge-input bit (where supported)
- Raspberry Pi throttling, temperature, ARM clock, uptime and memory

The stateless `battery_charging` field is intentionally `null` in v0.8d. Charging determination requires history and is owned by the persistent display/power controller.

## BAT/CHG detector

The accepted PiSugar2 revision did not provide a useful direct charge-input indication at register `0x55` bit 4. The display service therefore maintains a six-sample voltage history and treats charging as confirmed after two rising-history observations. Falling/flat history returns the state to BAT promptly.

If a direct `0x55` plug indication is ever observed true, the service remembers that the hardware supports that indication and can use subsequent true/false edges directly.

## Battery percentage

The health collector uses the PiSugar2 1200 mAh voltage curve and linear interpolation. The accepted post-charge battery-only validation remained around 4.16 V for roughly two minutes and legitimately evaluated at approximately 100%.

This is still a voltage-derived estimate rather than coulomb counting; users should treat it as an approximate state-of-charge indicator.

## Charging

Charge the battery through the PiSugar charging connector. The Pi Zero may remain attached to the host through its USB gadget/data port at the same time.
