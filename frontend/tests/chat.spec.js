import {test, expect} from '@playwright/test';

test('chat starters, keyboard composition and pending conversation controls work together', async ({page}) => {
  let submittedContent;
  let sendRequests = 0;
  let releaseResponse;
  const responseAllowed = new Promise(resolve => { releaseResponse = resolve; });
  const unexpectedRequests = [];
  const reply = 'Let us revisit your recent ideas and choose a useful next step.';

  // Keep this interaction test independent of saved chats and model availability.
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const respond = body => route.fulfill({json: body});
    if (request.method() === 'GET') {
      if (path === '/api/status') return respond({connection: 'ONLINE', vector_ready: true, active_memories: 3, pending: 0, conflicts: 0});
      if (path === '/api/sync') return respond({operations: [], conflicts: []});
      if (path === '/api/settings') return respond({preferences: {memory_enabled: true, default_type: 'STANDARD'}, cloud_model: 'Not configured'});
      if (path === '/api/chats') return respond([{id: 'previous-chat', title: 'Previous conversation'}]);
      if (path === '/api/chats/current-chat') return respond([
        {id: 'user-message', role: 'user', content: submittedContent, metadata: {}},
        {id: 'assistant-message', role: 'assistant', content: reply, metadata: {route: 'local'}},
      ]);
    }
    if (path === '/api/chat' && request.method() === 'POST') {
      sendRequests += 1;
      submittedContent = request.postDataJSON().content;
      await responseAllowed;
      return respond({chat_id: 'current-chat', response: reply, warnings: []});
    }
    unexpectedRequests.push(request.method() + ' ' + path);
    return route.fulfill({status: 500, json: {detail: 'Unexpected test request'}});
  });

  try {
    await page.goto('/');
    const message = page.getByRole('textbox', {name: 'Message', exact: true});
    await page.getByRole('button', {name: /Write something/}).click();
    await expect(message).toHaveValue('Help me write something. Ask me what I want to write and who it is for.');
    await expect(message).toBeFocused();

    await message.press('End');
    await message.press('Shift+Enter');
    await message.pressSequentially('Include a practical next step.');
    const content = 'Help me write something. Ask me what I want to write and who it is for.\nInclude a practical next step.';
    await expect(message).toHaveValue(content);

    // Enter confirms an IME candidate without submitting the conversation.
    await message.dispatchEvent('keydown', {key: 'Enter', code: 'Enter', isComposing: true, bubbles: true});
    await expect(message).toHaveValue(content);
    expect(sendRequests).toBe(0);

    await message.press('Enter');
    await expect.poll(() => sendRequests).toBe(1);
    expect(submittedContent).toBe(content);
    await expect(page.locator('.message.user p')).toHaveText(content);
    await expect(message).toHaveValue(content);
    await expect(message).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Send message', exact: true})).toBeDisabled();
    await expect(page.getByRole('button', {name: 'New chat', exact: true})).toBeDisabled();
    const resets = page.getByRole('button', {name: 'New conversation', exact: true});
    await expect(resets).toHaveCount(1);
    await expect(resets).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Previous conversation', exact: true})).toBeDisabled();

    releaseResponse();
    await expect(page.locator('.message.assistant p')).toHaveText(reply);
    await expect(page.getByRole('button', {name: 'Previous conversation', exact: true})).toBeEnabled();
    await page.getByRole('button', {name: 'New chat', exact: true}).click();
    await expect(page.getByRole('heading', {name: 'Where will your mind go?', exact: true})).toBeVisible();
    await expect(page.locator('.message')).toHaveCount(0);
    expect(unexpectedRequests).toEqual([]);
  } finally {
    releaseResponse();
  }
});
