const REPORT_ID=/^(morning|asia-close)-(\d{4}-\d{2}-\d{2})$/;
const REPORT_PATH=/^\/reports\/(morning|asia-close)\/(\d{4}-\d{2}-\d{2})(?:\.html)?$/;
export function json(data,status=200,extra={}){return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store',...extra}})}
export function validId(id){return typeof id==='string'&&id.length<=40&&REPORT_ID.test(id)}
export function validPath(path){return typeof path==='string'&&path.length<=160&&REPORT_PATH.test(path)}
export function idFromPath(path){const match=typeof path==='string'&&path.match(REPORT_PATH);return match?`${match[1]}-${match[2]}`:null}
export function pathFromId(id){const match=typeof id==='string'&&id.match(REPORT_ID);return match?`/reports/${match[1]}/${match[2]}.html`:null}
export function normalizeIdentifier(value){if(validId(value))return value;if(validPath(value))return idFromPath(value);return null}
export function legacyKeys(id){return [id,pathFromId(id)]}
export function sameOrigin(request){const origin=request.headers.get('origin');return !origin||origin===new URL(request.url).origin}
export function isProduction(request){const host=new URL(request.url).hostname;if(host==='localhost'||host==='127.0.0.1'||host==='::1')return false;if(host.endsWith('.pages.dev'))return host.split('.').length===3;return true}
export function isBot(request){return /bot|crawler|spider|preview|headless|lighthouse/i.test(request.headers.get('user-agent')||'')}
export async function readJson(request,limit=4096){const len=Number(request.headers.get('content-length')||0);if(len>limit)throw new Error('body_too_large');const raw=await request.text();if(raw.length>limit)throw new Error('body_too_large');return JSON.parse(raw||'{}')}
export async function getViews(db,id){const [primary,legacy]=legacyKeys(id);const result=await db.prepare('SELECT path, views FROM page_views WHERE path IN (?, ?)').bind(primary,legacy).all();return (result.results||[]).reduce((sum,row)=>sum+Number(row.views||0),0)}
