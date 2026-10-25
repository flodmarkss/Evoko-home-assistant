"""Authenticated LAN transport; no device action until a script is supplied."""
import argparse
from contextlib import contextmanager
import http.client
from pathlib import Path
import sys

@contextmanager
def execute(host, key_file, script, timeout=60):
    data = script.encode()
    if not 0 < len(data) <= 65536:
        raise ValueError('Script must contain 1..65536 bytes')
    c = http.client.HTTPConnection(host,8089,timeout=timeout)
    try:
        c.request('POST','/run',body=data,headers={
            'X-Naso-Key':Path(key_file).read_text().strip(),
            'Content-Type':'text/plain', 'Connection':'close'})
        r = c.getresponse()
        if r.status != 200:
            raise RuntimeError('Control HTTP status '+str(r.status))
        yield r
    finally:
        c.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',required=True)
    p.add_argument('--key-file',type=Path,required=True)
    p.add_argument('--script',type=Path,required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--timeout',type=int,default=60)
    a = p.parse_args()
    with execute(a.host,a.key_file,a.script.read_text(encoding='utf-8-sig'),a.timeout) as r:
        if a.output:
            # Refuse overwriting an existing backup/output.
            with a.output.open('xb') as f:
                while b := r.read(1024*1024):
                    f.write(b)
        else:
            while b := r.read(65536):
                sys.stdout.buffer.write(b)

if __name__=='__main__':
    main()
