# Validation baseline

The publication source is derived from the accepted `final-201303` archive with SHA-256:

```text
a183fae8ce88b7722878278cbd4c3ed83b0352f5c53ef0c7b0e9386a610cdfe9
```

The final artifact's source manifest contained the Bettercap drop-ins, Pwnagotchi/pwngrid readiness gates, launchers, NetworkManager policy, logrotate configuration, `i2c-dev` configuration, and modified WPA-SEC/WiGLE plugins.

A smaller later-named `known-good` snapshot was compared by filename against `final-201303`; `final-201303` additionally contained the final logrotate policy, bounded Bettercap restart policy, modified WPA-SEC/WiGLE plugin files, and the WPA-SEC runtime database. The database was removed for publication.

## Publication-source validation

The sanitized export verified:

- canonical source archive hash matched;
- `.wpa_sec_db` was removed;
- private `config.toml` was excluded;
- all expected hardening components remained present;
- an obvious populated-credential assignment scan returned no matches;
- the documentation-source SHA-256 manifest verified.

## Runtime policy to revalidate on a target

A target installation should demonstrate:

1. `bettercap.service` starts without forcing an unconditional Wi-Fi driver reload;
2. `wlan0mon` remains stable for the launcher's five-second gate;
3. TCP/8081 is available before Pwnagotchi starts;
4. TCP/8666 is available before Pwnagotchi's pwngrid gate completes;
5. Bettercap start attempts are bounded to four per 180 seconds;
6. Pwnagotchi restarts do not unnecessarily restart an already-active Bettercap service.

Use `scripts/validate-live.sh` as a starting point, then perform at least one real cold boot before treating a new device as accepted.
