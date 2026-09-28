// Only translate literal display expressions. Never traverse conditions or event handlers as text.
const acorn = require('/usr/share/nodejs/acorn');
const displayProperties = new Set(['children','label','title','description','placeholder','aria-label','tooltip','emptyMessage','confirmLabel','cancelLabel','message','text','buttonLabel','loadingText','emptyText','searchPlaceholder','detail','subtitle','hint','defaultLabel']);
const displayConstants=new Set(['STATUS_LABELS','SOURCE_LABELS','CREDENTIAL_SOURCE_LABELS','KIND_LABELS','STAGE_LABELS','MONTH_LABELS','WEEKDAY_LABELS','PERIOD_LABELS','PROGRESS_LABELS','CREATION_STAGE_LABELS','UNREGISTERED_STAGE_LABEL','ISSUE_FEATURE_LABELS','REVEAL_LABEL','vr','Cd2','mergeLabels','mergeDescriptions','bypassMergeLabels','bypassMergeDescriptions']);
const displayFunctions=new Set(['provenanceBadgeLabel','provenanceSourceText','brokenSettingText','fieldLabel','projectConfigWriteFieldLabel','runtimeStatusLabel','scriptIssueLabel','formatRunTriggerKindLabel','provenanceLabel','authLabel','stateLabel','checkoutDriftLabel','previewServerStatusLabel']);
function translate(source, dictionary) {
 const ast=acorn.parse(source,{ecmaVersion:'latest',sourceType:'module'}), edits=new Map(), candidates=[];
 function display(node,context) {
  if(!node)return;
  if(node.type==='Literal' && typeof node.value==='string') {
   candidates.push({text:node.value,start:node.start,end:node.end,context});
   if(Object.hasOwn(dictionary,node.value))edits.set(node.start,{start:node.start,end:node.end,text:JSON.stringify(context === "defaultLabel" && node.value === "on" ? "开" : dictionary[node.value]),original:node.value,context});
  } else if(node.type==='TemplateLiteral') {
   let key=node.quasis.map((q,i)=>(q.value.cooked??q.value.raw)+(i<node.expressions.length?`{${i}}`:'')).join('');
   candidates.push({text:key,start:node.start,end:node.end,context});
   if(Object.hasOwn(dictionary,key)) {
    const translated=dictionary[key];const indexes=[...translated.matchAll(/\{(\d+)\}/g)].map(m=>Number(m[1]));
    if(indexes.length!==node.expressions.length||indexes.some((x,i)=>x!==i))throw Error('Interpolation order changed: '+key);
    const parts=translated.split(/(\{\d+\})/).filter(Boolean).map(p=>/^\{\d+\}$/.test(p)?'('+source.slice(node.expressions[Number(p.slice(1,-1))].start,node.expressions[Number(p.slice(1,-1))].end)+')':JSON.stringify(p));
    edits.set(node.start,{start:node.start,end:node.end,text:'("" + '+parts.join(' + ')+')',original:key,context});
   }
  } else if(node.type==='ConditionalExpression') {display(node.consequent,context);display(node.alternate,context);}
  else if(node.type==='LogicalExpression')display(node.right,context);
  else if(node.type==='ArrayExpression')node.elements.forEach(e=>display(e,context));
 }
 function walk(node, displayReturn=false) {
  if(!node||!node.type)return;
  if(/Function/.test(node.type))displayReturn=displayFunctions.has(node.id?.name);
  if(displayReturn && node.type==='ReturnStatement')display(node.argument,'caption-return');
  if(node.type==='VariableDeclarator' && displayConstants.has(node.id.name)) {
   if(node.init?.type==='ObjectExpression')node.init.properties.forEach(p=>display(p.value,'caption-map'));
   else display(node.init,'caption-constant');
  }
  if(node.type==='Property'&&displayProperties.has(node.key.name||node.key.value))display(node.value,node.key.name||node.key.value);
  if(node.type==='CallExpression'&&node.callee.type==='MemberExpression'&&(/^(?:toast|Re\$2$)/.test(node.callee.object.name||''))&&['error','success','info','warning'].includes(node.callee.property.name))display(node.arguments[0],'toast');
  for(const v of Object.values(node))if(Array.isArray(v))v.forEach(c=>walk(c,displayReturn));else if(v&&typeof v==='object')walk(v,displayReturn);
 }
 walk(ast);const sorted=[...edits.values()].sort((a,b)=>a.start-b.start);let boundary=0;const parts=[];
 for(const e of sorted){if(e.start<boundary)throw Error('Overlapping translation');parts.push(source.slice(boundary,e.start),e.text);boundary=e.end;}parts.push(source.slice(boundary));const code=parts.join('');
 acorn.parse(code,{ecmaVersion:'latest',sourceType:'module'});
 return {code,edits:sorted,candidates};
}
module.exports={translate};
