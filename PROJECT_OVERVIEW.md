# Vybe AI — Offline AI Chatbot

## Overview

Vybe AI is an offline-first AI workspace that combines chat with persistent, searchable memories. It runs a local device API and browser interface, supports local AI inference, and can optionally connect to cloud AI providers and a synchronization service.

## Main features

- **Local chat:** Use a configured local language model after downloading the required models and runtime.
- **Saved memories:** Review AI memory suggestions, create and edit memories, and archive or delete them.
- **Semantic search:** Search saved memories using local ONNX embeddings and Qdrant Edge.
- **Memory history:** Track versions and retain references to source conversations.
- **Optional synchronization:** Queue changes locally and retry synchronization when the configured service becomes reachable.
- **Conflict review:** Resolve competing edits by keeping local values, adopting remote values, or merging changes.
- **AI connections:** Configure compatible AI services through the interface.
- **Device-only memories:** Keep selected memories out of synchronization and use local inference for conversations that retrieve them.

## Technology

| Component | Technology |
| --- | --- |
| Browser interface | React |
| Device API | Python / FastAPI |
| Persistent storage | SQLite |
| Semantic index | Qdrant Edge |
| Local embeddings | FastEmbed / ONNX, BGE-small |
| Local inference | llama.cpp or Ollama with a compatible API |
| Synchronization | Authenticated HTTP service with a durable outbox and change feed |

## How it works

1. The user chats with a configured AI model.
2. Useful details can be proposed as compact memories.
3. The user reviews and saves memories before they become searchable.
4. Saved memories are stored locally and indexed for semantic retrieval.
5. Eligible changes enter a persistent synchronization queue.
6. When the synchronization service is reachable, devices exchange updates and surface competing edits for review.

## Run the prepared Windows workspace

From PowerShell in the project directory:

```powershell
.\scripts\start.ps1 -WithModel
```

Open `http://127.0.0.1:8000` in a browser.

For a fresh installation, follow the full setup instructions in the project's `README.md`. Initial dependency and model downloads require internet access. Offline chat requires a working local model; offline semantic search requires the installed embedding model.

## Current scope and limitations

- The synchronization authority is documented as a local development deployment; a public cloud host has not been provisioned.
- Synchronization is designed for trusted devices belonging to one account and sharing a bearer token.
- Multi-user identity and end-to-end encryption are not implemented.
- Local databases are plaintext.
- Conversations are stored locally and are not automatically indexed or synchronized.
- A reachable local synchronization service does not prove that the internet is reachable.

## Project documentation

The repository includes setup instructions, architecture and data-model documents, synchronization specifications, demo guides, Android documentation, and verification scripts.

This overview summarizes the existing project documentation. It does not represent a new test or deployment verification.
