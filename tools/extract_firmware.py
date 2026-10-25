"""Offline extraction only. Never runs the destructive vendor updater."""
import argparse, hashlib, json, struct, subprocess, zipfile
from pathlib import Path

FIRMWARE_SHA = 'f87e902138850f8ac2fcaef5bc8f3534ddfbfcda8f758833f336ef628a4e15a1'
KERNEL_SHA = 'e2c266aa18dd27cb4ad3921a9dab85ab4229559a10de3d99615f69b3714026a6'
DTB_SHA = 'a3f3c325a92ce10ea16b65315a1065afecefebc06ad8db16e2b778fef6c1db5f'
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--firmware',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seven-zip',type=Path,required=True,help='7-Zip executable with SquashFS support')
    a=p.parse_args()
    if sha(a.firmware.read_bytes()) != FIRMWARE_SHA: raise SystemExit('Not the verified firmware 144 / 92.zip. Refusing changed firmware.')
    a.out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(a.firmware) as z:
        for name in ('recovery.img','rootfs.squashfs'):
            matches=[n for n in z.namelist() if n.rsplit('/',1)[-1]==name]
            if len(matches)!=1: raise SystemExit('Missing or ambiguous '+name)
            (a.out/name).write_bytes(z.read(matches[0]))
    b=(a.out/'recovery.img').read_bytes()
    assert b[:8]==b'ANDROID!'
    k,r,s=[struct.unpack_from('<I',b,n)[0] for n in (8,16,24)]
    page=struct.unpack_from('<I',b,36)[0];assert page==2048
    align=lambda n:(n+page-1)//page*page
    kernel=b[page:page+k];ram=b[page+align(k):page+align(k)+r]
    dtb=b[page+align(k)+align(r):page+align(k)+align(r)+s]
    assert sha(kernel)==KERNEL_SHA and sha(dtb)==DTB_SHA
    assert ram[:2]==b'\x1f\x8b'
    (a.out/'components.json').write_text(json.dumps(dict(kernel_sha256=sha(kernel),dtb_sha256=sha(dtb),vendor_ramdisk_sha256=sha(ram),hardware_tested=False),indent=2))
    # Recovery BusyBox has no udhcpc/ifconfig. Overlay the vendor rootfs network
    # BusyBox and its matching glibc libraries, as in the reference V5/V6 path.
    net_paths=['bin/busybox','lib/ld-linux-armhf.so.3','lib/libc.so.6','lib/libm.so.6','lib/libresolv.so.2']
    net=a.out/'net';net.mkdir()
    subprocess.run([str(a.seven_zip.resolve()),'x',str((a.out/'rootfs.squashfs').resolve()),'-o'+str(net.resolve()),*net_paths],check=True)
    for name in net_paths:
        f=net/name
        if not f.is_file() or f.read_bytes()[:4]!=b'\x7fELF':raise SystemExit('Missing/invalid network runtime '+name)
    if a.seven_zip:
        paths=['lib/modules/6.1.60/extra/'+n+'.ko' for n in ('rtw_core','rtw_usb','rtw_8723d','rtw_8723du')]
        paths+=['lib/firmware/rtw88/rtw8723d_fw.bin']
        dest=a.out/'wifi';dest.mkdir()
        subprocess.run([str(a.seven_zip.resolve()),'x',str((a.out/'rootfs.squashfs').resolve()),'-o'+str(dest.resolve()),*paths],check=True)
        for name in paths:
            if not (dest/name).is_file(): raise SystemExit('Missing extracted Wi-Fi file '+name)
    print('Extracted locally. No device access; no updater executed. Newly built images need RAM testing.')

if __name__=='__main__':main()
