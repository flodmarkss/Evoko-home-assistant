# Validation of the public source export

The original reference hardware results are summarized in README.md. These are separate from tests of this new public reproduction path.

On the publishing workstation:

- `python -m unittest discover -s tests -v`: all four tests passed. They require an explicit HA address, reject and preserve an existing browser session, and check a fresh root contains preferences only.
- Python source compilation passed.
- Firmware extraction from the pinned `92.zip` succeeded, including all four WLAN modules and the radio firmware. No vendor updater or device command was run.
- Zig 0.14.1 built both rescue and installed ARM images from the pinned recovery base using a documentation-only test backend address. Generated files and random control keys stayed outside the public source tree.
- ARM syntax checks passed for the keyboard/Wi-Fi button and proximity daemon; the local X11 SDK emitted an existing endian-header precedence warning.
- Public files were checked against the original private control key and for local credentials, profiles, private LAN addresses and workstation paths before publication.

Not performed in this publishing pass: Docker/BuildKit ARMv7 rootfs build, deployment of the newly generated images, full new-panel installation, real Wi-Fi association/failover, or physical cold-start. The original working owner's kiosk was not modified. Public CI performs source/privacy/shell/C syntax checks; it does not prove hardware compatibility or a working complete image.
