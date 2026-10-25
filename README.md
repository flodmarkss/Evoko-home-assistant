# Evoko Naso → Linux Home Assistant kiosk

Repurpose an **Evoko Naso ENX1001** as a standalone Home Assistant touchscreen. Linux, Xorg and Firefox run locally from the panel's internal storage; no PC renderer is needed during normal operation.

**Every fresh installation starts at your own Home Assistant login.** This repository contains no contributor's browser profile, HA token, Wi-Fi password, root-control key or eMMC backup. You supply your own HA server address at build time. After signing in, that panel can retain **your** session across reboots.

**Svenska:** Börja med [installationsguiden](docs/INSTALL.md). En ny installation har tom webbläsarprofil och visar din egen Home Assistants inloggning. Projektägarens konto och hemnät följer inte med. [Wi-Fi och daglig användning](docs/USAGE.md).

## Features

- Native Firefox kiosk, 1024×768, dark theme and local rendering.
- Touch input, bottom-right **ABC** keyboard button, and **Wi-Fi / HA** settings button.
- Internal RTL8723DU Wi-Fi, **2.4 GHz**, with local password entry through `wpa_gui`.
- Proximity/touch wake; dim to **5% after 60 seconds**, never intentionally turn the backlight off.
- NTP clock correction and configurable timezone.
- Normal boot from eMMC using original U-Boot; supervisor restarts kiosk services.

## Compatibility and project status

The reference installation was verified on **one** Naso with i.MX6 DualLite, ARMv7, 512 MB RAM, FT5x06 touch, 1024×768 LCD and Linux 6.1.60. This does **not** establish compatibility with all Naso revisions, Evoko Liso or every product called Evoko.

The critical memory fix was putting the Alpine userspace on **eMMC**. A ~275 MB RAM root plus Firefox caused OOM crashes when switching dashboards. Disk-backed program pages were reclaimable; repeated dashboard changes then worked.

| Path / feature | Evidence |
|---|---|
| Reference disk-root kiosk and normal warm reboot | Verified on the original panel; owner confirmed operation |
| Fullscreen, dark mode, soft keyboard, local HA login/dashboard navigation | Verified on reference installation |
| Presence dimming, including user-selected 5% / 60 seconds | Verified on reference installation |
| Wi-Fi driver, scan, settings GUI, synthetic profile save/reload/removal | Verified; real Wi-Fi association and cable failover were not tested in that pass |
| Generic Docker rootfs and vendor-recovery-based image recipes in this repo | New public reproduction path; offline checks only, **not end-to-end hardware tested** |
| Physical PoE cold-start on another panel | Not established |

This is an experimental build-and-install project, **not a one-click universal firmware**. Do not flash a newly generated image because a compiler succeeded. Read [INSTALL.md](docs/INSTALL.md) and RAM-test your exact board first.

## Start here

1. [Hardware, backup, build, RAM test and installation](docs/INSTALL.md)
2. [Authentication and privacy](docs/PRIVACY.md)
3. [Wi-Fi, keyboard, brightness and clock](docs/USAGE.md)
4. [Architecture and troubleshooting](docs/ARCHITECTURE.md)
5. [Instructions for AI agents](AGENTS.md)

Python 3, Zig 0.14.1, USB Fastboot, a few GB of free space, Docker buildx with ARMv7 support (or an ARMv7 Linux builder), and the **verified firmware 144 / `92.zip`** are needed for the public build path. Firmware binaries and third-party package archives are deliberately obtained from their suppliers locally, rather than copied from a user's running panel.

No firmware updater is executed by the supplied tools. The vendor's updater is destructive and must **not** be used for this Linux installation. Original U-Boot, recovery, boot0/boot1 and partition-table areas must be preserved. Persistent installation changes the chosen data folder and boot partition; it is not byte-identical Android preservation.

## Source layout

`sources/` contains the native X11 keyboard/Wi-Fi button, proximity daemon, loopback TCP/WebSocket relay and authenticated rescue control server. `assets/` contains kiosk/init/DHCP/time/Wi-Fi scripts, Firefox preferences and screen configuration. `tools/` contains offline image/root preparation, firmware extraction, LAN transport and backup tools. `tests/` checks privacy and offline behavior.

The user-selected GitHub repository license is GPL-3.0. It covers this project's code; third-party packages/firmware retain their own licenses. See [THIRD_PARTY.md](THIRD_PARTY.md). This project is independent of Biamp/Evoko and Home Assistant.
