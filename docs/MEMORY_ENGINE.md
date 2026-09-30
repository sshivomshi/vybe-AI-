# PS3 Memory Engine

## Purpose
Convert useful conversational information into compact, structured, searchable memories.

Objective: maximize useful information per unit of storage while preserving enough context for accurate retrieval.

## Lifecycle
Conversation → Candidate Detection → Importance → Memory Type → Fact Extraction → Compression → Validation → Duplicate Detection → Create/Update/Merge → Embedding → Qdrant Edge.

## Memory Modes
- DONT_SAVE
- QUICK
- STANDARD
- DETAILED
- ARCHIVE_ONLY

## Suggested Memory
memory_id, user_id, title, summary, tags, memory_type, importance, created_at, updated_at, source_chat_id, source_message_ids, embedding_model, version, device_id, sync_status, archived.

## Compression
Remove greetings, filler, repetition, and irrelevant wording. Preserve meaning, constraints, current state, useful relationships, and traceability.

## Validation
Check whether the memory is understandable, supported by the source, sufficiently contextualized, non-duplicate, non-contradictory, and appropriately sized.

## Duplicate Detection
New candidate → embedding → semantic search → related memory?
- No → create.
- Yes → compare → update/merge when appropriate.

## Evolving Memory
Example:
v1: User is learning CNN.
v2: User understands convolution and pooling.
v3: User completed CNN fundamentals and is revising backpropagation.

Prefer updating logical memories instead of accumulating duplicates.

## Retrieval
Query → embedding → Qdrant Edge → Top-K → metadata filtering → optional reranking → context builder → LLM.

## User Control
Users must be able to inspect, edit, archive, delete, and control synchronization of memories.

## Metrics
Track memory size, active memory count, duplicate rate, retrieval latency, relevance, update frequency, compression ratio, and user correction rate.

## Benchmark
Compare raw conversations against Quick, Standard, and Detailed memories. Measure storage, retrieval relevance, faithfulness, context coverage, and AI answer quality. Do not assume a fixed word limit is optimal without testing.
