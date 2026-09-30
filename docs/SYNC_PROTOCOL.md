# PS3 Synchronization Protocol

## Goal
Synchronize local memory with cloud state while supporting offline operation, intermittent connectivity, multiple devices, retries, evolving memories, and conflicts.

## Principle
Offline changes are persisted locally and queued. They are synchronized when connectivity returns.

## Sync Operation
operation_id, entity_type, entity_id, operation, device_id, base_version, new_version, timestamp, payload, status, retry_count.

## Operation Types
CREATE, UPDATE, ARCHIVE, RESTORE, DELETE, MERGE.

## Lifecycle
PENDING → SYNCING → SUCCESS.
Failure: SYNCING → FAILED → RETRY.
Conflict: SYNCING → CONFLICT → RESOLUTION → SYNCED.

## Idempotency
Every operation has a unique operation ID. Repeated delivery must not create duplicate state.

## Retry
Use retry count, exponential backoff, maximum delay, network-state checks, and manual retry. Do not retry indefinitely at high frequency.

## Conflict Detection
Compare memory ID, version/base version, device ID, timestamp, and content. Two independent updates from the same base version indicate competing changes.

## Conflict Resolution
Possible strategies:
1. User selection: Keep Local / Keep Remote.
2. Semantic merge: AI proposes a combined memory for user review.
3. Deterministic version rule where safely applicable.

Do not silently apply last-write-wins to every meaningful conflict.

## Semantic Conflict
Example:
A: User needs to revise backpropagation.
B: User completed backpropagation.
These are semantically contradictory and should be surfaced rather than silently discarded.

## Reconnection
Internet returns → detect connectivity → start sync worker → process pending operations → check versions → detect conflicts → resolve → update local state → mark synced.

## Reliability Tests
Test network loss during upload/download, application restart during sync, duplicate operations, out-of-order operations, cloud failure, conflicts, and multi-device changes.

## UI
Expose Online/Offline, Last Sync, Pending Operations, Sync Progress, Failures, and Conflicts.
