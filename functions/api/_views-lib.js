const REPORT_PATH=/^\/reports\/(morning|asia-close)\/(?!sample)[0-9]{4}-[0-9]{2}-[0-9]{2}\.html$/;
export function json(data,status=200,extra={}){return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store',...extra}})}
export function validPath(path){return typeof path==='string'&&path.length<160&&REPORT_PATH.test(path)}
export function sameOrigin(request){const origin=request.headers.get('origin');return !origin||origin===new URL(request.url).origin}
export function isProduction(request){const host=new URL(request.url).hostname;return !['localhost','127.0.0.1'].includes(host)&&!host.endsWith('.pages.dev')?true:host.endsWith('.pages.dev')&&!host.includes('-')}
export function isBot(request){return /bot|crawler|spider|preview|headless|lighthouse/i.test(request.headers.get('user-agent')||'')}
export async function readJson(request,limit=4096){const len=Number(request.headers.get('content-length')||0);if(len>limit)throw new Error('body_too_large');const raw=await request.text();if(raw.length>limit)throw new Error('body_too_large');return JSON.parse(raw||'{}')}
