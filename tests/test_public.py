import importlib.util
import subprocess
import sys
import tempfile
import unittest
import contextlib
import hashlib
import io
import re
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class PublicDistributionTests(unittest.TestCase):
    def test_ram_upload_preserves_new_target_marker(self):
        sys.path.insert(0,str(ROOT/'tools'))
        spec=importlib.util.spec_from_file_location('ram_upload_under_test',ROOT/'tools/upload_ram_file.py')
        upload=importlib.util.module_from_spec(spec);spec.loader.exec_module(upload)
        calls=[]
        with tempfile.TemporaryDirectory() as tmp:
            helper=Path(tmp)/'test-helper';helper.write_bytes(b'harmless RAM helper')
            digest=hashlib.sha256(helper.read_bytes()).hexdigest()
            @contextlib.contextmanager
            def transport(host,key,script,timeout=60):
                calls.append(script)
                if 'cat /proc/cmdline' in script:data=b'androidboot.serialno=TEST_PANEL\n'
                elif 'else echo' in script:
                    # Simulate the shell's actual marker, not an assumed response.
                    data=(re.search(r'else echo ([^;]+);',script).group(1)+'\n').encode()
                elif 'sha256sum /tmp/naso-bootstrap/test-helper' in script:data=(digest+'  /tmp/naso-bootstrap/test-helper\n').encode()
                else:data=b''
                yield io.BytesIO(data)
            args=['upload_ram_file.py','--host','192.0.2.2','--key-file','unused-private-key','--serial','TEST_PANEL','--file',str(helper)]
            with patch.object(upload,'execute',transport),patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()):upload.main()
        self.assertTrue(any('base64 -d >> /tmp/naso-bootstrap/test-helper' in s for s in calls))

    def test_no_session_or_key_files(self):
        forbidden={'cookies.sqlite','logins.json','key4.db','cert9.db','webappsstore.sqlite','control-key.txt','backup-key.txt','naso.conf'}
        for p in ROOT.rglob('*'):
            if any(x in p.parts for x in ('.git','__pycache__','private-build','vendor')):continue
            self.assertNotIn(p.name,forbidden,str(p))
        prefs=(ROOT/'assets/firefox-user.js').read_text()
        self.assertNotIn('authToken',prefs)
        self.assertNotIn('192.168.',(ROOT/'sources/ha-proxy.c').read_text())

    def test_builder_has_no_default_ha(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/build_images.py'),'--zig','missing','--out','missing'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('--ha-ip',p.stderr)

    def test_existing_profile_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);(r/'usr/bin').mkdir(parents=True);(r/'usr/bin/firefox-esr').touch()
            profile=r/'var/lib/naso/firefox';profile.mkdir(parents=True)
            private=profile/'cookies.sqlite';private.write_bytes(b'FAKE SESSION DATA')
            p=subprocess.run([sys.executable,str(ROOT/'tools/prepare_root.py'),'--root',str(r),'--build',str(r/'build')],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('Existing profile',p.stderr)
            self.assertEqual(private.read_bytes(),b'FAKE SESSION DATA')

    def test_fresh_profile_contains_preferences_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)/'root';(r/'usr/bin').mkdir(parents=True);(r/'usr/bin/firefox-esr').touch()
            (r/'usr/local/sbin').mkdir(parents=True)
            profile=r/'var/lib/naso/firefox';profile.mkdir(parents=True)
            (profile/'user.js').write_bytes((ROOT/'assets/firefox-user.js').read_bytes())
            build=Path(tmp)/'build';build.mkdir();(build/'ha-proxy-arm').write_bytes(b'TEST ONLY')
            p=subprocess.run([sys.executable,str(ROOT/'tools/prepare_root.py'),'--root',str(r),'--build',str(build)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual({x.name for x in profile.iterdir()},{'user.js'})
            self.assertFalse((r/'etc/wpa_supplicant/naso.conf').exists())

if __name__=='__main__':unittest.main()
