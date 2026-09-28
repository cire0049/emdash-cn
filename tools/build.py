#!/usr/bin/env python3
"""Build a version-pinned local Chinese AppImage without modifying the original."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tempfile
from asar import Archive
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE_SHA='0542de761fe7713847ba713d30cc95e692778d90a7fc732e121e64188c11e0c8'
SUPPORTED_BUILDS={
 SOURCE_SHA: {'version':'1.2.5','renderer':'out/renderer/assets/index-1QfyQ0T0.js'},
 'eb8db9cc3f912b51dce05860098bed71e85ba622380538d6a507f7c567ca1732': {'version':'1.2.6','renderer':'out/renderer/assets/index-BVIXIuEj.js'},
 '595bb9be13f2d29e858e78a16ea8dc91cbc1db33d9c592b94ea7808e0e396594': {'version':'1.2.7','renderer':'out/renderer/assets/index-C92ugmnG.js','scoped':'scoped-1.2.7.json'}
}
DEFAULT_SOURCE=pathlib.Path.home()/'.local/share/emdash-app/Emdash-1.2.7.AppImage'
def sha(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args):subprocess.run([str(a) for a in args],check=True)
def build(source,output):
 source=source.resolve();output=output.absolute()
 if output.exists():raise ValueError('Output already exists; choose a new output path')
 source_sha=sha(source);spec=SUPPORTED_BUILDS.get(source_sha)
 if spec is None:raise ValueError('Source is not a reviewed Emdash build; refusing to patch')
 output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='emdash-cn-build-',dir='/tmp') as td:
  work=pathlib.Path(td);app=work/'app';raw=work/'original-js';patches=work/'patches'
  offset=int(subprocess.check_output([str(source),'--appimage-offset'],text=True).strip())
  run('unsquashfs','-no-progress','-d',app,'-o',offset,source)
  archive=Archive(app/'resources/app.asar')
  entries=dict(archive.entries())
  if json.loads(archive.read(entries['package.json']))['version']!=spec['version']:raise ValueError('Incorrect version')
  for name,entry in entries.items():
   if name.startswith('out/') and name.endswith(('.js','.html')) and ('/assets/' not in name or pathlib.Path(name).name.startswith('index-')):
    dest=raw/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.read(entry))
  run('node',ROOT/'tools/apply.cjs',raw,patches,spec['renderer'],spec.get('scoped','scoped.json'))
  report=json.loads((patches/'report.json').read_text())
  replacements={e['file']:(patches/e['file']).read_bytes() for e in report}
  new_asar=work/'localized.asar';archive.rewrite(new_asar,replacements)
  rewritten=Archive(new_asar);new_entries=dict(rewritten.entries());verified=0
  for name,entry in entries.items():
   if 'offset' not in entry:
    if entry!=new_entries[name]:raise ValueError('Unpacked metadata changed: '+name)
    continue
   data=rewritten.read(new_entries[name]);expected=replacements.get(name)
   if expected is None:expected=archive.read(entry)
   if data!=expected:raise ValueError('Unexpected archive modification: '+name)
   integrity=new_entries[name].get('integrity')
   if integrity and hashlib.sha256(data).hexdigest()!=integrity['hash']:raise ValueError('Bad integrity: '+name)
   verified+=1
  os.replace(new_asar,app/'resources/app.asar')
  squash=work/'payload.squashfs'
  run('mksquashfs',app,squash,'-noappend','-comp','gzip','-all-root','-processors','4','-no-progress')
  # Build to a sibling temp file then atomically publish the completed artifact.
  with tempfile.NamedTemporaryFile(prefix=output.name+'.',dir=output.parent,delete=False) as f:
   staged=pathlib.Path(f.name)
   try:
    with source.open('rb') as original:f.write(original.read(offset))
    with squash.open('rb') as image:shutil.copyfileobj(image,f)
    f.flush();os.fsync(f.fileno())
   except BaseException:
    staged.unlink(missing_ok=True);raise
  staged.chmod(0o755)
  # Destination must still be absent; link prevents overwriting concurrently created files.
  try:os.link(staged,output)
  finally:staged.unlink(missing_ok=True)
  manifest={'source':str(source),'sourceSha256':source_sha,'output':str(output),'outputSha256':sha(output),'version':spec['version'],'locale':'zh-CN','verifiedPackedFiles':verified,'files':report}
  (ROOT/'verification').mkdir(exist_ok=True)
  (ROOT/'verification/build.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,default=DEFAULT_SOURCE);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();build(args.source,args.output)
