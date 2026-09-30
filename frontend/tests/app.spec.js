import {test,expect} from '@playwright/test';
test('real API memory create, semantic retrieval, edit, archive, restore and delete',async({page})=>{
  const title='Browser test '+Date.now();
  let createdId;
  try {
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'How can I help you?'})).toBeVisible();
  await page.getByRole('button',{name:'Saved memories',exact:false}).first().click();
  await page.getByRole('button',{name:'New memory'}).click();
  await page.getByLabel('Title',{exact:true}).fill(title);
  await page.getByLabel('Memory',{exact:true}).fill('Studying CNN: understands convolution and pooling, but needs revision of backpropagation. Session reference: '+title);
  await page.getByText('More options', {exact: true}).click();
  await page.getByLabel('Tags, separated by commas').fill('CNN, study');
  await page.getByLabel('Keep on this device only').check();
  const created = page.waitForResponse(response => response.url().endsWith('/api/memories') && response.request().method() === 'POST');
  await page.getByRole('button',{name:'Save memory',exact:true}).click();
  createdId = (await (await created).json()).memory_id;
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button',{name:title,exact:true})).toBeVisible();
  await page.getByLabel('Search memories').fill('What topic was I struggling with in CNN?');
  await page.getByRole('button',{name:'Search',exact:true}).click();
  const card=page.locator('.memory-card').filter({hasText:title});
  await expect(card).toBeVisible();
  await card.getByRole('button',{name:'Edit',exact:true}).click();
  await page.getByLabel('Memory',{exact:true}).fill('Completed backpropagation and CNN fundamentals.');
  await page.getByRole('button',{name:'Save memory',exact:true}).click();
  await expect(card).toContainText('Completed backpropagation');
  await page.getByLabel('Search memories').fill('');
  await page.getByRole('button',{name:'Search',exact:true}).click();
  await card.getByRole('button',{name:'Archive',exact:true}).click();
  await expect(card).toHaveCount(0);
  await page.getByRole('button',{name:'Archived memories'}).click();
  await expect(card).toBeVisible();
  await card.getByRole('button',{name:'Restore',exact:true}).click();
  await page.getByRole('button',{name:'Back to saved memories'}).click();
  await expect(card).toBeVisible();
  page.once('dialog',d=>d.accept());
  await card.getByRole('button',{name:'Delete '+title}).click();
  await expect(card).toHaveCount(0);
  } finally {
    if (createdId) {
      const [active, archived] = await Promise.all(['/api/memories', '/api/memories?archived=true'].map(async path => (await page.request.get(path)).json()));
      const remaining = [...active, ...archived].find(memory => memory.memory_id === createdId);
      if (remaining) await page.request.delete('/api/memories/' + createdId + '?expected_version=' + remaining.version);
    }
  }
});
test('desktop and mobile navigation have no horizontal overflow',async({page})=>{
  await page.goto('/');
  await page.screenshot({path:'../docs/screenshot-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await expect(page.getByRole('heading',{name:'How can I help you?'})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await page.screenshot({path:'../docs/screenshot-mobile.png',fullPage:true});
});

test('everyday tasks stay simple while optional controls remain available in settings', async ({page}) => {
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const responses = {
      '/api/status': {connection: 'ONLINE', vector_ready: true, active_memories: 0, pending: 0, failed: 0, conflicts: 0},
      '/api/settings': {preferences: {memory_enabled: true, default_type: 'STANDARD'}, embedding_model: 'test-embedding-model', local_model: 'test-local-model', cloud_model: 'Not configured'},
      '/api/chats': [],
      '/api/memories': [],
      '/api/plugins': [],
      '/api/sync': {conflicts: [], operations: [{id: 'operation-test-id', entity: 'memory-test-id', status: 'SYNCED', retries: 0}]},
    };
    if (route.request().method() !== 'GET' || !(path in responses)) {
      return route.fulfill({status: 500, json: {detail: 'Unexpected request in navigation test'}});
    }
    return route.fulfill({json: responses[path]});
  });
  await page.goto('/');
  await expect(page.getByRole('heading', {name: 'How can I help you?', exact: true})).toBeVisible();
  const sidebar = page.locator('.sidebar');
  await expect(sidebar.getByRole('button', {name: /API Plugins|Sync Center|Conflicts/})).toHaveCount(0);
  await sidebar.getByRole('button', {name: 'Saved memories', exact: false}).click();
  await page.getByRole('button', {name: 'New memory', exact: true}).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog.getByLabel('Title', {exact: true})).toBeVisible();
  await expect(dialog.getByLabel('Memory', {exact: true})).toBeVisible();
  await expect(dialog.getByLabel('Keep on this device only')).toBeVisible();
  await expect(dialog.getByLabel('Tags, separated by commas')).toBeHidden();
  await expect(dialog.getByLabel('Memory length', {exact: true})).toBeHidden();
  await dialog.getByText('More options', {exact: true}).click();
  await expect(dialog.getByLabel('Tags, separated by commas')).toBeVisible();
  await expect(dialog.getByLabel('Memory length', {exact: true})).toBeVisible();
  await dialog.getByRole('button', {name: 'Close editor', exact: true}).click();

  await sidebar.getByRole('button', {name: 'Settings', exact: true}).click();
  await expect(page.getByText('test-embedding-model', {exact: true})).toBeHidden();
  await page.getByText('Advanced settings', {exact: true}).click();
  await expect(page.getByText('test-embedding-model', {exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Manage AI connections', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'AI connections', exact: true})).toBeVisible();
  await sidebar.getByRole('button', {name: 'Settings', exact: true}).click();
  await page.getByRole('button', {name: 'View sync status', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Device sync', exact: true})).toBeVisible();
  await expect(page.getByRole('table')).toBeHidden();
  await page.getByText('Technical details', {exact: true}).click();
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByRole('button', {name: 'Review changes', exact: true})).toHaveCount(0);
});
