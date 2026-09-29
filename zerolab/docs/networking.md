# Networking and failover

## RNDIS management network

The Pi's USB gadget address is fixed at:

```text
10.13.37.1/30
```

A typical host uses:

```text
10.13.37.2/30
```

No default route or DNS is assigned to the RNDIS management link.

## Wi-Fi primary network

`wlan0` is expected to be managed separately by NetworkManager. ZeroLab does not store or publish Wi-Fi credentials.

## Bluetooth PAN fallback

The tested policy uses a NetworkManager Bluetooth PANU connection called `zerolab-phone-tether`. It receives an address from the phone by DHCP and uses route metric 900, so the normal Wi-Fi route can remain preferred.

The accepted configuration was:

```text
CHECK_INTERVAL=10
FAIL_THRESHOLD=3
RECOVER_THRESHOLD=3
BT_RETRY_COOLDOWN=60
STARTUP_GRACE=30
```

This means Wi-Fi must be observed unassociated for three checks before fallback is attempted. After Wi-Fi returns, three connected checks are required before PAN is taken down.

## Important semantic choice

Failover tests **Wi-Fi association only**. It intentionally does not probe DNS, Internet reachability, a default route, or a public IP address.

Therefore:

- Wi-Fi associated + Internet outage -> Bluetooth stays off.
- Wi-Fi not associated -> Bluetooth fallback is eligible.

## Manual checks

```bash
zerolab-netfailover --status
nmcli connection show zerolab-phone-tether
ip -4 -br addr show dev wlan0
ip -4 -br addr show dev bnep0
ip route
```

## Accepted end-to-end behavior

The final acceptance demonstrated:

1. RNDIS SSH remained available while Wi-Fi was deliberately disconnected.
2. Bluetooth PAN activated and obtained a DHCP address.
3. The e-paper dashboard changed Wi-Fi to `--` and displayed the Bluetooth IP.
4. Wi-Fi was restored.
5. Bluetooth PAN was removed after the recovery threshold.
6. The dashboard returned to Wi-Fi IP / BT `--` automatically.
