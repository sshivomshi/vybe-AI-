import {chromium} from '@playwright/test';
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage();
await page.route('**/api/**',route=>{const u=new URL(route.request().url());route.fulfill({json:u.pathname.endsWith('/settings')?{preferences:{}}:u.pathname.endsWith('/status')?{connection:'OFFLINE'}:u.pathname.endsWith('/sync')?{operations:[],conflicts:[]}:[]});});
for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
 await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:5173');await page.getByRole('heading',{name:'Where will your mind go?'}).waitFor();
 await page.screenshot({path:`test-results/space-${name}.png`,fullPage:true});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow '+name);
 await page.getByRole('button',{name:'Explain a topic'}).click();if(!await page.getByRole('textbox',{name:'Message',exact:true}).inputValue())throw Error('Starter failed');
}
await page.emulateMedia({reducedMotion:'reduce'});if(await page.locator('.orbit-light').evaluate(e=>getComputedStyle(e).animationName)!=='none')throw Error('Reduced motion failed');
await browser.close();console.log('PASS: desktop/mobile layout, prompt starter, reduced motion. API mocked for visual checks.');
