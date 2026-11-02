const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {chromium}=require(path.resolve('frontend/node_modules/playwright'));

(async()=>{
 const root=path.resolve('frontend/dist');
 const server=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');
  if(url.pathname.startsWith('/v1/')||url.pathname.startsWith('/health/')){
   res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});
   return res.end(JSON.stringify({private:'test-only-private-marker'}));
  }
  const file=path.resolve(root,url.pathname==='/'?'index.html':'.'+url.pathname);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);return res.end();}
  const type={'.js':'text/javascript','.html':'text/html','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webmanifest':'application/manifest+json'}[path.extname(file)]||'application/octet-stream';
  res.writeHead(200,{'Content-Type':type,'Cache-Control':'no-cache'});res.end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 try{
  browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
  const context=await browser.newContext();const page=await context.newPage();
  const origin='http://127.0.0.1:'+server.address().port;
  await page.goto(origin);
  await page.evaluate(()=>navigator.serviceWorker.ready);
  await page.waitForFunction(()=>Boolean(navigator.serviceWorker.controller));
  await page.evaluate(async()=>{
   await fetch('/v1/private',{headers:{Authorization:'Bearer test-only-token'}});
   await fetch('/v1/private');await fetch('/health/ready');
   await fetch('/v1/write',{method:'POST',body:'test-only-body'});
  });
  const cached=await page.evaluate(async()=>{
   const names=await caches.keys();return (await Promise.all(names.map(async name=>{
    const cache=await caches.open(name);return (await cache.keys()).map(request=>request.url);
   }))).flat();
  });
  assert(cached.some(url=>url.endsWith('/index.html')));
  assert(!cached.some(url=>url.includes('/v1/')||url.includes('/health/')));
  await context.setOffline(true);await page.reload();
  await page.getByText('You’re offline.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'Explore design preview',exact:true}).click();
  await page.locator('.design-preview-content').waitFor();
  assert.equal(await page.locator('#session').count(),0);
  console.log('PASS: real HTTP service-worker install/control; public assets cached; authenticated/public API responses and writes excluded; offline reload and isolated design preview work.');
 }finally{
  if(browser)await browser.close();
  await new Promise(resolve=>server.close(resolve));
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
