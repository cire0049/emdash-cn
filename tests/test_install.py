import unittest,tempfile,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from install import switch
class InstallTest(unittest.TestCase):
 def test_round_trip_preserves_original_and_other_launchers(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);original=root/'original';localized=root/'localized';other=root/'other';link=root/'emdash'
   for p in (original,localized,other):p.write_text(p.name)
   link.symlink_to(original);switch(link,original,localized);self.assertEqual(link.resolve(),localized);self.assertEqual(original.read_text(),'original')
   switch(link,localized,original);self.assertEqual(link.resolve(),original)
   link.unlink();link.symlink_to(other)
   with self.assertRaises(ValueError):switch(link,original,localized)
   self.assertEqual(link.resolve(),other)
if __name__=='__main__':unittest.main()

class RestoreAfterRebuildTest(unittest.TestCase):
 def test_restore_uses_installed_version_not_uninstalled_build(self):
  import json,hashlib
  from unittest.mock import patch
  import install
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);(root/'verification').mkdir();original=root/'original';a=root/'A';b=root/'B';link=root/'emdash'
   for p in (original,a,b):p.write_text(p.name)
   link.symlink_to(a)
   (root/'verification/build.json').write_text(json.dumps({'source':str(original),'output':str(b),'outputSha256':hashlib.sha256(b.read_bytes()).hexdigest()}))
   (root/'verification/installation.json').write_text(json.dumps({'original':str(original),'localized':str(a),'active':str(a)}))
   with patch.object(install,'ROOT',root),patch.object(install,'LAUNCHER',link),patch.object(install,'SOURCE_SHA',hashlib.sha256(original.read_bytes()).hexdigest()),patch.object(sys,'argv',['install.py','--restore']):install.main()
   self.assertEqual(link.resolve(),original)

class UpdateInstallTest(unittest.TestCase):
 def test_updated_binary_is_backed_up_and_broken_old_link_repaired(self):
  import json,hashlib
  from unittest.mock import patch
  import install
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);(root/'verification').mkdir();official=root/'Emdash-1.2.6.AppImage';candidate=root/'candidate.AppImage';stable=root/'emdash-x86_64.AppImage';old=root/'deleted-1.2.5-zh.AppImage';link=root/'emdash'
   official.write_bytes(b'official126');stable.write_bytes(b'official126');candidate.write_bytes(b'chinese126');link.symlink_to(old)
   digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
   (root/'verification/build.json').write_text(json.dumps({'source':str(official),'sourceSha256':digest(official),'output':str(candidate),'outputSha256':digest(candidate),'version':'1.2.6'}))
   (root/'verification/installation.json').write_text(json.dumps({'original':str(root/'original125'),'localized':str(old),'active':str(old)}))
   with patch.object(install,'ROOT',root),patch.object(install,'LAUNCHER',link),patch.object(install,'SOURCE_SHA',digest(official)),patch.object(sys,'argv',['install.py']):install.main()
   self.assertEqual(link.resolve(),stable);self.assertEqual(stable.read_bytes(),b'chinese126');self.assertEqual(official.read_bytes(),b'official126')
   with patch.object(install,'ROOT',root),patch.object(install,'LAUNCHER',link),patch.object(install,'SOURCE_SHA','old-version-checksum'),patch.object(sys,'argv',['install.py','--restore']):install.main()
   self.assertEqual(link.resolve(),official)

class PublishSafetyTest(unittest.TestCase):
 def test_unknown_updated_binary_is_not_overwritten(self):
  import hashlib
  from install import publish
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);candidate=root/'cn';target=root/'emdash-x86_64.AppImage'
   candidate.write_bytes(b'known localized');target.write_bytes(b'new unknown update')
   with self.assertRaises(ValueError):publish(candidate,target,hashlib.sha256(candidate.read_bytes()).hexdigest(),{'reviewed-official-sha'})
   self.assertEqual(target.read_bytes(),b'new unknown update')
