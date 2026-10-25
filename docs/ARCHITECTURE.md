# Architecture and troubleshooting

```text
Original U-Boot → chosen boot partition → Linux 6.1.60 + board DTB + small initramfs
  → Ethernet/DHCP + private authenticated rescue/control endpoint
  → existing data partition / naso-linux/root on eMMC
  → Alpine ARMv7 chroot → Xorg fbdev + Firefox ESR + local HA relay
  → keyboard/Wi-Fi button + wpa_gui + NTP + proximity dimming
```

All rendering is local. The loopback relay permits local HTTP/WebSocket to the explicitly chosen HA IPv4 server. A second loopback port denies background proxy traffic. The launcher redirects to `/` on the local relay; no user/dashboard identifier or token is embedded.

The reference board uses 16-bit fbdev and real VT graphics switching. `-sharevts` caused display problems. Firefox's actual top-level window is sized after creation to 1024×768; merely requesting kiosk mode was insufficient. Matchbox keyboard occupies the bottom section; Qt Wi-Fi dialogs are fitted above it. Without a window manager, each new dialog must be explicitly focused.

The X11 toggle must ignore `ConfigureNotify` from its own buttons **and the keyboard** to avoid a raise/configure event loop. Reopening Wi-Fi should reuse the same GUI process. Closing the settings GUI must not kill `wpa_supplicant` or drop an existing connection.

OOM while switching dashboards: verify executable/mapped libraries really live on eMMC, not a 275 MB RAM root. Measure `MemAvailable`, anonymous/file RSS and kernel OOM logs. Low `MemFree` alone is not an error. Swap syscalls returned ENOSYS on the reference kernel. Disabling JIT was not the solution. WebKitGTK failed without a working EGL environment; do not claim it as a proven lower-memory replacement.

Kernel firmware loading starts in the outer namespace, not the Alpine chroot. `wifi-service.sh` copies firmware into `/proc/1/root/lib/firmware/rtw88` and strictly loads the matching modules. The stable WLAN MAC is obtained from the **current panel's** own boot command line. Ethernet and Wi-Fi coexist, with Wi-Fi default metric 600 and the kernel skipping routes on a down link; test actual fallback before relying on it.

The reference U-Boot reports `secure:yes` and `unlocked:no`; static analysis showed its MMC `boota` path continued without cryptographic verification. This is evidence for that bootloader binary only. Successful Fastboot RAM boot does not prove another bootloader accepts a normal eMMC image. Keep original bootloader/fuses and inspect your own target path.

HTTP 200 from the control server only proves a response stream opened. For shell operations require explicit completion markers, byte counts and source/readback SHA256. Never treat Fastboot `OKAY` as proof that init ran. Detect a new boot ID and expected init marker after a restart.
