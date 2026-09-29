# Networking

## NetworkManager policy

The accepted overlay contains two NetworkManager configuration fragments.

`90-pwnagotchi-wifi-unmanaged.conf` declares `wlan0` and `wlan0mon` unmanaged so NetworkManager does not contend with Pwnagotchi/Bettercap for the capture interfaces.

`90-pwnagotchi-dns.conf` sets NetworkManager DNS handling to `none` in the accepted build.

These settings are copied exactly from the sanitized final artifact. Review them against the networking model of the target host before installation because they affect system-wide NetworkManager behavior.

## USB gadget networking

The accepted device also had Raspberry Pi USB-gadget support enabled, but that implementation was outside the final-201303 publication artifact. This overlay therefore does not attempt to install or reproduce the USB gadget stack.

Do not publish host-specific Ethernet, USB-gadget, or Wi-Fi addresses as required configuration. Treat them as deployment values.
