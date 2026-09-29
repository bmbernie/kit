# Troubleshooting

## Bettercap does not become ready

Check:

```bash
sudo systemctl status bettercap.service --no-pager -l
ip -br link
ss -ltn
journalctl -u bettercap.service -b --no-pager -l
```

The accepted readiness criteria are:

- `wlan0mon` exists;
- the interface is administratively UP;
- Bettercap listens on TCP/8081;
- the monitor/API condition is seen twice consecutively by the readiness gate.

If the start limit has been hit, first identify the failure, then after remediation:

```bash
sudo systemctl reset-failed bettercap.service
sudo systemctl start bettercap.service
```

## `wlan0` never appears

The safe launcher waits 20 seconds for kernel-created `wlan0`. If that times out, inspect kernel/firmware logs rather than adding unconditional driver reloads:

```bash
dmesg | grep -Ei 'brcm|brcmfmac|firmware|sdio'
ip -br link
```

## `wlan0mon` appears and disappears

The launcher intentionally requires five seconds of stability after monitor-interface creation. A failure here points to the Wi-Fi/firmware path, not Pwnagotchi's higher-level service.

## Pwnagotchi gate fails

Run the gate manually:

```bash
sudo /usr/local/sbin/pwnagotchi-wait-bettercap
sudo /usr/local/sbin/pwnagotchi-wait-pwngrid
```

Both scripts print bounded diagnostics on timeout.

## pwngrid is not ready

Check:

```bash
sudo systemctl status pwngrid-peer.service --no-pager -l
ss -ltnp | grep 8666
journalctl -u pwngrid-peer.service -b --no-pager -l
```

## Repeated restarts stop

That is intentional. Bettercap is limited to four starts per 180 seconds. Do not raise the limit merely to hide a persistent driver/firmware failure.
