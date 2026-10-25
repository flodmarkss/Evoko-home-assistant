"""Prepare a fresh OFFLINE root directory. Refuses an existing browser profile.

Do not run against a mounted/live panel. No device or partition writes.
"""
import argparse, ipaddress, shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--wifi-files',type=Path)
    a=p.parse_args();r=a.root.resolve()
    profile=r/'var/lib/naso/firefox'
    if not (r/'usr/bin/firefox-esr').exists():raise SystemExit('Not an exported ARMv7 root')
    if profile.is_symlink():raise SystemExit('Profile symlink refused')
    if profile.exists() and any(x.name!='user.js' for x in profile.iterdir()):raise SystemExit('Existing profile state found. Preserved; use a FRESH Docker export.')
    conf=r/'etc/wpa_supplicant/naso.conf'
    if conf.exists():raise SystemExit('Existing Wi-Fi configuration found; preserved. Use a FRESH root.')
    source=a.build/'ha-proxy-arm'
    if not source.is_file():raise SystemExit('Build private images/proxy first')
    shutil.copyfile(source,r/'usr/local/sbin/naso-ha-proxy');(r/'usr/local/sbin/naso-ha-proxy').chmod(0o755)
    if a.wifi_files:
        for n in ('rtw_core','rtw_usb','rtw_8723d','rtw_8723du'):
            rel=Path('lib/modules/6.1.60/extra')/(n+'.ko');dst=r/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.wifi_files/rel,dst)
        rel=Path('lib/firmware/rtw88/rtw8723d_fw.bin');dst=r/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.wifi_files/rel,dst)
    else:
        # Core kiosk works over Ethernet. Avoid restarting a missing-driver service.
        s=r/'usr/local/sbin/naso-wifi-service'
        s.write_text('#!/bin/sh\nwhile :; do sleep 3600; done\n');s.chmod(0o755)
    profile.mkdir(parents=True,exist_ok=True);profile.chmod(0o700)
    assert set(x.name for x in profile.iterdir())=={'user.js'}
    print('Offline root prepared with preferences ONLY. First HA access requires the new owner to log in.')

if __name__=='__main__':main()
