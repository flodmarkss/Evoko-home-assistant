import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class PublicDistributionTests(unittest.TestCase):
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
