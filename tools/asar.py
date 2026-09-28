"""Read and rewrite ASAR while preserving unpacked files, links and integrity metadata."""
import hashlib,json,struct,pathlib,copy
class Archive:
 def __init__(self,path):
  self.path=pathlib.Path(path)
  with self.path.open('rb') as f:
   sizes=struct.unpack('<4I',f.read(16));self.base=8+sizes[1];self.header=json.loads(f.read(sizes[3]))
 def entries(self,tree=None,prefix=''):
  for name,entry in (tree or self.header)['files'].items():
   path=prefix+name
   if 'files' in entry:yield from self.entries(entry,path+'/')
   else:yield path,entry
 def read(self,entry):
  if entry.get('unpacked') or 'link' in entry:raise ValueError('Not an inline file')
  with self.path.open('rb') as f:
   f.seek(self.base+int(entry['offset']));return f.read(entry['size'])
 def rewrite(self,destination,replacements):
  destination=pathlib.Path(destination)
  if destination.resolve()==self.path.resolve() or (destination.exists() and destination.samefile(self.path)):
   raise ValueError('Refusing to overwrite source archive')
  header=copy.deepcopy(self.header);offset=0;payload=[]
  for name,entry in self.entries(header):
   if entry.get('unpacked') or 'link' in entry:continue
   original_offset=int(entry['offset']);original_size=entry['size'];data=replacements.get(name)
   if data is not None:
    entry['size']=len(data)
    if 'integrity' in entry:
     block=entry['integrity'].get('blockSize',4194304)
     entry['integrity']={'algorithm':'SHA256','hash':hashlib.sha256(data).hexdigest(),'blockSize':block,'blocks':[hashlib.sha256(data[i:i+block]).hexdigest() for i in range(0,max(1,len(data)),block)]}
   entry['offset']=str(offset);offset+=entry['size'];payload.append((original_offset,original_size,data))
  raw=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode();padding=(-len(raw))%4
  header_payload=struct.pack('<I',len(raw))+raw+b'\0'*padding
  header_pickle=struct.pack('<I',len(header_payload))+header_payload
  with open(destination,'wb') as out,self.path.open('rb') as original:
   out.write(struct.pack('<II',4,len(header_pickle)));out.write(header_pickle)
   for start,size,data in payload:
    if data is not None:out.write(data);continue
    original.seek(self.base+start)
    while size:
     chunk=original.read(min(size,1024*1024))
     if not chunk:raise EOFError('Truncated archive')
     out.write(chunk);size-=len(chunk)
