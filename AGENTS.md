# Working on this project

Read README.md, docs/INSTALL.md and docs/PRIVACY.md first. This is an experimental hardware project validated on one Naso i.MX6 DualLite board, not every Evoko product.

Do not upload live browser profiles, authentication/storage databases, WPA profiles, root-control keys, generated boot images, original eMMC backups, screenshots of dashboards, or device logs. Public defaults must never point at a contributor's own Home Assistant server. Fresh installations start at the owner's HA login.

Identify serial/CID/partition map anew. Verify full original user-area and boot0/boot1 backups against source SHA256 before persistent writes. Never execute the vendor firmware updater, format the eMMC, replace U-Boot, unlock/fuse, or reuse another panel's backup. Run RAM tests first, then disk-root tests, then separately review the boot target. Preserve recovery, bootloader and partition table.

Do not copy historical PID/IP/identity constants into a generic installer. HTTP 200 from the root control endpoint is not a shell success indicator. Verify markers, size and hashes. The control transport is unencrypted LAN-only root access; do not expose it publicly.

Distinguish offline-built, hardware-tested, warm-reboot-tested and physically cold-start-tested. Do not describe newly generated vendor/Docker images as hardware-tested. Keep an already working panel running when editing documentation. No device operations are required to publish this repository.

For keyboard X11 changes, ignore ConfigureNotify events from both our own buttons AND the keyboard; otherwise restacking can cause a busy loop. Qt Wi-Fi dialogs need explicit input focus without a window manager. Keep the keyboard available below dialogs.
