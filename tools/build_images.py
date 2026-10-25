"""Offline builder only: creates a private control key and ARM boot images.

No USB or device connection, flashing, mount or installation is performed.
Accepts verified V6 or firmware-144 recovery components. Recovery-based output is a new, untested RAM variant. The vendor init is replaced by an appended overlay.
"""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import secrets
import struct
import subprocess

BASE = Path(__file__).resolve().parent.parent
BASE_SHA = 'dcd4adc5fe8b0c8b45bcf5728088016c7fee3378dfd83d0d11d5cbc843f31210'

NETWORK_HASHES = {'bin/busybox': '5b6175f21d7ed3d3b65a13fa752e050b87de42b93282ecee319caff33aa82f9b', 'lib/ld-linux-armhf.so.3': '977763392efa689292753f9d698ccd2587563777266398d91f42420f3487a4e2', 'lib/libc.so.6': 'ce833d90473071db1f039808a746c9f96b8962bcd620191f7b127eb33d6756c2', 'lib/libm.so.6': '56e3304fffb63a396988da9cd3b12643b3076465554a5b7fae76ce12dae2bf2c', 'lib/libresolv.so.2': '0581af919fa94996cbe13a360f3fb7bd2db2f01dde6cad27eb633a3aeac49986'}

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zig', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--mode', choices=['rescue', 'installed'], default='rescue')
    p.add_argument('--data-partition', help='Verified Linux partition basename, e.g. mmcblk2p4')
    p.add_argument('--ha-ip', required=True)
    p.add_argument('--base-image', type=Path, required=True)
    p.add_argument('--network-root', type=Path, help='Extracted fw144/net directory; mandatory for a recovery base')
    a = p.parse_args()
    if a.mode == 'installed' and not re.fullmatch(r'mmcblk[0-9]+p[0-9]+', a.data_partition or ''):
        p.error('Installed mode requires --data-partition from the target device inventory')
    ha = str(ipaddress.IPv4Address(a.ha_ip))
    b = a.base_image.read_bytes()
    if sha(b) not in (BASE_SHA, '015bf20567a44062f882bb4726aae35311a41aa787ee51dba93e719067a89309'):
        raise RuntimeError('Base image hash mismatch')
    if sha(b) != BASE_SHA and not a.network_root:
        p.error('Recovery BusyBox lacks DHCP. Supply --network-root vendor/fw144/net from extract_firmware.py')
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    keyfile = out/'control-key.txt'
    if not keyfile.exists():
        keyfile.write_text(secrets.token_hex(32)+'\n', encoding='ascii')
    key = keyfile.read_text().strip()
    if not re.fullmatch('[0-9a-f]{64}', key):
        raise RuntimeError('Unexpected key format; key file preserved')
    header = out/'control-key.h'
    header.write_text('#define CONTROL_KEY "'+key+'"\n', encoding='ascii')
    control = out/'naso-control-arm'
    common = [str(a.zig.resolve()), 'cc', '-target', 'arm-linux-musleabihf',
              '-mcpu=cortex_a9', '-static', '-Oz', '-s', '-Wall', '-Wextra']
    subprocess.run(common+['-include', str(header), str(BASE/'sources/ram-control.c'),
                           '-o', str(control)], check=True)
    proxy_source = (BASE/'sources/ha-proxy.c').read_text()
    (out/'ha-proxy.c').write_text(proxy_source, encoding='utf-8')
    subprocess.run(common+['-DHA_IPV4="'+ha+'"', str(out/'ha-proxy.c'), '-o', str(out/'ha-proxy-arm')], check=True)
    init = (BASE/'assets/init.sh').read_text()
    if a.mode == 'rescue':
        # Keep device/proc/sys, loopback, control and DHCP; never mount eMMC.
        init = init.split('R=/mnt/naso-data/naso-linux/root\n')[0]
        init = init.replace('NASO_NATIVE_DISK_INIT_V2', 'NASO_RESCUE_RAM_ONLY_V1')
        init += '''while :; do
 if ! kill -0 "$control" 2>/dev/null; then /bin/naso_control & control=$!; fi
 $B sleep 5
done
'''
    else:
        init = init.replace('/dev/mmcblk2p4', '/dev/'+a.data_partition)
    (out/(a.mode+'-init.sh')).write_bytes(init.encode())
    page = struct.unpack_from('<I', b, 36)[0]
    assert page == 2048
    align = lambda n: (n+page-1)//page*page
    k, r, s = [struct.unpack_from('<I', b, n)[0] for n in (8,16,24)]
    ro = page+align(k)
    kernel, original, dtb = b[page:page+k], b[ro:ro+r], b[ro+align(r):ro+align(r)+s]
    assert s == 40827 and original[:2] == b'\x1f\x8b'
    overlay = bytearray()
    def add(name, data, mode=0o100755):
        name = name.encode()+b'\0'
        fields = [9001,mode,0,0,1,0,len(data),0,0,0,0,len(name),0]
        overlay.extend(b'070701'+b''.join(f'{v:08x}'.encode() for v in fields)+name)
        overlay.extend(b'\0'*(-len(overlay)%4))
        overlay.extend(data)
        overlay.extend(b'\0'*(-len(overlay)%4))
    add('init', init.encode())
    add('dhcp-native.sh', (BASE/'assets/dhcp.sh').read_bytes())
    add('bin/naso_control', control.read_bytes())
    if sha(b) != BASE_SHA:
        for name, expected in NETWORK_HASHES.items():
            data = (a.network_root/name).read_bytes()
            if sha(data) != expected:
                raise RuntimeError('Network runtime hash mismatch: '+name)
            add(name, data)
    add('TRAILER!!!', b'', 0)
    ram = original+b'\0'*(-len(original)%4)+overlay
    hdr = bytearray(b[:page])
    struct.pack_into('<I', hdr, 16, len(ram))
    hdr[48:64] = ('NASO_'+a.mode.upper()).encode().ljust(16,b'\0')
    h = hashlib.sha1()
    for data in (kernel,ram,dtb):
        h.update(data)
        h.update(struct.pack('<I',len(data)))
    hdr[576:608] = h.digest().ljust(32,b'\0')
    image = bytes(hdr)
    for data in (kernel,ram,dtb):
        image += data+b'\0'*(-len(data)%page)
    target = out/('naso-'+a.mode+'.img')
    target.write_bytes(image)
    manifest = dict(mode=a.mode,size=len(image),sha256=sha(image),
        kernel_sha256=sha(kernel),dtb_sha256=sha(dtb),
        original_gzip_sha256=sha(original),ha_ip=ha,
        data_partition=a.data_partition if a.mode=='installed' else None,
        image_contains_new_private_key=True,
        hardware_tested=False,
        note='Built offline from verified components; this newly generated image must be RAM-tested on its target.')
    (out/(a.mode+'-manifest.json')).write_text(json.dumps(manifest,indent=2))
    print('Built', target, 'SHA256', sha(image))
    print('Private key retained in', keyfile, '(not printed). No device operation performed.')

if __name__ == '__main__':
    main()
