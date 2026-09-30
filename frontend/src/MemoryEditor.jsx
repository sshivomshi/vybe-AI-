import React, {useEffect, useRef, useState} from 'react';
import {Check, Sparkles, X} from 'lucide-react';
import {fields, write} from './api';

export const memoryLengths = {QUICK: 'Short', STANDARD: 'Standard', DETAILED: 'Detailed', ARCHIVE_ONLY: 'Archive only'};
export const blankMemory = {title: '', summary: '', tags: [], memory_type: 'STANDARD', importance: .5, local_only: false, archived: false};

export default function MemoryEditor({value, onClose, onSave, heading = 'Save a memory'}) {
  const [form, setForm] = useState({...blankMemory, ...fields(value || {})});
  const [tags, setTags] = useState((value?.tags || []).join(', '));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const dialog = useRef(null);
  const set = (key, next) => setForm(current => ({...current, [key]: next}));

  useEffect(() => {
    const previousFocus = document.activeElement;
    dialog.current?.querySelector('input')?.focus();
    return () => previousFocus?.focus();
  }, []);
  useEffect(() => {
    const handle = event => {
      if (event.key === 'Escape' && !busy) onClose();
      if (event.key !== 'Tab') return;
      const elements = [...dialog.current.querySelectorAll('button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), summary')].filter(element => element.getClientRects().length);
      const first = elements[0], last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last?.focus();}
      else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [busy, onClose]);

  return <div className="overlay" onClick={() => !busy && onClose()}>
    <section ref={dialog} role="dialog" aria-modal="true" aria-labelledby="memory-editor-title" className="modal memory-editor" onClick={event => event.stopPropagation()}>
      <div className="row"><h2 id="memory-editor-title">{value?.review ? 'Review before saving' : heading}</h2><button className="icon" aria-label="Close editor" disabled={busy} onClick={onClose}><X/></button></div>
      <p>{value?.review ? 'Check or edit this suggested memory. It is saved only when you choose Save memory.' : 'Save a useful detail so the assistant can remember it in future chats.'}</p>
      <form onSubmit={async event => {
        event.preventDefault(); setBusy(true); setError('');
        try {await onSave({...form, tags: tags.split(',').map(tag => tag.trim()).filter(Boolean)}); onClose();}
        catch (cause) {setError(cause.message);}
        finally {setBusy(false);}
      }}>
        <div className="form-fields"><fieldset disabled={busy}>
          <label>Title<input required maxLength={160} value={form.title} onChange={event => set('title', event.target.value)} placeholder="For example, My food preferences"/></label>
          <label>Memory<textarea aria-label="Memory" required rows={4} maxLength={12000} value={form.summary} onChange={event => set('summary', event.target.value)} placeholder="For example, I prefer vegetarian meals and quick recipes."/></label>
          <label className="check"><input type="checkbox" checked={form.local_only} onChange={event => set('local_only', event.target.checked)}/>Keep on this device only</label>
          <p className="field-help">When checked, this memory stays on this device and is used only by the assistant running here.</p>
          <details className="simple-disclosure memory-options">
            <summary>More options</summary>
            <label>Tags, separated by commas<input value={tags} onChange={event => setTags(event.target.value)} placeholder="For example, food, preferences"/></label>
            <label>Memory length<select aria-label="Memory length" value={form.memory_type} onChange={event => set('memory_type', event.target.value)}>{Object.entries(memoryLengths).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
            <p className="field-help">Standard works for most details. Archived memories are kept for you but are not used in replies.</p>
            <label>How important is this?<input type="range" min="0" max="1" step="0.1" value={form.importance} onChange={event => set('importance', Number(event.target.value))}/><span className="range-labels"><span>Less important</span><span>Very important</span></span></label>
            <button type="button" disabled={busy || !form.title.trim() || !form.summary.trim()} onClick={async () => {
              setBusy(true); setError('');
              try {setForm(await write('/compact', {...form, tags: tags.split(',').map(tag => tag.trim()).filter(Boolean)}));}
              catch (cause) {setError(cause.message);}
              finally {setBusy(false);}
            }}><Sparkles size={15}/>Help me rewrite this</button>
            <p className="field-help">Review the suggested wording before saving.</p>
          </details>
        </fieldset></div>
        {error && <div className="error" role="alert">{error}</div>}
        <div className="actions"><button type="button" disabled={busy} onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save memory'}<Check size={16}/></button></div>
      </form>
    </section>
  </div>;
}
