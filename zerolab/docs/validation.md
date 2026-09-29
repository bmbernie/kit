# Validation matrix

The following behaviors were explicitly exercised before the v0.8d freeze.

| Area | Acceptance result |
| --- | --- |
| USB gadget cold boot | `full` came up configured with RNDIS + ACM + HID |
| RNDIS management | Pi `10.13.37.1/30`; SSH management proven |
| Controller teardown | ConfigFS gadget fully removed by `down` |
| Profile switching | serialized; fail-closed cleanup path |
| HID | harmless literal typing/release behavior proven |
| Storage | read-only mass-storage profile and `full-storage` proven |
| Wi-Fi primary | associated normally; remains preferred |
| Bluetooth PAN | fallback activated after Wi-Fi-association failure threshold |
| Recovery | PAN removed after Wi-Fi recovery threshold |
| E-paper | Waveshare 2.13 V2 full and partial update paths proven |
| Display/network integration | Wi-Fi/BT/RNDIS fields tracked live transitions |
| PiSugar | RTC `0x32`, PowerIC `0x75`, voltage/current telemetry |
| BAT/CHG | automatic BAT -> CHG -> BAT transitions proven |
| Cold boot | all three ZeroLab services enabled/active after real power cycle |
| Power | final validation remained `throttled=0x0` |

## Canonical accepted artifact

```text
/var/lib/zerolab/baselines/20260928-v0.8d.tar.gz
SHA-256 2e7d2af814c7269afd9c188a0af49c815250292f56274ab4d0f45e7e5e9785c1
```

The public repository is a sanitized packaging of that accepted artifact and not itself the canonical forensic freeze.

## Local validation

Run:

```bash
sudo ./scripts/validate.sh
```

For full Bluetooth acceptance, perform a controlled Wi-Fi disconnect from an RNDIS SSH session and observe PAN activation/recovery rather than running the destructive test automatically.
