# Home Assistant login and private material

The public rootfs is built from Alpine packages, not cloned from a running panel. Its Firefox profile starts with **one file: `user.js`**, which contains preferences only. `tools/prepare_root.py` refuses an existing profile containing any other state. It also refuses an existing panel WPA configuration.

There are no authentication cookies, `webappsstore.sqlite`, IndexedDB/localStorage directories, saved passwords, refresh/access tokens, or HA dashboard snapshots in the source distribution. Do not export a live panel's `/var/lib/naso/firefox`, `/etc/wpa_supplicant/naso.conf`, logs, backups or generated images to a public release.

`--ha-ip` is required when building. There is no contributor's backend address as a default. The relay connects only to that IPv4 address on TCP 8123 and binds its kiosk-facing listeners to loopback. It forwards HTTP and WebSocket traffic and **does not inject credentials or bypass HA authentication**. HTTP to the configured HA server must work on the trusted local network; HTTPS-only, reverse-proxy and IPv6 setups need an adapted transport. Do not disable certificate checks to make an HTTPS deployment work.

On first launch, enter the **new owner's** HA credentials on the panel. Afterward, the browser stores that owner's login on that panel only. Use a dedicated, minimally privileged HA account for a wall display. A fresh profile causes the normal HA login screen unless the **owner's own HA configuration** deliberately bypasses login, such as a trusted-network authentication configuration.

The build tool generates a random per-installation root-control key. Generated images contain it and are private. `.gitignore` excludes build directories, images and typical profile/credential files. This is defense in depth, not a substitute for reviewing release contents.

The rescue/control protocol is authenticated **plaintext HTTP**, with root command execution on TCP 8089. Use only on a trusted isolated LAN, never port-forward it or publish its key. No SSH/password login is installed by this project. Memory-related Firefox settings reduce process isolation and restrict background traffic; this is a dedicated local kiosk, not a general-purpose secure browsing workstation.

The original owner's working panel is untouched when preparing or publishing this repository. Publishing does not log that panel out and does not publish its session.
