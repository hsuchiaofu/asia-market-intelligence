import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {pathToFileURL} from 'node:url';

const root=path.resolve(import.meta.dirname,'..');

async function testSearchCounts(){
  const listeners={},count={value:null,error:false},result={innerHTML:''};
  const box={value:'',addEventListener:(name,fn)=>listeners.box=fn};
  const type={value:'',addEventListener:(name,fn)=>listeners.type=fn};
  const sort={value:'newest',addEventListener:(name,fn)=>listeners.sort=fn};
  const rows=[
    {id:'morning-2026-07-23',type:'morning',title:'全球新聞晨報',summary:'AI 市場',date:'2026-07-23'},
    {id:'asia-close-2026-07-22',type:'asia-close',title:'亞洲股市收盤報',summary:'亞洲市場',date:'2026-07-22'},
    {id:'morning-2026-07-22',type:'morning',title:'全球新聞晨報',summary:'利率市場',date:'2026-07-22'},
    {id:'asia-close-2026-07-21',type:'asia-close',title:'亞洲股市收盤報',summary:'半導體市場',date:'2026-07-21'}
  ];
  let domReady;
  const AMI={load:async()=>rows,typeName:t=>t==='morning'?'全球新聞晨報':'亞洲股市收盤報',updateCount:(n,e=false)=>{count.value=n;count.error=e},render:(items,el,msg)=>{el.items=items;el.emptyMessage=msg},loadViewCounts:()=>{}};
  const document={addEventListener:(name,fn)=>domReady=fn,querySelector:s=>({'[data-search]':box,'[data-search-results]':result,'[data-type-filter]':type,'[data-sort]':sort}[s])};
  vm.runInNewContext(await fs.readFile(path.join(root,'assets/js/search.js'),'utf8'),{document,AMI});
  await domReady();
  assert.equal(count.value,4,'初始數量應等於有效報告總數');
  box.value='利率';listeners.box();assert.equal(count.value,1,'搜尋後數量應即時更新');
  box.value='';type.value='asia-close';listeners.type();assert.equal(count.value,2,'類型篩選後數量應即時更新');
  type.value='';listeners.type();assert.equal(count.value,4,'清除搜尋與篩選後應恢復總數');
  box.value='不存在';listeners.box();assert.equal(count.value,0);assert.equal(result.emptyMessage,'沒有符合搜尋條件的報告');

  let failedReady;const failedResult={innerHTML:''};const failedAMI={...AMI,load:async()=>{throw new Error('load failed')}};
  const failedDocument={addEventListener:(name,fn)=>failedReady=fn,querySelector:s=>({'[data-search]':box,'[data-search-results]':failedResult,'[data-type-filter]':type,'[data-sort]':sort}[s])};
  vm.runInNewContext(await fs.readFile(path.join(root,'assets/js/search.js'),'utf8'),{document:failedDocument,AMI:failedAMI});
  await failedReady();assert.equal(count.error,true);assert.match(failedResult.innerHTML,/無法載入報告資料/);
}

async function testViewDedupAndFailure(){
  const source=await fs.readFile(path.join(root,'assets/js/views.js'),'utf8');
  async function run(lastValue,fetchImpl,pathname='/reports/morning/2026-07-23'){
    const el={textContent:'正文仍可閱讀'},storage=new Map(lastValue?[['ami-view:morning-2026-07-23',String(lastValue)]]:[]),calls=[];
    const context={document:{querySelector:()=>el},location:{pathname},Date,Number,encodeURIComponent,localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},fetch:async(...args)=>{calls.push(args);return fetchImpl(...args)}};
    vm.runInNewContext(source,context);await new Promise(resolve=>setTimeout(resolve,0));return{el,calls,storage};
  }
  const ok=()=>({ok:true,json:async()=>({views:12})});
  const first=await run(0,ok);assert.equal(first.calls[0][1].method,'POST','首次閱讀才增加次數');assert.equal(first.el.textContent,'閱讀 12 次');
  const recent=await run(Date.now()-60_000,ok);assert.match(recent.calls[0][0],/\/api\/views\?id=/);assert.equal(recent.calls[0][1].method,undefined,'24 小時內只取得數字，不增加');
  const failed=await run(0,async()=>{throw new Error('offline')});assert.equal(failed.el.textContent,'閱讀 — 次','API 失敗須安靜降級');
}

async function testApi(){
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'ami-api-'));await fs.mkdir(path.join(temp,'views'));
  for(const file of ['_views-lib.js','views.js'])await fs.copyFile(path.join(root,'functions/api',file),path.join(temp,file));
  await fs.copyFile(path.join(root,'functions/api/views/batch.js'),path.join(temp,'views/batch.js'));await fs.writeFile(path.join(temp,'package.json'),'\{"type":"module"\}');
  const api=await import(pathToFileURL(path.join(temp,'views.js'))+'?v=1');
  class DB{constructor(){this.rows=new Map()}prepare(sql){const db=this;return{args:[],bind(...args){this.args=args;return this},async all(){if(sql.startsWith('SELECT'))return{results:this.args.filter(k=>db.rows.has(k)).map(path=>({path,views:db.rows.get(path).views}))};return{results:[]}},async run(){const[id,,created]=this.args,current=db.rows.get(id);db.rows.set(id,{views:(current?.views||0)+1,created_at:current?.created_at||created});return{}},async first(){return null}}}}
  const db=new DB(),env={DB:db},headers={'content-type':'application/json','user-agent':'Mozilla/5.0'};
  let response=await api.onRequestGet({request:new Request('https://example.com/api/views?id=bad'),env});assert.equal(response.status,400,'不合法 id 必須拒絕');
  response=await api.onRequestPost({request:new Request('https://example.com/api/views',{method:'POST',headers,body:JSON.stringify({id:'morning-2026-07-23'})}),env});assert.equal(response.status,200);assert.equal((await response.json()).views,1,'POST 應增加閱讀次數');
  response=await api.onRequestGet({request:new Request('https://example.com/api/views?id=morning-2026-07-23'),env});assert.equal((await response.json()).views,1,'GET 應取得閱讀次數');
}

await testSearchCounts();await testViewDedupAndFailure();await testApi();console.log('Frontend and views API behavior tests passed');
