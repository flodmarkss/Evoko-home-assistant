"""Upload one helper file only below /tmp/naso-bootstrap; never to eMMC."""
import argparse
import base64
import hashlib
from pathlib import Path
import re
from control_client import execute

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',required=True)
    p.add_argument('--key-file',type=Path,required=True)
    p.add_argument('--serial',required=True)
    p.add_argument('--file',type=Path,required=True)
    a = p.parse_args()
    name = a.file.name
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',name) or not re.fullmatch(r'[A-Za-z0-9_-]+',a.serial):
        raise ValueError('Unexpected name/serial format')
    def run(script):
        with execute(a.host,a.key_file,script) as r:
            return r.read().decode(errors='replace')
    identity = run('/bin/busybox cat /proc/cmdline\n')
    if 'androidboot.serialno='+a.serial not in identity.split():
        raise RuntimeError('Identity mismatch; no upload')
    target = '/tmp/naso-bootstrap/'+name
    data = a.file.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data)>2*1024*1024:
        raise ValueError('Only small bootstrap helpers are allowed')
    state = run('''set -e
B=/bin/busybox
$B mkdir -p /tmp/naso-bootstrap
[ "$($B readlink -f /tmp/naso-bootstrap)" = /tmp/naso-bootstrap ]
[ ! -L TARGET ]
if [ -e TARGET ]; then $B sha256sum TARGET; else echo NEW_TARGET; fi
'''.replace('TARGET',target))
    if not state.startswith(digest):
        if 'NEW_TARGET' not in state:
            raise RuntimeError('Existing target differs; preserved')
        run(': > '+target+'\n')
        for i in range(0,len(data),32768):
            encoded = base64.b64encode(data[i:i+32768]).decode()
            run('/bin/busybox base64 -d >> '+target+" <<'DATA'\n"+encoded+'\nDATA\n')
        if not run('/bin/busybox sha256sum '+target+'\n').startswith(digest):
            raise RuntimeError('Upload hash mismatch; no execution performed')
    run('/bin/busybox chmod 700 '+target+'\n')
    print('Verified RAM helper',target,digest)

if __name__=='__main__':
    main()
