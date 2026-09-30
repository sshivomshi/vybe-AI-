import {test, expect} from '@playwright/test';

test('API plugins can be added, edited, tested, selected, disabled and deleted', async ({page}) => {
  let records = [];
  const changes = [];
  // Only the plugin API is mocked: this test never contacts a provider or stores a key.
  await page.route('**/api/plugins**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const body = request.postDataJSON();
    changes.push({path, method, body});
    let result;
    if (path === '/api/plugins' && method === 'GET') result = records;
    else if (path === '/api/plugins' && method === 'POST') {
      const {api_key, ...connection} = body;
      result = {id: 'plugin-browser-test', ...connection, is_default: false, has_api_key: Boolean(api_key), last_test: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString()};
      records.push(result);
    } else if (path.endsWith('/default') && method === 'POST') {
      records = records.map(record => ({...record, is_default: true}));
      result = records[0];
    } else if (path.endsWith('/test') && method === 'POST') {
      result = {ok: true, message: 'The configured model responded.', checked_at: new Date().toISOString()};
      records[0].last_test = result;
    } else if (method === 'PUT') {
      const {api_key, clear_api_key, ...connection} = body;
      records[0] = {...records[0], ...connection};
      if (api_key) records[0].has_api_key = true;
      if (clear_api_key) records[0].has_api_key = false;
      if (connection.enabled === false) records[0].is_default = false;
      result = records[0];
    } else if (method === 'DELETE') {
      records = [];
      result = {ok: true};
    } else throw new Error('Unexpected plugin request: ' + method + ' ' + path);
    await route.fulfill({json: result});
  });

  await page.goto('/');
  await page.getByRole('button', {name: 'Settings', exact: true}).click();
  await page.getByRole('button', {name: 'Manage AI connections'}).click();
  await expect(page.getByRole('heading', {name: 'AI connections', exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Connect a service', exact: true}).click();
  await page.getByLabel('Connection name').fill('My API');
  await page.getByLabel('Service address (API URL)').fill('http://127.0.0.1:11434/v1');
  await page.getByLabel('Model name').fill('my-model');
  await page.getByLabel('API key (optional)').fill('test-only-key');
  await page.getByRole('button', {name: 'Save connection', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  let card = page.getByRole('article', {name: 'My API', exact: true});
  await expect(card).toContainText('API key saved');
  await expect(page.getByText('test-only-key', {exact: true})).toHaveCount(0);

  await card.getByRole('button', {name: 'Edit', exact: true}).click();
  await expect(page.getByLabel('API key (leave blank to keep existing)')).toHaveValue('');
  await page.getByLabel('Connection name').fill('My updated API');
  await page.getByLabel('Model name').fill('updated-model');
  await page.getByRole('button', {name: 'Save connection', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  card = page.getByRole('article', {name: 'My updated API', exact: true});
  await expect(card.getByText('updated-model', {exact: true})).toBeHidden();
  await card.getByText('Connection details', {exact: true}).click();
  await expect(card.getByText('updated-model', {exact: true})).toBeVisible();
  expect(changes.find(change => change.method === 'PUT').body).not.toHaveProperty('api_key');
  await expect(card).toContainText('API key saved');

  await card.getByRole('button', {name: 'Test connection', exact: true}).click();
  await expect(card).toContainText('Connection successful');
  await card.getByRole('button', {name: 'Use for chat', exact: true}).click();
  await expect(card).toContainText('Used for chat');
  await expect(page.locator('.plugin-routing')).toContainText('My updated API');
  await card.getByRole('button', {name: 'Turn off', exact: true}).click();
  await expect(card).toContainText('Off');
  await expect(card.getByRole('button', {name: 'Use for chat', exact: true})).toBeDisabled();
  await expect(page.locator('.plugin-routing')).toContainText('Built-in assistant');
  await card.getByRole('button', {name: 'Turn on', exact: true}).click();
  await card.getByRole('button', {name: 'Edit', exact: true}).click();
  await page.getByLabel('Remove saved API key').check();
  await expect(page.getByLabel('API key (leave blank to keep existing)')).toBeDisabled();
  await page.getByRole('button', {name: 'Save connection', exact: true}).click();
  await expect(card).toContainText('No API key');

  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  page.once('dialog', dialog => dialog.accept());
  await card.getByRole('button', {name: 'Delete My updated API', exact: true}).click();
  await expect(card).toHaveCount(0);
  await expect(page.getByRole('heading', {name: 'No extra services connected'})).toBeVisible();
});

test('API plugin save errors keep the editor open for correction', async ({page}) => {
  await page.route('**/api/plugins', async route => {
    await route.fulfill(route.request().method() === 'GET'
      ? {json: []}
      : {status: 422, json: {detail: 'Use HTTPS for remote API services.'}});
  });
  await page.goto('/?view=plugins');
  await page.getByRole('button', {name: 'Connect a service', exact: true}).click();
  await page.getByLabel('Connection name').fill('Unsecured endpoint');
  await page.getByLabel('Service address (API URL)').fill('http://invalid.example/v1');
  await page.getByLabel('Model name').fill('test-model');
  await page.getByRole('button', {name: 'Save connection', exact: true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('alert')).toHaveText('Use HTTPS for remote API services.');
  await expect(page.getByLabel('Connection name')).toHaveValue('Unsecured endpoint');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('real API persists a disabled plugin and its edits without changing chat routing', async ({page}) => {
  const name = 'Browser plugin ' + Date.now();
  let createdId;
  try {
    await page.goto('/?view=plugins');
    await page.getByRole('button', {name: 'Connect a service', exact: true}).click();
    await page.getByLabel('Connection name').fill(name);
    await page.getByLabel('Service address (API URL)').fill('http://127.0.0.1:11434/v1');
    await page.getByLabel('Model name').fill('browser-test-model');
    await page.getByLabel('Allow this connection').uncheck();
    const createdResponse = page.waitForResponse(response => response.url().endsWith('/api/plugins') && response.request().method() === 'POST');
    await page.getByRole('button', {name: 'Save connection', exact: true}).click();
    const response = await createdResponse;
    expect(response.ok()).toBeTruthy();
    createdId = (await response.json()).id;
    await expect(page.getByRole('dialog')).toHaveCount(0);
    let card = page.getByRole('article', {name, exact: true});
    await expect(card).toContainText('Off');
    await expect(card.getByRole('button', {name: 'Use for chat', exact: true})).toBeDisabled();

    await card.getByRole('button', {name: 'Edit', exact: true}).click();
    await page.getByLabel('Connection name').fill(name + ' edited');
    await page.getByLabel('Model name').fill('browser-test-model-updated');
    await page.getByRole('button', {name: 'Save connection', exact: true}).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await page.reload();
    card = page.getByRole('article', {name: name + ' edited', exact: true});
    await expect(card).toContainText('browser-test-model-updated');
    await expect(card).toContainText('Off');
    const saved = (await (await page.request.get('/api/plugins')).json()).find(record => record.id === createdId);
    expect(saved).toMatchObject({name: name + ' edited', enabled: false, is_default: false, has_api_key: false});
    expect(saved).not.toHaveProperty('api_key');
    page.once('dialog', dialog => dialog.accept());
    await card.getByRole('button', {name: 'Delete ' + name + ' edited', exact: true}).click();
    await expect(card).toHaveCount(0);
  } finally {
    if (createdId) await page.request.delete('/api/plugins/' + createdId);
  }
});
