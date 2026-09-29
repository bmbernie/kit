# Architecture

The Pwnagotchi kit is an **overlay** on a compatible Pwnagotchi base installation. The frozen artifact contains the files that were changed or added to make the accepted device boot and recover deterministically; it is not a full root filesystem.

## Startup dependency chain

The accepted startup path is:

```text
NetworkManager
    |
    v
bettercap.service
    |
    +--> bettercap-launcher-safe
    |       |
    |       +--> wait for wlan0 (20 s bound)
    |       +--> 3 s firmware-settle period
    |       +--> create wlan0mon
    |       +--> require wlan0mon UP for 5 consecutive seconds
    |       +--> exec Bettercap on wlan0mon
    |
    +--> pwngrid-peer.service waits for Bettercap readiness
    |
    +--> pwnagotchi.service waits for Bettercap readiness
            |
            +--> waits for pwngrid-peer readiness
            +--> pwnagotchi-launcher
```

The Bettercap readiness gate requires both an administratively-UP `wlan0mon` and a listener on TCP/8081 for two consecutive observations within 30 seconds. The pwngrid gate requires `pwngrid-peer.service` to be active and TCP/8666 to be listening within 60 seconds.

## Failure containment

`bettercap.service` is protected by a systemd unit start limit of four starts within 180 seconds. This bounds repeated firmware/monitor-interface failure loops instead of allowing indefinite restart churn.

## Wi-Fi ownership

NetworkManager is configured to leave `wlan0` and `wlan0mon` unmanaged. Bettercap/Pwnagotchi therefore own their operational Wi-Fi state without NetworkManager trying to reconfigure those interfaces.

## Upstream-derived plugin source

The WPA-SEC and WiGLE files are not presented as original `kit` code. They are retained under `upstream/modified-plugins/` with GPL attribution and provenance metadata.
