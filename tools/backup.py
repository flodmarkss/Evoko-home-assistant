"""Read-only original eMMC backup via private LAN control. No device writes."""
import argparse, hashlib, json, re
from pathlib import Path
from control_client import execute

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','serial','cid','device'):p.add_argument('--'+name,required=True)
    p.add_argument('--key-file',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.serial):p.error('Unexpected serial')
    if not re.fullmatch(r'[0-9a-fA-F]{32}',a.cid):p.error('CID must be 32 hex digits')
    if not re.fullmatch(r'mmcblk[0-9]+',a.device):p.error('Expected whole eMMC basename')
    def run(script,timeout=60):
        with execute(a.host,a.key_file,'set -e\nB=/bin/busybox\n'+script,timeout) as r:return r.read().decode()
    def identity():
        s=run('$B cat /proc/cmdline\n$B cat /sys/block/'+a.device+'/device/cid\necho ID_OK\n')
        if 'androidboot.serialno='+a.serial not in s.split() or a.cid.lower() not in s.lower().split() or 'ID_OK' not in s.split():raise RuntimeError('Identity mismatch')
        # Any mounted partition of the chosen eMMC is refused, even read-only.
        mounts=run('$B cat /proc/mounts\necho MOUNTS_OK\n')
        if 'MOUNTS_OK' not in mounts:raise RuntimeError('No mount inventory')
        if re.search(r'^/dev/'+re.escape(a.device)+r'(p[0-9]+)?\s',mounts,re.M):raise RuntimeError('Selected eMMC is mounted; use a RAM-only rescue boot')
    identity();a.out.mkdir(parents=True,exist_ok=False)
    records=[]
    for dev in (a.device,a.device+'boot0',a.device+'boot1'):
        identity()
        size_text=run('$B cat /sys/block/'+dev+'/size\necho SIZE_OK\n')
        parts=size_text.split()
        if len(parts)!=2 or parts[-1]!='SIZE_OK' or not parts[0].isdigit():raise RuntimeError('Invalid device size')
        size=int(parts[0])*512
        if size<=0:raise RuntimeError('Empty block device')
        def source_sha():
            text=run('$B sha256sum /dev/'+dev+'\necho HASH_OK\n',3600)
            x=text.split()
            if len(x)!=3 or x[1]!='/dev/'+dev or x[2]!='HASH_OK' or not re.fullmatch('[0-9a-f]{64}',x[0]):raise RuntimeError('Source hash failed')
            return x[0]
        before=source_sha();temp=a.out/(dev+'.img.partial');digest=hashlib.sha256();received=0
        with execute(a.host,a.key_file,'/bin/busybox dd if=/dev/'+dev+' bs=1048576 2>/dev/null\n',3600) as r, temp.open('xb') as f:
            while data:=r.read(1024*1024):f.write(data);digest.update(data);received+=len(data)
        after=source_sha();identity()
        if received!=size or digest.hexdigest()!=before or after!=before:raise RuntimeError('Backup verification failed; partial preserved')
        target=a.out/(dev+'.img');temp.rename(target)
        records.append(dict(device=dev,bytes=size,source_sha256_before=before,source_sha256_after=after,local_sha256=digest.hexdigest(),verified=True))
        (a.out/'verification.json').write_text(json.dumps(dict(serial=a.serial,cid=a.cid,areas=records,all_three_areas_verified=len(records)==3),indent=2))
        print('Verified',dev,size,'bytes')
    print('All three source/local hashes match. Keep this backup private and duplicate it.')

if __name__=='__main__':main()
