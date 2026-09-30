# Codex / AI Agent Instructions

## Mission
Build a real PS3 offline-first AI memory system. Do not fake Qdrant Edge, offline mode, synchronization, or conflict handling.

## Non-Negotiable Requirements
- Use Qdrant Edge for local semantic memory/retrieval.
- Support low-latency local search without network access.
- Support local/cloud synchronization.
- Handle intermittent connectivity.
- Support evolving memory.
- Detect and handle conflicts.
- Provide memory and synchronization UI.
- Demonstrate an edge-to-cloud AI workflow.

## Architecture Rules
Separate:
Frontend → API/Application Layer → Chat Engine / Memory Engine / Sync Engine / Conflict Engine → Local Storage/Qdrant Edge → Cloud.

Keep business logic out of UI components.

## Offline Rules
- Local memory operations must continue offline.
- Persist pending cloud operations.
- Retry when connectivity returns.
- Never simulate offline mode with hardcoded responses.
- Never require cloud access for local semantic retrieval.

## Memory Rules
Do not make full raw conversations the active memory by default.
Every memory needs a stable ID, version, timestamps, device ID, source reference, and sync state.
Allow user approval, editing, archiving, and deletion.
Avoid duplicate memories when an existing memory can be updated.

## Sync Rules
Every operation needs operation ID, entity ID, operation type, device ID, version information, timestamp, status, and retry metadata.
Synchronization must be idempotent.

## Conflict Rules
Never silently overwrite meaningful competing user data.
Preserve enough metadata to explain conflicts.
Support documented automatic rules and user-assisted/semantic merge where appropriate.

## Security
Never commit secrets. Use environment variables. Never expose server-side API keys to the frontend. Avoid unnecessary sensitive logging.

## Testing
Test memory creation/retrieval/update/delete, Qdrant integration, offline queue, retry, idempotent sync, conflict detection/resolution, API validation, and the complete offline→online flow.

## Development Order
Foundation → Data Models → Local Storage → Qdrant Edge → Embeddings → Memory Engine → Retrieval → Chat → Offline State → Sync Queue → Cloud Sync → Conflicts → UI → Testing → Benchmarking → Polish.

## Codex Workflow
Inspect existing code before changing it. Make small changes. Run tests. Fix regressions. Update documentation. Do not rewrite unrelated working code.
