/* Public application assets only. Never intercept/cache APIs, health, credentials or writes. */
const CACHE='growth-public-shell-v1';
const publicAsset=url=>url.origin===self.location.origin&&(
 url.pathname==='/'||url.pathname==='/index.html'||url.pathname.startsWith('/assets/')||
 ['/icon.svg','/icon-192.png','/icon-512.png','/manifest.webmanifest'].includes(url.pathname));
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const response=await fetch('/index.html',{cache:'reload'});
 if(!response.ok)throw new Error('Public shell unavailable');
 const html=await response.clone().text();
 const assets=[...html.matchAll(/(?:src|href)="([^"]+)"/g)].map(match=>new URL(match[1],self.location.origin))
  .filter(url=>publicAsset(url)&&url.pathname.startsWith('/assets/')).map(url=>url.href);
 const cache=await caches.open(CACHE);
 await cache.put('/index.html',response);
 await cache.addAll(['/icon.svg','/manifest.webmanifest',...assets]);
 await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 for(const key of await caches.keys())if(key.startsWith('growth-public-shell-')&&key!==CACHE)await caches.delete(key);
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||request.headers.has('Authorization')||!publicAsset(url))return;
 if(request.mode==='navigate'){
  event.respondWith((async()=>{
   try{
    const response=await fetch(request);
    if(response.ok){const cache=await caches.open(CACHE);await cache.put('/index.html',response.clone());}
    return response;
   }catch{
    return await caches.match('/index.html')||Response.error();
   }
  })());return;
 }
 event.respondWith((async()=>{
  const cache=await caches.open(CACHE),hit=await cache.match(request);
  if(hit)return hit;
  const response=await fetch(request);
  if(response.ok){
   await cache.put(request,response.clone());
   const keys=await cache.keys();
   // Bound obsolete hashed assets while preserving the navigation fallback.
   const old=keys.filter(key=>new URL(key.url).pathname.startsWith('/assets/'));
   for(const key of old.slice(0,Math.max(0,old.length-64)))await cache.delete(key);
  }
  return response;
 })());
});
