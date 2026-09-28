const {test}=require('node:test');const assert=require('node:assert/strict');const vm=require('node:vm');const fs=require('node:fs');
const patch=fs.existsSync(require('node:path').join(__dirname,'../tools/translate.cjs'))?require('../tools/translate.cjs').translate:(s)=>s;
const dict={'Settings':'设置','Delete':'删除','Working…':'处理中…','Ready':'就绪','Remove {0}?':'删除 {0}？'};
test('translates display values but preserves identifiers, comparisons, user content and handlers',()=>{
 const source='const state="Ready"; const user="Settings"; globalThis.out={id:"Settings", label:"Settings", children: state === "Ready" ? "Delete" : "Working…", onClick:()=>"Delete", value:user};';
 const ctx={};vm.runInNewContext(patch(source,dict).code??source,ctx);assert.equal(ctx.out.label,'设置');assert.equal(ctx.out.children,'删除');assert.equal(ctx.out.id,'Settings');assert.equal(ctx.out.value,'Settings');assert.equal(ctx.out.onClick(),'Delete');
});
test('preserves template interpolation and hostile user text',()=>{
 const source='const name="${secret} ` Settings"; globalThis.out={title:`Remove ${name}?`};';const ctx={};vm.runInNewContext(patch(source,dict).code??source,ctx);assert.equal(ctx.out.title,'删除 ${secret} ` Settings？');
});
test('translates known status captions without changing status keys or unrelated functions',()=>{
 const source='const STATUS_LABELS={connected:"Ready"};function stateLabel(state){switch(state){case "ready":return "Ready";default:return state;}}function business(){return "Ready";}globalThis.out=[STATUS_LABELS.connected,stateLabel("ready"),stateLabel("Custom"),business()];';
 const ctx={};vm.runInNewContext(patch(source,dict).code??source,ctx);assert.deepEqual(Array.from(ctx.out),['就绪','就绪','Custom','Ready']);
});
