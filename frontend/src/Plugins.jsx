import React, {useEffect, useRef, useState} from 'react';
import {ArrowLeft, ArrowRight, Check, CircleCheck, MessageSquare, KeyRound, Plug, Plus, ShieldCheck, Trash2, X} from 'lucide-react';
import {api, write} from './api';
import './plugins.css';

const emptyPlugin = {name: '', base_url: '', model: '', api_key: '', enabled: true, clear_api_key: false};
const displayDate = value => value ? new Date(value).toLocaleString() : '';

function PluginEditor({plugin, onClose, onSave}) {
  const [form, setForm] = useState({...emptyPlugin, ...plugin, api_key: ''});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const dialog = useRef(null);
  const heading = plugin ? 'Edit connection' : 'Connect an AI service';
  const endpointChanged = plugin && form.base_url.trim().replace(/\/+$/, '') !== plugin.base_url.replace(/\/+$/, '');
  const set = (key, value) => setForm(current => ({...current, [key]: value}));

  useEffect(() => {
    const previousFocus = document.activeElement;
    dialog.current?.querySelector('input')?.focus();
    return () => previousFocus?.focus();
  }, []);

  useEffect(() => {
    const handleKeys = event => {
      if (event.key === 'Escape' && !busy) {
        event.preventDefault();
        onClose();
      }
      if (event.key !== 'Tab') return;
      const elements = [...dialog.current.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), summary, a[href], textarea:not(:disabled)')].filter(element => element.getClientRects().length > 0);
      const first = elements[0], last = elements.at(-1);
      if (!elements.length) {
        event.preventDefault();
      } else if (!dialog.current.contains(document.activeElement)) {
        event.preventDefault();
        (event.shiftKey ? last : first)?.focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first?.focus();
      }
    };
    document.addEventListener('keydown', handleKeys);
    return () => document.removeEventListener('keydown', handleKeys);
  }, [busy, onClose]);

  useEffect(() => {
    if (error && !busy) dialog.current?.querySelector('input:not(:disabled)')?.focus();
  }, [error, busy]);

  const save = async event => {
    event.preventDefault();
    setBusy(true);
    setError('');
    const body = {name: form.name.trim(), base_url: form.base_url.trim(), model: form.model.trim(), enabled: form.enabled};
    if (form.api_key) body.api_key = form.api_key;
    if (plugin && form.clear_api_key) body.clear_api_key = true;
    try {
      await onSave(body);
      onClose();
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusy(false);
    }
  };

  return <div className="overlay" onClick={() => !busy && onClose()}>
    <section ref={dialog} role="dialog" aria-modal="true" aria-labelledby="plugin-editor-title" className="modal plugin-editor" onClick={event => event.stopPropagation()}>
      <div className="row"><h2 id="plugin-editor-title">{heading}</h2><button type="button" className="icon" aria-label="Close connection editor" disabled={busy} onClick={onClose}><X size={20}/></button></div>
      <p>Copy these details from your AI service’s account or setup page. Saving them does not send your conversations.</p>
      <form onSubmit={save}>
        <div className="form-fields"><fieldset disabled={busy}>
          <label>Connection name<input required maxLength={80} value={form.name} onChange={event => set('name', event.target.value)} placeholder="A name you’ll recognize" autoComplete="off"/></label>
          <label>Service address (API URL)<input type="url" required value={form.base_url} onChange={event => set('base_url', event.target.value)} placeholder="Paste the address from your service" aria-describedby="plugin-url-help" autoComplete="off" spellCheck={false}/></label>
          <p id="plugin-url-help" className="plugin-field-help">Your service calls this the “base URL” or “API URL”. It is usually different from its website address.</p>
          <label>Model name<input required maxLength={160} value={form.model} onChange={event => set('model', event.target.value)} placeholder="Copy the model name from your service" autoComplete="off" spellCheck={false}/></label>
          <label>API key {endpointChanged ? '(re-enter for new URL)' : plugin ? '(leave blank to keep existing)' : '(optional)'}<input type="password" value={form.api_key} disabled={form.clear_api_key} onChange={event => set('api_key', event.target.value)} autoComplete="new-password" aria-describedby="plugin-key-help"/></label>
          <p id="plugin-key-help" className="plugin-field-help">An API key is a private access code from your service. {endpointChanged ? 'Changing the service address removes the saved key. Enter a key for the new service if it needs one.' : 'It is encrypted on this device and is never displayed again. Leave it empty if your service does not need one.'}</p>
          {plugin?.has_api_key && <label className="check"><input type="checkbox" checked={form.clear_api_key} onChange={event => setForm(current => ({...current, clear_api_key: event.target.checked, api_key: ''}))}/>Remove saved API key</label>}
          <label className="check"><input type="checkbox" checked={form.enabled} onChange={event => set('enabled', event.target.checked)}/>Allow this connection</label>
          <details className="plugin-more-details"><summary>More connection details</summary><p>This service must support the OpenAI-compatible chat format. Include /v1 in the address if your service asks for it. Mnemos adds /chat/completions when it connects.</p></details>
        </fieldset></div>
        {error && <div className="error" role="alert">{error}</div>}
        <div className="actions"><button type="button" disabled={busy} onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save connection'}<Check size={16}/></button></div>
      </form>
    </section>
  </div>;
}

export default function Plugins({onChanged, onBack}) {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [editor, setEditor] = useState(undefined);
  const [busy, setBusy] = useState(null);

  const load = async () => setPlugins(await api('/plugins'));
  useEffect(() => {
    let active = true;
    api('/plugins').then(result => active && setPlugins(result)).catch(cause => active && setError(cause.message)).finally(() => active && setLoading(false));
    return () => {active = false;};
  }, []);

  const act = async (plugin, action, message) => {
    setBusy(plugin.id);
    setError('');
    setNotice('');
    try {
      await action();
      await load();
      onChanged?.();
      if (message) setNotice(message);
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusy(null);
    }
  };

  const selected = plugins.find(plugin => plugin.is_default && plugin.enabled);
  return <div className="plugins-page">
    {onBack && <button className="plugin-back" onClick={onBack}><ArrowLeft size={16}/>Back to chat</button>}
    <div className="page-heading"><div><h1>AI connections</h1><p>Optional: connect an AI service you already use. You can keep chatting without adding one.</p></div><button className="primary" onClick={() => setEditor(null)}><Plus size={16}/>Connect a service</button></div>
    <div className="plugin-routing"><span className="plugin-routing-icon"><MessageSquare size={20}/></span><div><span className="plugin-routing-label">Used for chat</span><strong>{selected ? selected.name : 'Built-in assistant'}</strong></div></div>
    {error && <div role="alert" className="error global-error">{error}</div>}
    {notice && <div role="status" className="plugin-notice"><CircleCheck size={16}/>{notice}</div>}
    {loading ? <p role="status" className="muted">Loading connections…</p> : plugins.length ? <div className="plugin-grid">{plugins.map(plugin => <article className={'plugin-card' + (plugin.is_default && plugin.enabled ? ' plugin-selected' : '')} key={plugin.id} aria-label={plugin.name}>
      <div className="row"><span className="plugin-symbol"><Plug size={21}/></span><div className="plugin-badges">{plugin.is_default && plugin.enabled && <span className="badge green">Used for chat</span>}<span className={'badge ' + (plugin.enabled ? 'green' : 'neutral')}>{plugin.enabled ? 'On' : 'Off'}</span></div></div>
      <h2>{plugin.name}</h2>
      <div className="plugin-key-status"><KeyRound size={14}/>{plugin.has_api_key ? 'API key saved' : 'No API key'}</div>
      {plugin.last_test && <div className={'plugin-test-result ' + (plugin.last_test.ok ? 'passed' : 'failed')} role="status"><strong>{plugin.last_test.ok ? 'Connection successful' : 'Connection failed'}</strong></div>}
      <details className="plugin-connection-details"><summary>Connection details</summary><div className="plugin-detail"><span>Model</span><p className="plugin-model">{plugin.model}</p></div><div className="plugin-detail"><span>Address</span><p className="plugin-endpoint">{plugin.base_url}</p></div>{plugin.last_test && <div className="plugin-last-test"><p>{plugin.last_test.message}</p><small>Last tested {displayDate(plugin.last_test.checked_at)}</small></div>}</details>
      <div className="plugin-card-actions"><button disabled={busy !== null} onClick={() => setEditor(plugin)}>Edit</button><button disabled={busy !== null || !plugin.enabled} title="Send a small test message without your conversation or memories" onClick={() => act(plugin, () => write('/plugins/' + plugin.id + '/test', {}))}>{busy === plugin.id ? 'Working…' : 'Test connection'}</button><button disabled={busy !== null} onClick={() => act(plugin, () => write('/plugins/' + plugin.id, {name: plugin.name, base_url: plugin.base_url, model: plugin.model, enabled: !plugin.enabled}, 'PUT'), plugin.enabled ? 'Connection turned off.' : 'Connection turned on.')}>{plugin.enabled ? 'Turn off' : 'Turn on'}</button><button className="icon" aria-label={'Delete ' + plugin.name} disabled={busy !== null} onClick={() => {if (confirm('Delete “' + plugin.name + '” and its saved API key?')) act(plugin, () => api('/plugins/' + plugin.id, {method: 'DELETE'}), 'Connection deleted.');}}><Trash2 size={15}/></button></div>
      {!plugin.is_default && <button className="plugin-default-button" disabled={busy !== null || !plugin.enabled} onClick={() => act(plugin, () => write('/plugins/' + plugin.id + '/default', {}), plugin.name + ' will now be used for chat.')}><span>Use for chat</span><ArrowRight size={15}/></button>}
    </article>)}</div> : !error && <div className="plugin-empty"><h2>No extra services connected</h2><p>Your built-in assistant is already available. Add a connection only if you want to use another AI service.</p>{onBack && <button onClick={onBack}><MessageSquare size={16}/>Start chatting</button>}</div>}
    <section className="plugin-privacy"><ShieldCheck size={20}/><div><h3>Your privacy</h3><p>When you choose a service for chat, your messages and relevant saved memories may be sent to it. Memories saved for this device only stay on your computer. You can turn off a connection at any time.</p></div></section>
    {editor !== undefined && <PluginEditor plugin={editor} onClose={() => setEditor(undefined)} onSave={async body => {await write('/plugins' + (editor ? '/' + editor.id : ''), body, editor ? 'PUT' : 'POST');await load();onChanged?.();setNotice(editor ? 'Connection updated.' : 'Connection saved. Choose “Use for chat” when you are ready.');}}/>}
  </div>;
}
