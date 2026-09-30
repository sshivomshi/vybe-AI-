# Vybe AI — PS3 Edge Memory

An offline-first AI workspace with **real Qdrant Edge**, local ONNX embeddings, SQLite persistence, a local language model, and a version-aware synchronization authority. The React interface includes Chat, Memory Center, Sync Center, conflict review, and settings.

## Run on this Windows machine

Dependencies, the embedding model, and the optional Qwen language model have already been downloaded into this workspace. Open PowerShell here:

```powershell
.\scripts\start.ps1 -WithModel
```

Open **http://127.0.0.1:8000**. The script starts the model and local development sync authority in hidden processes; the device API stays in the terminal. If those services are already running, start only the device API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

For a second independent device, in another terminal:

```powershell
.\scripts\start.ps1 -DeviceB
```

Open **http://127.0.0.1:8001**. Device A and B have separate SQLite databases, Qdrant shards, device identifiers, and sync cursors. They share only the model runtime/cache and the configured sync authority.

## Fresh installation

Requires Python 3.12 and Node.js 20.19+ (24 tested). The supplied local language-model setup script targets Windows x64. On other platforms, use Ollama or an OpenAI-compatible local inference server.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m scripts.setup_models
.\.venv\Scripts\python.exe -m scripts.configure_local
cd frontend
npm ci
npm run build
cd ..
# Optional, ~1.1 GB download plus CPU runtime:
.\.venv\Scripts\python.exe -m scripts.setup_llm
.\scripts\start.ps1 -WithModel
```

Model installation requires internet once. Normal embedding initialization uses `local_files_only=True`; it never downloads a model during a request. The language-model installer verifies the model's SHA-256 against Hugging Face metadata and the runtime digest when supplied by GitHub. The installed revision is recorded in `data/llm/manifest.json`.

### Alternative: Ollama

Pull your model while connected, then configure `.env`:

```dotenv
PS3_LOCAL_MODEL_URL=http://127.0.0.1:11434/v1
PS3_LOCAL_MODEL=qwen2.5:3b
```

Run Ollama separately and omit `-WithModel`. The app does not pretend to generate answers when no model is available: it preserves the message and reports the limitation. Memory browsing/editing remains available; semantic search requires the installed embedding model.

## Configuration

See `.env.example`. `scripts.configure_local` creates a gitignored `.env` with a random token and never overwrites an existing configuration.

| Setting | Purpose |
| --- | --- |
| `PS3_DATA_DIR` | This device's database and vector shard |
| `PS3_MODEL_CACHE` | Shared local embedding-model cache |
| `PS3_CLOUD_URL` | URL of the sync authority; blank disables cloud sync |
| `PS3_SYNC_TOKEN` | Shared bearer token for one trusted account's devices |
| `PS3_CLOUD_DIR` | Authority's persistent SQLite directory |
| `PS3_LOCAL_MODEL_URL`, `PS3_LOCAL_MODEL` | OpenAI-compatible local inference |
| `PS3_CLOUD_MODEL_URL`, `PS3_CLOUD_MODEL`, `PS3_CLOUD_API_KEY` | Optional cloud inference, configured only on the backend |

The app prefers configured cloud inference, falling back to the local model on request failure. Retrieved local-only memories force local inference; conversations that use them remain pinned to local inference. Approving a source-linked local-only memory also pins its source conversation. This cannot retract content already sent before a memory was designated local-only.

### API plugins

Open **AI connections** in the sidebar (also linked from Settings) to connect an **OpenAI-compatible Chat Completions API** without editing `.env`:

1. Choose **Connect a service** and enter a name, API base URL, model ID, and optional API key. Include the provider's API prefix (such as `/v1`), but omit `/chat/completions`.
2. Save the connection. Saving alone does not select it for chat or make an outbound call.
3. **Test connection** sends a short synthetic prompt to that model. It does not send your messages or memories; the provider may bill for this small request. Test success verifies a text response, not every provider's structured-output capabilities.
4. **Use for chat** selects that enabled provider as the default for chat and memory extraction. Other saved plugins receive no traffic. If this provider fails, inference falls back directly to the configured local model. A provider that cannot handle structured memory output can still answer chat while extraction falls back locally.
5. Edit, enable/disable, or delete connections at any time. Disabling the default clears the selection. With no selected plugin, the existing `.env` routing applies (configured cloud provider, then local model).

HTTPS is required for remote endpoints; HTTP is permitted for explicit loopback APIs such as `http://127.0.0.1:8081/v1`. API plugins support the Chat Completions protocol; arbitrary REST tools and provider-specific noncompatible protocols are outside this feature.

API keys are encrypted with Fernet in the device's SQLite plugin table. The backend encryption key is stored in `.plugin-key` beside that device's database, with owner-only file permissions where supported by the OS. Keys are never returned to the browser, included in model prompts, or synchronized. Protect the complete device directory with OS access controls; someone with both the database and encryption-key file can decrypt credentials. Back up those files together. If the key file is lost, restore it or clear all saved plugin API keys before adding replacements.

When editing, a blank API-key field preserves the saved credential. **Changing the base URL clears the old key unless you explicitly enter a replacement**, so it is never silently forwarded to a different destination. Test errors contain no provider response bodies or credentials. Chats containing local-only memory bypass all API plugins, including plugins configured with loopback addresses.

**Connection badges describe reachability of the configured synchronization service.** A loopback authority can remain reachable when Wi-Fi is disabled. For an actual internet-disconnection demonstration, deploy the authority on another host, or stop the local authority to demonstrate transport loss. The badge is not a claim that the whole internet is reachable.

## Everyday use

### Constellation and chat capture

Open **Constellation** in the sidebar to explore captured conversations and saved memories in a spatial view. Drag to orbit, scroll or pinch to zoom, and select a node to focus. The node selector supports keyboard access. Reset view restores the whole composition; Collapse hides message branches.

The **Save chat** switch in Chat is off by default for each new conversation. Enabling it captures the current conversation and automatically captures subsequent messages. Disabling it stops new capture while retaining saved nodes. Enabling it again includes the conversation's existing messages. Capture is persisted locally, survives restarts, and does not send captured transcripts to the synchronization service or add them to AI retrieval. Conversations and their messages form the hierarchy; source-linked memories connect to their source conversation. The view shows up to twelve captured messages per conversation, with a rendering limit for smaller screens; older captured data remains stored.

The main menu has three sections: **Chat**, **Saved memories**, and **Settings**. Start by typing a message, or choose a writing, explanation, or planning prompt. The optional **How to use this** guide explains the chat controls.

To keep a useful detail, review a suggestion in chat or choose **Saved memories → New memory**. A title and the memory text are enough; tags, length, and priority are under **More options**. **Keep on this device only** remains visible. Archived memories are kept for reference and are not used in replies.

Optional services are under **Settings → Manage AI connections**. Sync status and any competing changes are available through **Settings → View sync status**. Model information, storage figures, and sync operation history are available in the collapsed advanced sections.

## Architecture

```text
React browser UI, served from the local device
  └─ FastAPI device API (loopback only)
      ├─ SQLite: memories, versions, chats, messages, preferences, queue, conflicts
      ├─ FastEmbed / ONNX: locally cached BGE-small, 384 dimensions
      ├─ Qdrant Edge: actual embedded EdgeShard, cosine similarity, tag filters
      ├─ AI routing: cloud API → local llama.cpp / Ollama fallback
      └─ Sync worker: durable outbox → authenticated HTTP authority
                              ← cursor-based remote change feed
```

Code boundaries: `storage.py` (transactions), `vectors.py` (embeddings/index), `memory.py` (memory lifecycle), `ai.py` (model adapters/extraction), `sync.py` (retries/conflicts), `cloud.py` (authority), `main.py` (API), `frontend/src` (interface). Specifications are preserved in `docs/`.

### Memory behavior

- Conversation messages are stored locally; they are not automatically indexed or synchronized.
- AI proposes compact memories. **Review/edit/save** is required to index them; **Don't save** dismisses a suggestion.
- Quick, Standard, Detailed, and Archive Only are explicit modes. The editor's **More options → Help me rewrite this** produces a reviewable AI rewrite; changing a mode alone does not destructively shorten text.
- Exact duplicate summaries with the same privacy/mode/archive state reuse the existing memory. Semantic related-memory detection proposes an update, with the prior title, tags and privacy retained. The user approves the evolution.
- Updates carry optimistic version checks. History retains prior values and source references. Source conversations remain on their originating device; another device reports their unavailability rather than fabricating them.
- Archive Only, archived, and deleted memories are excluded from semantic retrieval. Deletion leaves synchronization tombstones and version history; this is logical deletion, not secure disk erasure.
- SQLite is authoritative. Index failure preserves the local memory and queue, marks the index dirty, and allows repair/rebuild on search or restart. A model/dimension mismatch is rejected rather than mixed silently.

### Synchronization behavior

Local memory and outbox operations commit in the **same SQLite transaction**. Each operation has a UUID, device ID, base/new version, timestamp, payload, state, retry count, next retry, and error. The authority atomically commits memory, change feed, and idempotency receipt. Reusing an operation ID with different data is rejected.

The worker runs every 10 seconds, processes operations in order, uses bounded exponential retry delays, and supports manual retry. An interrupted in-flight operation becomes pending on restart. A lost response after a server commit is safely retried against its receipt. Pull cursors and downloaded memory updates commit together.

Competing base versions create persistent conflicts. Keep Local and Merge create a new operation against the remote version. Keep Remote adopts the remote value. Earlier queued operations are marked superseded, and a further race at the authority creates another conflict rather than overwriting data.

Local-only memories never enter the queue. A previously synchronized record cannot be switched to local-only in place: first delete it across devices, then create a local-only copy.

## Cloud deployment

The included authority is a **real persistent HTTP service**, currently configured as a local development deployment. A public cloud host has not been provisioned.

```powershell
docker compose up --build -d
```

`Dockerfile.cloud` and `compose.yaml` mount persistent `/data` and run as a non-root user. Set a strong `PS3_SYNC_TOKEN` and use the same token on your own devices. On a remote host, put this service behind an HTTPS reverse proxy, retain its volume, and set each device's `PS3_CLOUD_URL` to that HTTPS URL. The compose port is intentionally bound to loopback for use with a host reverse proxy. Do not expose the device API itself on the internet.

This authority is single-account, designed for trusted devices sharing one bearer token. Multi-user identity, token rotation, end-to-end encryption, quotas, and large-scale authority operation are not implemented. Local databases are plaintext; use OS disk encryption where needed.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.benchmark
# Requires the local LLM on :8081:
.\.venv\Scripts\python.exe -m scripts.verify_demo
# Requires the authority configured in .env:
.\.venv\Scripts\python.exe -m scripts.verify_sync_http
# Requires the device app on :8000 and Microsoft Edge installed:
cd frontend
npx playwright test
```

The offline demo verifier blocks **all non-loopback socket connections**. It uses the real local model and real Qdrant Edge, saves a suggestion, retrieves by meaning, evolves the record, asks about it from a fresh conversation, and verifies queued offline writes. This is not a canned model response or substituted vector store.

Measured reports: `docs/BENCHMARK.json`, `docs/OFFLINE_DEMO_RESULT.json`, and `docs/SYNC_HTTP_RESULT.json`. The benchmark is deliberately scoped: one CNN memory, 20 repeated retrievals per depth. It is not a large-corpus relevance evaluation or a claim about general LLM faithfulness.

See `docs/DEMO_RUNBOOK.md` for the judge walkthrough and `docs/IMPLEMENTATION_AUDIT.md` for verified scope and limitations.

## Developer commands

```powershell
# Terminal 1, API
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# Terminal 2, frontend hot reload
cd frontend
npm run dev
```

Local API docs: `http://127.0.0.1:8000/docs`. Secrets never enter the frontend bundle. The backend rejects cross-origin writes and unexpected hostnames. Access logs should be disabled or redacted when logging search query strings is inappropriate; conversation bodies are not deliberately logged.

## References

Implementation uses the official [Qdrant Edge API](https://qdrant.tech/documentation/edge/edge-api/), [FastEmbed](https://github.com/qdrant/fastembed), [llama.cpp](https://github.com/ggml-org/llama.cpp), and [Qwen's official GGUF model](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF). Qdrant Edge is an evolving API; the tested dependency versions are captured in `requirements.lock.txt` and `frontend/package-lock.json`.

## Android app: internet chat and phone storage

The Android app uses a midnight/lavender interface and direct HTTPS inference. Conversations and bookmarked replies are stored on the phone; API credentials are encrypted with Android Keystore. There is no API-key form in the app. The debug app can be provisioned over authorized USB with `scripts/verify_gemini_android.py --from-env` and the provisioning instrumentation. Vybe AI and Vybe AI Dev have separate storage. Neither currently integrates the PC memory or synchronization engine.

See [current gap-closure report](docs/GAP_CLOSURE.md) for fresh verification, deployment preparation, and remaining limitations.

## Android Studio and live UI editing

Open this repository root in Android Studio. See [Android Studio development](docs/ANDROID_STUDIO.md) for Run/Debug, USB forwarding, and live React/CSS updates.

