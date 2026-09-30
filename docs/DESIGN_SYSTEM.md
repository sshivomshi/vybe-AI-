# PS3 Design System

## Design Goal
Create a polished AI interface that clearly communicates intelligence, memory, offline capability, synchronization, and trust.

## Main Areas
- Chat
- Memory Center
- Sync Center
- Conflict Center
- Settings

## Core Screens
### Chat
Conversation list, messages, AI response, memory-used indicator, save-memory action, memory recommendation, connectivity state, AI processing state.

### Memory Center
Memory cards should show title, summary, tags, type, importance, created/updated time, sync state, and source conversation.

Actions: Edit, Archive, Delete, View Source, Change Type, Sync.

### Memory Creation
Show the AI's proposed memory and recommended memory type. User can Don't Save, Edit, or Save.

### Sync Center
Show Online/Offline state, Last Sync, Pending Operations, Failed Operations, Conflicts, and Sync Now.

### Conflict UI
Show local and remote versions with Keep Local, Keep Remote, Merge, and Review options.

## Required Statuses
ONLINE, OFFLINE, SYNCING, SYNCED, SYNC_FAILED, CONFLICT, MEMORY_SAVED, MEMORY_UPDATED, AI_PROCESSING.

Never rely on color alone; use text/icons too.

## Reusable Components
Button, Input, SearchBox, ChatMessage, MemoryCard, MemoryEditor, MemoryTypeSelector, MemoryRecommendation, SyncBadge, ConnectionBadge, ConflictCard, ConflictModal, Timeline, EmptyState, LoadingState, ErrorState, Toast, Modal, Drawer, Tabs.

## UX Principles
- Make AI actions understandable.
- Make memory behavior transparent.
- Make synchronization visible.
- Preserve user control.
- Use progressive disclosure for technical details.
- Prefer useful animation over decorative animation.
- Support keyboard navigation and readable contrast.

## Hackathon Demo UX
The UI should visibly communicate:
ONLINE → MEMORY CREATED → OFFLINE → MEMORY RETRIEVED → LOCAL CHANGE → ONLINE → SYNCING → CONFLICT → RESOLVED.
