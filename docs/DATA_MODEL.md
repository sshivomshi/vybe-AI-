# PS3 Data Model

## User
user_id, display_name, created_at, settings.

Settings may include memory enabled, default memory type, cloud sync preference, and offline AI preference.

## Device
device_id, user_id, device_name, platform, app_version, last_seen, created_at.

## Conversation
chat_id, user_id, title, created_at, updated_at, archived.

## Message
message_id, chat_id, role, content, timestamp, metadata.

Roles: USER, ASSISTANT, SYSTEM.

## Memory
memory_id, user_id, title, summary, tags[], memory_type, importance, created_at, updated_at, source_chat_id, source_message_ids[], embedding_model, version, device_id, sync_status, archived, deleted_at.

## Memory Types
DONT_SAVE, QUICK, STANDARD, DETAILED, ARCHIVE_ONLY.

## Embedding
memory_id, model, dimension, vector_id, created_at. The actual vector is stored in Qdrant Edge.

## Sync Operation
operation_id, entity_type, entity_id, operation_type, device_id, base_version, new_version, timestamp, payload, status, retry_count, last_error.

## Conflict
conflict_id, entity_id, local_version, remote_version, local_device_id, remote_device_id, detected_at, conflict_type, resolution_status, resolution_method, resolved_value.

## Conflict Types
VERSION_CONFLICT, CONTENT_CONFLICT, DELETE_UPDATE_CONFLICT, SEMANTIC_CONFLICT.

## Sync Status
LOCAL_ONLY, PENDING, SYNCING, SYNCED, FAILED, CONFLICT.

## Relationships
User → Conversations → Messages.
User → Memories → Embeddings.
User → Devices.
User → Sync Operations.
User → Conflicts.
Memory → source_chat_id → Conversation → source_message_ids → Messages.

## Integrity Rules
IDs must be stable. Versions must follow the synchronization model. Deletions must be synchronization-safe. Source references should remain valid where possible. Embedding metadata must match the vector. Sync operations must be idempotent.
