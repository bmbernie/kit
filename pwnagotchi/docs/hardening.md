# Bettercap and service hardening

## Safe Bettercap launcher

The accepted launcher deliberately does **not** unconditionally reload `brcmfmac` immediately before monitor-mode creation. The build notes in the launcher record that this sequence had been observed to crash the BCM43430 firmware/SDIO backplane.

The launcher instead:

1. waits up to 20 seconds for kernel-created `wlan0`;
2. gives the initialized firmware a 3-second quiet period;
3. creates the monitor interface through the existing Pwnagotchi helper;
4. verifies `wlan0mon` remains present and UP for five consecutive seconds;
5. only then starts Bettercap using the selected Pwnagotchi caplet.

Any failed bounded prerequisite causes the launcher to exit non-zero so systemd can account for the failure.

## Pwnagotchi readiness gate

`pwnagotchi-wait-bettercap` prevents Pwnagotchi from starting merely because systemd considers a `Type=simple` Bettercap process active. It requires both the monitor interface and Bettercap API to be genuinely ready.

## pwngrid readiness gate

`pwnagotchi-wait-pwngrid` waits up to 60 seconds for the peer API on `127.0.0.1:8666`. Failure emits service status and socket diagnostics before exiting non-zero.

## Bounded restart policy

The accepted drop-in is:

```ini
[Unit]
StartLimitIntervalSec=180
StartLimitBurst=4
```

This bounds Bettercap to four service starts within a three-minute window. The overlay does not silently clear a tripped start limit; investigate the underlying Wi-Fi/firmware failure, then use `systemctl reset-failed bettercap.service` only after remediation.

## Pwnagotchi launcher behavior

The accepted launcher does not unconditionally restart Bettercap each time Pwnagotchi restarts. If Bettercap is already active, the launcher leaves it alone. This avoids forcing another monitor-interface/firmware initialization cycle during unrelated Pwnagotchi restarts.
