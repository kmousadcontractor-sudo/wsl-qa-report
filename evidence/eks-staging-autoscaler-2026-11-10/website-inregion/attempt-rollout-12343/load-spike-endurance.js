import http from 'k6/http';
import {check,group,sleep} from 'k6';
import exec from 'k6/execution';
import encoding from 'k6/encoding';
const profile=__ENV.PROFILE||'smoke';
const allowed=new Set(['www.staging.worldsurfleague.com','staging.worldsurfleague.com']);
const origin='https://www.staging.worldsurfleague.com';
const results='/events/2026/ct/445/meo-rip-curl-pro-portugal/results';
const stages={
 smoke:[{target:1,duration:'30s'}],
 flows:[{target:1,duration:'1m'},{target:3,duration:'2m'},{target:1,duration:'1m'}],
 spike:[{target:1,duration:'1m'},{target:20,duration:'10s'},{target:20,duration:'30s'},{target:1,duration:'10s'},{target:1,duration:'2m'}],
 endurance:[{target:2,duration:'1m'},{target:2,duration:'15m'},{target:0,duration:'1m'}],
};
if(!stages[profile])throw new Error('Use smoke, flows, spike or endurance');
export const options={scenarios:{public_browse:{executor:'ramping-arrival-rate',startRate:1,timeUnit:'1s',preAllocatedVUs:10,maxVUs:100,stages:stages[profile],gracefulStop:'10s'}},thresholds:{http_req_failed:[{threshold:'rate<0.02',abortOnFail:true,delayAbortEval:'30s'}],http_req_duration:[{threshold:'p(95)<5000'},{threshold:'p(95)<8000',abortOnFail:true,delayAbortEval:'30s'}],checks:[{threshold:'rate>0.98',abortOnFail:true,delayAbortEval:'30s'}],dropped_iterations:[{threshold:'count<20',abortOnFail:true,delayAbortEval:'30s'}]},tags:{target:'legacy-staging-website',profile},discardResponseBodies:true};
function read(path,step,full=false){
 if(!__ENV.LEGACY_BASIC_USER||!__ENV.LEGACY_BASIC_PASSWORD)exec.test.abort('Missing legacy staging HTTP Basic credentials');
 let url=origin+path;let response;
 for(let i=0;i<4;i++){
  const host=/^https:\/\/([^/]+)/.exec(url)?.[1];if(!allowed.has(host))exec.test.abort('Redirect left the authorized staging hosts');
  response=http.get(url,{headers:{Authorization:'Basic '+encoding.b64encode(__ENV.LEGACY_BASIC_USER+':'+__ENV.LEGACY_BASIC_PASSWORD),'User-Agent':'WSL-QA-k6-staging-autoscaler'},redirects:0,responseType:full?'text':'none',timeout:'10s',tags:{name:step,flow:full?'preflight':'public-browse'}});
  if(response.status===401||response.status===403)exec.test.abort('Staging website access denied; no further load');
  if(response.status>=300&&response.status<400){const location=response.headers.Location;if(!location)exec.test.abort('Redirect missing Location');url=location.startsWith('/')?'https://'+host+location:location;continue;}
  if(response.status!==200)console.warn(JSON.stringify({step,status:response.status,error:response.error,errorCode:response.error_code,url:response.url}));return response;
 }
 exec.test.abort('Too many staging redirects');
}
export function setup(){for(const [path,step]of [['/','homepage'],[results,'event-results']]){const r=read(path,'preflight-'+step,true);if(r.status!==200||!/<html|<!doctype/i.test(r.body||''))exec.test.abort('Smoke prerequisite failed for '+step+': HTTP '+r.status);}return {verified:true};}
export default function(){
 group(__ITER%5===0?'Returning visitor: event results':'Visitor: home to event results',()=>{
  if(__ITER%5!==0){const r=read('/','homepage');check(r,{'homepage HTTP 200':r=>r.status===200});sleep(0.2);}
  const r=read(results,'event-results');check(r,{'event results HTTP 200':r=>r.status===200});
 });
}
export function handleSummary(data){if(__ENV.SUMMARY_STDOUT==='true')return {stdout:'WSL_QA_SUMMARY '+JSON.stringify({metrics:data.metrics,root_group:data.root_group})+'\n'};return {[__ENV.SUMMARY_PATH||'legacy-website-summary.json']:JSON.stringify(data,null,2)};}
