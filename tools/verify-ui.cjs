// Run only against the isolated smoke-test instance on localhost:19325.
const {connect}=require('./cdp.cjs');const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const output=path.join(__dirname,'../verification');
(async()=>{
 const c=await connect();const checks=[];
 const evaluate=async expression=>{const r=await c.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value;};
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const click=async name=>{assert(await evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()===${JSON.stringify(name)}||x.getAttribute('aria-label')===${JSON.stringify(name)});if(!b)return false;b.click();return true})()`),'Button missing: '+name);await wait(200);};
 const expect=async text=>{for(let i=0;i<30;i++){if((await evaluate('document.body.innerText')).includes(text)){checks.push(text);return;}await wait(100);}throw Error('UI text missing: '+text)};
 const shot=async name=>{await evaluate('document.querySelectorAll("*").forEach(x=>{if(x.scrollTop)x.scrollTop=0})');await wait(100);const r=await c.send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(output,name),Buffer.from(r.data,'base64'));};
 const enter=async(placeholder,text)=>{assert(await evaluate(`(()=>{const el=[...document.querySelectorAll('input')].find(x=>x.placeholder===${JSON.stringify(placeholder)});if(!el)return false;el.focus();el.select();return true})()`),'Input missing');await c.send('Input.insertText',{text});await wait(200);};
 try{
  assert.equal(await evaluate('document.documentElement.lang'),'zh-CN');checks.push('document language zh-CN');
  await click('设置');
  for(const [name,description] of [['通用','管理账户、应用更新和任务偏好设置。'],['界面','在系统托盘显示 Emdash'],['仓库','配置仓库和分支设置。'],['浏览器','管理浏览器配置及其保存的登录状态。'],['集成','处理 GitHub 议题和拉取请求'],['代理','管理代理及模型配置。'],['MCP','将代理连接到外部数据源和工具'],['计算机','管理用于远程项目的可复用计算机连接。']]){await click(name);await expect(description);}
  await click('通用');await expect('已是最新版本');await expect('始终');
  await click('界面');await shot('settings-zh-CN.png');
  await enter('搜索设置','终端');await expect('终端字体');checks.push('Chinese settings search: terminal');
  await enter('搜索设置','系统托盘');await expect('在系统托盘显示 Emdash');checks.push('Chinese settings search: system tray');
  await enter('搜索设置','');await c.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8});await c.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8});
  await click('自动化');await expect('查找严重缺陷');await expect('补充测试覆盖');await shot('automations-zh-CN.png');
  await click('搜索');await enter('搜索任务、项目、操作…','设置');await expect('打开设置');checks.push('Chinese command palette search');
  await c.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await c.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await click('设置');await click('界面');
  const report={passed:true,checks,checkedAt:new Date().toISOString(),scope:'Isolated test profile; navigation, search and rendering. No paid agent runs, remote writes, or destructive Git actions.'};fs.writeFileSync(path.join(output,'ui-checks.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 } finally {c.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
