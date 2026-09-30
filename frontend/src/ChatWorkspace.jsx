import React, {useEffect, useRef} from 'react';
import {ArrowRight, ArrowUp, BookOpen, CalendarDays, ChevronDown, MessageCircle, PenLine, Plus, Sparkles, ShieldCheck} from 'lucide-react';
import './chat-easy.css';
import SpaceScene from './SpaceScene';

const starters = [
  {icon: PenLine, title: 'Write something', description: 'A message, email, or story', prompt: 'Help me write something. Ask me what I want to write and who it is for.'},
  {icon: BookOpen, title: 'Explain a topic', description: 'Get a clear explanation', prompt: 'Explain a topic to me in simple words. Ask me what I would like to learn.'},
  {icon: CalendarDays, title: 'Plan my day', description: 'Sort out your tasks', prompt: 'Help me plan my day. Ask me what I need to get done.'},
];

function ChatMessage({message, memoryEnabled, onReview, onDismiss}) {
  const {role, content, metadata = {}} = message;
  return <article className={'message ' + role}>
    <span className={'message-avatar ' + role} aria-hidden="true">{role === 'user' ? 'Y' : <MessageCircle size={20}/>}</span>
    <div><div className="message-byline"><strong>{role === 'user' ? 'You' : 'Your assistant'}</strong></div>
      <p>{content}</p>{role==='assistant'&&metadata.route&&<small className="reply-model">{metadata.route==='cloud'?'Google / cloud':metadata.route==='local'?'Local model':metadata.route}{metadata.model?` · ${metadata.model}`:''}</small>}
      {metadata.memories_used?.length > 0 && <details className="reply-memories"><summary><BookOpen size={16}/>Saved details used in this reply<ChevronDown size={15}/></summary>{metadata.memories_used.map(memory => <div className="used-memory" key={memory.memory_id}><b>{memory.title}</b><p>{memory.summary}</p></div>)}</details>}
      {metadata.candidate && memoryEnabled && <div className="memory-review-prompt">
        <button className="memory-review-trigger" aria-haspopup="dialog" onClick={() => onReview(metadata.candidate, metadata.related_id)}><BookOpen size={16}/><span>Review before saving</span><ArrowRight size={15}/></button>
        <button className="memory-review-dismiss" onClick={() => onDismiss(message)}>Don't save</button>
      </div>}
    </div>
  </article>;
}

export default function ChatWorkspace({inference, onInference, capture, captureBusy, onCapture, messages, input, setInput, busy, prefs, onSend, onNewChat, onNavigate, onReview, onDismiss}) {
  const composer = useRef(null);
  const conversation = useRef(null);
  const isNew = messages.length === 0;
  const captureSwitch = <><label className="chat-inference">AI mode<select aria-label="AI mode" disabled={busy} value={inference} onChange={event=>onInference(event.target.value)}><option value="configured">Configured AI (Google)</option><option value="local">Local model · offline</option></select></label><label className="save-chat-control" title="Capture this conversation in your local constellation"><input type="checkbox" role="switch" checked={capture} disabled={captureBusy || busy} onChange={event => onCapture(event.target.checked)}/><span className="save-chat-track" aria-hidden="true"/><span>Save chat</span></label></>;
  useEffect(() => {
    if (conversation.current) conversation.current.scrollTop = conversation.current.scrollHeight;
  }, [messages.length, busy]);
  const chooseStarter = prompt => {
    setInput(prompt);
    composer.current?.focus();
  };

  return <section className={'chat-workspace easy-chat-workspace ' + (isNew ? 'is-welcome' : 'is-conversation')}>
    {isNew && <div className="easy-save-chat">{captureSwitch}</div>}
    {!isNew && <div className="easy-chat-top">{captureSwitch}<button className="easy-new-chat" disabled={busy} onClick={() => {onNewChat();composer.current?.focus();}}><Plus size={18}/>New chat</button></div>}
    {isNew ? <div className="easy-welcome">
      <SpaceScene/>
      <h1>Where will your mind go?</h1>
      <p>Big questions. Small ideas. Endless possibilities.</p>
    </div> : <><div className="easy-conversation-heading"><h1>Your conversation</h1></div><div ref={conversation} className="conversation-messages" aria-live="polite">
      {messages.map((message, index) => <ChatMessage key={message.id || index} message={message} memoryEnabled={prefs?.preferences?.memory_enabled !== false} onReview={onReview} onDismiss={onDismiss}/>)}
      {busy && <div className="processing" role="status"><span className="pulse"/>Thinking about your message…</div>}
    </div></>}

    <div className="easy-composer-section"><form className="easy-composer" onSubmit={onSend}>
      <label htmlFor="chat-message">Message</label>
      <textarea ref={composer} id="chat-message" disabled={busy} aria-label="Message" placeholder="Message Vybe AI" rows={3} value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => {if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {event.preventDefault();if (!busy) onSend(event);}}}/>
      <div className="easy-composer-actions"><span className="easy-keyboard-hint">Press Enter to send</span><button className="easy-send" disabled={busy || !input.trim()} aria-label="Send message"><span>{busy ? 'Thinking…' : 'Send'}</span><ArrowUp size={18}/></button></div>
    </form><p className="easy-memory-note"><ShieldCheck size={16}/>Memories are saved only after you approve them.</p></div>

    {isNew && <section className="easy-starters" aria-label="Ideas to get started"><h2>A place to start</h2><div>{starters.map(({icon: Icon, title, description, prompt}) => <button key={title} onClick={() => chooseStarter(prompt)}><Icon size={21} strokeWidth={1.7}/><span><strong>{title}</strong><span>{description}</span></span><ArrowRight size={17}/></button>)}</div></section>}

    <div className="easy-chat-help"><details><summary>How to use this<ChevronDown size={16}/></summary><ol><li>Type a question or choose an idea above.</li><li>Click <strong>Send</strong> and wait for your reply.</li><li>Ask another question whenever you like.</li></ol><p>Choose Local model to chat without internet after the local model is installed and running. Google remains selected until you explicitly change AI mode; private memories require local inference.</p><p>Save chat captures messages for the constellation. To make a useful detail available to future AI replies, review and save its memory suggestion. Captured transcripts are not automatically indexed as memories.</p><p>To start a new topic, click <strong>New chat</strong>. Use Shift + Enter to add a new line to your message.</p></details></div>
  </section>;
}
