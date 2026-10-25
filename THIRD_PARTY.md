# Third-party components

This repository distributes project source and configuration, not vendor firmware, eMMC images or package binaries.

- Linux kernel / DTB / matching WLAN modules and firmware: extracted locally from the owner's acquired Biamp/Evoko firmware 144 (`92.zip`). Preserve applicable supplier license/source notices. [Biamp's firmware reference](https://support.biamp.com/Evoko/z_Evoko_Workplace/Server-Migration_Follow-Up_Guide/Step_6_-_Updating_a_Configured_Naso_Device_from_v1_0_to_v2_0) documents the supplier URL. **Do not follow its update/install procedure for this project.** We extract files offline only.
- Alpine Linux: [alpinelinux.org](https://alpinelinux.org/), package sources/build recipes at [Alpine aports](https://gitlab.alpinelinux.org/alpine/aports). APK signature verification remains enabled.
- Firefox ESR: Mozilla / [source](https://firefox-source-docs.mozilla.org/). Package-selected version depends on the Alpine branch, so a fresh Docker build is not a claim of bit-for-bit reproduction of the historical reference root.
- Xorg, Matchbox Keyboard, Qt 6 and `wpa_supplicant`/`wpa_gui`: their package licenses apply. [Upstream wpa_supplicant](https://w1.fi/wpa_supplicant/).
- Zig compiler: [ziglang.org](https://ziglang.org/), 0.14.1 used for project ARM helpers.
- Docker/BuildKit/QEMU: optional build tools, not part of runtime.

Before redistributing a derived binary image, satisfy each included component's license and corresponding-source obligations. The repository's GPL-3.0 license does not relicense supplier firmware or remove those obligations.
