# PS3 System Architecture

## High-Level Architecture

Frontend (React/Next.js)
→ FastAPI/Application Layer
→ Chat Engine / Memory Engine / Sync Engine / Conflict Engine
→ Local Storage + Qdrant Edge
→ Cloud Synchronization Services.

## Frontend
Responsible for chat, memory management, sync status, conflicts, connectivity status, and settings. Never store server credentials in the frontend.

## Backend
Recommended: Python, FastAPI, Pydantic.
Responsible for orchestration, embeddings, Qdrant repository, sync, conflict handling, and cloud communication.

## Chat Pipeline
User Query → Connectivity Check → Local Memory Retrieval → Context Builder → Local/Cloud LLM → Response → Memory Candidate Detection.

## Memory Pipeline
Conversation → Candidate Detection → Importance → Memory Type → Fact Extraction → Compression → Validation → Duplicate Check → Create/Update/Merge → Embedding → Qdrant Edge.

## Retrieval Pipeline
Query → Embedding → Qdrant Edge Search → Top-K Candidates → Metadata Filtering → Optional Reranking → Context Builder → LLM.

## Offline State
ONLINE → connection lost → OFFLINE → connection restored → SYNCING → SYNCED or SYNC_FAILED.

## Sync Pipeline
Local Change → Sync Operation → Persistent Queue → Connectivity Check → Upload → Version Check → Conflict Detection → Resolution → Local State Update → Synced.

## Local Layer
Qdrant Edge handles local vector retrieval. Additional local persistence may store conversations, sync operations, device metadata, memory state, and settings. Do not put all application state into the vector database.

## Cloud Layer
Provide persistent synchronized storage, cross-device synchronization, backup/restore where implemented, and optional cloud indexing. Cloud must not be required for local semantic retrieval.

## Suggested Backend Structure
backend/
- api/
- core/
- models/
- services/chat/
- services/memory/
- services/embeddings/
- services/retrieval/
- services/sync/
- services/conflicts/
- repositories/local/
- repositories/cloud/
- workers/
- tests/

## Suggested Frontend Structure
frontend/
- pages/
- components/chat/
- components/memory/
- components/sync/
- components/conflicts/
- hooks/
- services/
- stores/
- types/
- tests/

## Observability
Measure retrieval latency, memory creation latency, sync latency, sync failures, conflicts, pending operations, offline duration, and local storage size. Avoid logging sensitive conversation contents by default.
