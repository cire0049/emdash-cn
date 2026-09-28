import unittest,tempfile,pathlib,struct,json,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from asar import Archive
class AsarTest(unittest.TestCase):
 def test_unicode_resize_keeps_neighbor_and_unpacked(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t)/'a.asar';q=pathlib.Path(t)/'b.asar'
   header={'files':{'first':{'offset':'0','size':5},'last':{'offset':'5','size':4},'native':{'size':9,'unpacked':True},'alias':{'link':'last'}}}
   j=json.dumps(header).encode();payload=struct.pack('<I',len(j))+j+b'\0'*((-len(j))%4);h=struct.pack('<I',len(payload))+payload
   p.write_bytes(struct.pack('<II',4,len(h))+h+b'hellotail')
   Archive(p).rewrite(q,{'first':'你好，世界'.encode()});a=Archive(q);e=dict(a.entries())
   self.assertEqual(a.read(e['first']).decode(),'你好，世界');self.assertEqual(a.read(e['last']),b'tail');self.assertTrue(e['native']['unpacked']);self.assertEqual(e['alias']['link'],'last');self.assertEqual(Archive(p).read(header['files']['first']),b'hello')
if __name__=='__main__':unittest.main()

class ArchiveSafetyTest(unittest.TestCase):
 def test_refuses_overwriting_source(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t)/'source.asar';raw=b'{"files":{}}';payload=struct.pack('<I',len(raw))+raw+b'\0'*((-len(raw))%4);h=struct.pack('<I',len(payload))+payload;original=struct.pack('<II',4,len(h))+h;p.write_bytes(original)
   a=Archive(p)
   with self.assertRaises(ValueError):a.rewrite(p,{})
   self.assertEqual(p.read_bytes(),original)
