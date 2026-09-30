/**
 * Local Device Storage Manager
 * Stores all chats, notes, and settings securely on the device using localStorage.
 * Zero server required.
 */

const STORAGE_KEYS = {
  NOTES: 'mnemos_device_notes',
  CHATS: 'mnemos_device_chats',
  SETTINGS: 'mnemos_device_settings',
  ACTIVE_CHAT: 'mnemos_active_chat_id'
};

// Default settings
export const DEFAULT_SETTINGS = {
  provider: 'free', // 'free' | 'groq' | 'openai' | 'openrouter' | 'custom'
  apiKey: '',
  model: 'llama-3.3-70b',
  customUrl: '',
  autoExtractNotes: true,
  autoSaveNotes: true,
  theme: 'dark'
};

// Safe JSON parser
function parseJson(str, fallback) {
  try {
    return str ? JSON.parse(str) : fallback;
  } catch (e) {
    console.error('Storage parse error:', e);
    return fallback;
  }
}

// ---------------- NOTES API ----------------

export function getDeviceNotes() {
  const notes = parseJson(localStorage.getItem(STORAGE_KEYS.NOTES), []);
  return Array.isArray(notes) ? notes : [];
}

export function saveDeviceNote(note) {
  const notes = getDeviceNotes();
  const id = note.id || 'note_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7);
  const now = new Date().toISOString();

  const newNote = {
    id,
    title: note.title || 'Untitled Note',
    summary: note.summary || '',
    keyPoints: note.keyPoints || [],
    tags: Array.isArray(note.tags) ? note.tags : ['General'],
    category: note.category || 'Key Fact', // 'Key Fact' | 'Action Item' | 'Summary' | 'Idea'
    importance: note.importance || 'Medium',
    sourceChatId: note.sourceChatId || null,
    sourceQuery: note.sourceQuery || '',
    createdAt: note.createdAt || now,
    updatedAt: now
  };

  const existingIdx = notes.findIndex(n => n.id === id);
  if (existingIdx >= 0) {
    notes[existingIdx] = { ...notes[existingIdx], ...newNote, updatedAt: now };
  } else {
    notes.unshift(newNote);
  }

  localStorage.setItem(STORAGE_KEYS.NOTES, JSON.stringify(notes));
  return newNote;
}

export function deleteDeviceNote(id) {
  const notes = getDeviceNotes().filter(n => n.id !== id);
  localStorage.setItem(STORAGE_KEYS.NOTES, JSON.stringify(notes));
  return notes;
}

export function updateDeviceNote(id, updates) {
  const notes = getDeviceNotes();
  const idx = notes.findIndex(n => n.id === id);
  if (idx >= 0) {
    notes[idx] = { ...notes[idx], ...updates, updatedAt: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEYS.NOTES, JSON.stringify(notes));
    return notes[idx];
  }
  return null;
}

export function clearAllDeviceNotes() {
  localStorage.removeItem(STORAGE_KEYS.NOTES);
  return [];
}

// Export notes as JSON or Markdown
export function exportNotesAsFile(format = 'markdown') {
  const notes = getDeviceNotes();
  let content = '';
  let filename = `notes_export_${new Date().toISOString().slice(0, 10)}`;
  let mimeType = 'text/plain';

  if (format === 'json') {
    content = JSON.stringify(notes, null, 2);
    filename += '.json';
    mimeType = 'application/json';
  } else {
    filename += '.md';
    mimeType = 'text/markdown';
    content = `# Saved Notes & Memory (${new Date().toLocaleDateString()})\n\n`;
    notes.forEach((note, index) => {
      content += `## ${index + 1}. ${note.title}\n`;
      content += `*Category:* ${note.category} | *Tags:* ${note.tags.join(', ')} | *Saved:* ${new Date(note.createdAt).toLocaleString()}\n\n`;
      if (note.summary) content += `**Summary:** ${note.summary}\n\n`;
      if (note.keyPoints && note.keyPoints.length) {
        content += `**Key Points:**\n`;
        note.keyPoints.forEach(p => content += `- ${p}\n`);
        content += `\n`;
      }
      content += `---\n\n`;
    });
  }

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------- CHATS API ----------------

export function getDeviceChats() {
  return parseJson(localStorage.getItem(STORAGE_KEYS.CHATS), []);
}

export function saveDeviceChat(chat) {
  const chats = getDeviceChats();
  const idx = chats.findIndex(c => c.id === chat.id);
  if (idx >= 0) {
    chats[idx] = { ...chats[idx], ...chat, updatedAt: new Date().toISOString() };
  } else {
    chats.unshift({ ...chat, updatedAt: new Date().toISOString() });
  }
  localStorage.setItem(STORAGE_KEYS.CHATS, JSON.stringify(chats));
  return chat;
}

export function deleteDeviceChat(id) {
  const chats = getDeviceChats().filter(c => c.id !== id);
  localStorage.setItem(STORAGE_KEYS.CHATS, JSON.stringify(chats));
  return chats;
}

// ---------------- SETTINGS API ----------------

export function getDeviceSettings() {
  const saved = parseJson(localStorage.getItem(STORAGE_KEYS.SETTINGS), {});
  return { ...DEFAULT_SETTINGS, ...saved };
}

export function saveDeviceSettings(settings) {
  const merged = { ...getDeviceSettings(), ...settings };
  localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(merged));
  return merged;
}
