const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');

(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
   const req=route.request(),url=new URL(req.url());
   if(url.origin!=='http://foundation.test')return route.abort();
   if(url.pathname.startsWith('/v1/')){
    const result=JSON.parse(execFileSync(process.env.FOUNDATION_PYTHON,['scripts/foundation_browser_bridge.py'],{
     input:JSON.stringify({method:req.method(),path:url.pathname+url.search,headers:req.headers(),data:req.postDataJSON()}),
     encoding:'utf8',env:process.env
    }));
    return route.fulfill({status:result.status,contentType:'application/json',body:result.body});
   }
   const root=path.resolve('frontend/dist');
   const file=path.resolve(root,url.pathname==='/'?'index.html':'.'+url.pathname);
   if(!file.startsWith(root+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:'Not found'});
   const ext=path.extname(file);
   const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'}[ext]||'application/octet-stream';
   return route.fulfill({contentType:type,body:fs.readFileSync(file)});
  });
  await page.goto('http://foundation.test/');
  await page.locator('#session').fill('invalid-session');
  await page.getByRole('button',{name:'Open workspace',exact:true}).click();
  await page.getByRole('alert').waitFor();
  await page.locator('#session').fill(process.env.FOUNDATION_SESSION);
  await page.getByRole('button',{name:'Open workspace',exact:true}).click();
  await page.getByRole('button',{name:'End session',exact:true}).waitFor();
  await page.getByText('diagnostic.retry').count();
  await page.getByRole('button',{name:'Operations',exact:true}).click();
  await page.getByText('Cost threshold exceeded',{exact:true}).waitFor();
  assert.equal(await page.getByText('₹500.00',{exact:true}).count(),1);
  await page.getByRole('button',{name:'Home',exact:true}).click();
  await page.getByText('succeeded',{exact:false}).waitFor();
  await page.screenshot({path:'artifacts/foundation-desktop.png',fullPage:true});
  await page.getByRole('combobox',{name:'Language',exact:true}).selectOption('ta');
  await page.getByRole('button',{name:'முகப்பு',exact:true}).waitFor();
  assert.equal(await page.locator('html').getAttribute('lang'),'ta');
  await page.getByRole('combobox',{name:'மொழி',exact:true}).selectOption('hi');
  await page.getByRole('button',{name:'होम',exact:true}).waitFor();
  assert.equal(await page.locator('html').getAttribute('lang'),'hi');
  await page.getByRole('button',{name:'थीम बदलें',exact:true}).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.setViewportSize({width:360,height:800});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:'artifacts/foundation-mobile.png',fullPage:true});
  await page.getByRole('button',{name:'सत्र समाप्त करें',exact:true}).click();
  await page.locator('#session').waitFor();
  assert.deepEqual(errors,[]);
  console.log('PASS: real Flask handlers via controlled transport; invalid session; staff cost alert; en/ta/hi; theme; 360px; session revocation; no JS errors.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
