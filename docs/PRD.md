# PS3 — AI-Powered Edge Memory & Intelligence Platform

## Product Vision
Build an offline-first AI application with local semantic memory, offline retrieval, cloud synchronization, evolving memory, conflict handling, and a user-facing memory/sync experience.

## Core Workflow
User Conversation → Important Information Detection → Compact Memory → Embedding → Qdrant Edge → Local Semantic Retrieval → AI Response → Memory Evolution → Local/Cloud Sync.

## Core Features
1. AI chat with memory-aware responses.
2. Intelligent memory extraction from conversations.
3. User-controlled memory modes: Don't Save, Quick, Standard, Detailed, Archive Only.
4. Semantic retrieval using embeddings and Qdrant Edge.
5. Offline memory search and local memory operations.
6. Local/cloud synchronization.
7. Intermittent-connectivity handling.
8. Evolving memories instead of unnecessary duplicates.
9. Conflict detection and resolution.
10. Memory Center and Sync Center.
11. Source traceability from memory to conversation.
12. Edge-to-cloud AI workflow.

## Memory Pipeline
Conversation → Candidate Detection → Importance → Memory Type → Fact Extraction → Compression → Validation → Duplicate Check → Create/Update/Merge → Embedding → Qdrant Edge.

## Offline Requirements
When offline, the user must still be able to search memories, create/update memories, and continue core local operations. Cloud operations are queued.

## Synchronization Requirements
Persist local operations, retry failed operations, use unique operation IDs, preserve versions/device metadata, and synchronize when connectivity returns.

## Conflict Requirements
Detect competing updates, preserve relevant versions, and support deterministic or user-assisted resolution. Do not silently destroy meaningful data.

## Memory Record
memory_id, user_id, title, summary, tags, importance, memory_type, timestamps, source_chat_id, source_message_ids, embedding_model, version, device_id, sync_status, archived.

## MVP
Chat, memory extraction, approval/editing, embeddings, Qdrant Edge, semantic retrieval, offline mode, sync queue, cloud sync, basic conflict detection, Memory Center, Sync Center.

## Success Demo
Create memory online → disable Internet → retrieve semantically → create/update offline → reconnect → sync → create conflict → resolve conflict → show updated AI context.

## Non-Functional Requirements
Low-latency local retrieval, reliable offline persistence, idempotent sync, clear connectivity state, traceability, privacy, and testability.

## Scope Rule
Prioritize a reliable end-to-end PS3 vertical slice over unrelated features.
