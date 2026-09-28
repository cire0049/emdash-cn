const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm');
const patches=require('../translations/scoped.json');
test('quit warning retains local and remote session impact and incomplete-count caution',()=>{
 const p=patches.find(x=>x.before.startsWith('function describeShutdownImpact('));const ctx={};vm.runInNewContext(p.after+';globalThis.describe=describeShutdownImpact',ctx);
 assert.equal(ctx.describe({acpSessions:0,localTuiSessions:0,terminals:0,remoteSessions:0,incomplete:false}),'后台服务和自动化将停止。');
 assert.equal(ctx.describe({acpSessions:1,localTuiSessions:2,terminals:1,remoteSessions:2,incomplete:true}),'至少 3 个正在运行的代理会话和1 个终端可能会停止。 至少 2 个远程会话将继续运行。');
});
test('1.2.7 update captions preserve error and normal branches and interpolation',()=>{
 const next=require('../translations/scoped-1.2.7.json');
 assert.equal(new Set(next.map(p=>p.before)).size,next.length);
 const title=next.find(p=>p.before.startsWith('return i ? "Could not check'));
 const detail=next.find(p=>p.before.startsWith('return i ? `Current'));
 for(const failed of [false,true]){
  const ctx={i:failed,a2:'Emdash',e2:'1.2.7'};
  vm.runInNewContext('globalThis.title=(()=>{'+title.after+'})();globalThis.detail=(()=>{'+detail.after+'})();',ctx);
  assert.equal(ctx.title,failed?'无法检查更新':'已是最新版本');
  assert.equal(ctx.detail,failed?'当前 Emdash 版本 v1.2.7':'当前 Emdash 版本 v1.2.7 已是最新版本');
 }
});
