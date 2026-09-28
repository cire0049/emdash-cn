const fs=require('fs'),path=require('path');const {translate}=require('./translate.cjs');
const root=process.argv[2],out=process.argv[3],renderer=process.argv[4]??'out/renderer/assets/index-1QfyQ0T0.js',scoped=process.argv[5]??'scoped.json';
if(!fs.existsSync(path.join(root,renderer)))throw Error('Reviewed renderer not found');const dict=JSON.parse(fs.readFileSync(path.join(__dirname,'../translations/zh-CN.json'),'utf8'));const report=[];
if(fs.existsSync(out)&&fs.readdirSync(out).length)throw Error('Patch output must be empty');
fs.mkdirSync(out,{recursive:true});
function walk(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())walk(p);else if(p.endsWith('.js')){
 let source=fs.readFileSync(p,'utf8');let prepared=source;
 if(path.relative(root,p)===renderer)for(const patch of JSON.parse(fs.readFileSync(path.join(__dirname,'../translations',scoped),'utf8'))){const count=prepared.split(patch.before).length-1;if(count!==patch.count)throw Error('Scoped patch mismatch: '+patch.before.slice(0,100));prepared=prepared.replaceAll(patch.before,patch.after);}
 const r=translate(prepared,dict);let code=r.code;
 if(p.endsWith('/out/main/index.js'))code=code.replace('configureChromiumCommandLine({ commandLine: app.commandLine });','app.commandLine.appendSwitch("lang", "zh-CN");\nconfigureChromiumCommandLine({ commandLine: app.commandLine });');
 if(/\/menu-[^/]+\.js$/.test(p)){
  const labels={cut:'剪切',copy:'复制',paste:'粘贴',delete:'删除',selectAll:'全选',reload:'重新加载',forceReload:'强制重新加载',toggleDevTools:'切换开发者工具',resetZoom:'实际大小',zoomIn:'放大',zoomOut:'缩小',togglefullscreen:'切换全屏',windowMenu:'窗口'};
  for(const [role,label] of Object.entries(labels))code=code.replaceAll('{ role: '+JSON.stringify(role)+' }','{ role: '+JSON.stringify(role)+', label: '+JSON.stringify(label)+' }');
 }
 if(code!==source){const rel=path.relative(root,p),dest=path.join(out,rel);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,code);report.push({file:rel,edits:r.edits.length});}
 }}}
walk(root);const htmlPath='out/renderer/index.html';let html=fs.readFileSync(path.join(root,htmlPath),'utf8').replace('<html lang="en">','<html lang="zh-CN">').replace('Emdash is taking longer than expected to start.','Emdash 启动时间超出预期。').replace('Restart Emdash</button>','重启 Emdash</button>').replace('Open recovery</button>','打开恢复模式</button>');fs.mkdirSync(path.join(out,'out/renderer'),{recursive:true});fs.writeFileSync(path.join(out,htmlPath),html);report.push({file:htmlPath,edits:4});fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
