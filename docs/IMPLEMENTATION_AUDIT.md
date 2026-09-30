# Historical implementation audit

For the current 2026-09-30 results and outstanding work, see [GAP_CLOSURE.md](GAP_CLOSURE.md). Statements below about missing cloud API credentials and the old Android UI are historical.

# PS3 implementation audit

Built from an empty workspace. The supplied documents are preserved under `docs/`; they were used as project requirements, not executed as commands. No fake Qdrant replacement or canned AI response is used by the running application.

## Implemented and exercised

| Requirement | Implementation / evidence |
| --- | --- |
| Real Qdrant Edge | `qdrant-edge-py 0.8.0`, embedded `EdgeShard`; insertion, filtering, query, deletion, persistence and reopening exercised |
| Local semantic embeddings | FastEmbed BGE-small ONNX, 384 dimensions; installed model loaded without external network |
| Offline CRUD/search/restart | SQLite + Qdrant tests deny socket connections, create data, reopen it and retrieve by meaning |
| AI chat | Real local Qwen2.5 1.5B GGUF through llama.cpp; persisted conversation history and retrieved-memory provenance |
| Cloud/local AI routing | Backend OpenAI-compatible adapter; fallback and local-only routing covered by tests; live cloud inference not configured |
| API provider plugins | UI-managed OpenAI-compatible connections, encrypted device-local keys, explicit default selection, synthetic connection test, edit/disable/delete and direct local fallback |
| Extraction and approval | Schema-constrained candidate extraction; validation; editable approval, permanent dismissal, selectable depth, optional AI refinement |
| Compact/evolving memory | Exact duplicate reuse; related-memory proposal; dedicated evolution pass; user-approved versioned update |
| Offline AI evolution | Real local model recalled both initial and updated memory with external sockets blocked; final question uses a fresh conversation |
| Memory Center | Browser-tested creation, meaning-based retrieval, editing, archiving, restoring and deletion; detail/history/source view |
| Persistent sync queue | Atomic memory+operation transactions; retries/backoff; in-flight restart recovery; manual retry |
| Idempotent authority | Durable receipts and atomic version checks; lost response after commit safely retried |
| Multi-device conflicts | Independent devices; local/remote/merge resolution; delete/update conflict; superseded queue entries preserved |
| Real HTTP sync | Running authority exercised over HTTP: create, two-device conflict, resolution, and propagated deletion |
| Sync Center | Real queue states, retry counts, errors, last sync, pending count and conflicts |
| Privacy/security | Backend-only credentials; random local token; authority authentication; input validation; local Host/Origin controls; local-only exclusions |
| Responsive UI | Production React build; real-browser desktop/mobile checks and screenshots; keyboard-accessible editor |
| Measured performance | `BENCHMARK.json`: 20 queries per depth, about 16 ms median on a one-memory fixture; no broad relevance claims |

## Verification commands and artifacts

- `python -m pytest -q`: **54 passed**; 22 core/real-index tests and 32 API-plugin tests covering credentials, endpoint validation, default selection, fallback, and connection-test races.
- Browser checks: **5 passed** across the existing memory lifecycle/responsive tests and 3 API-plugin tests. Plugin selection/provider-error cases use explicit API mocks; persistence uses the real backend. The plugin suite was rerun after fixing keyboard dismissal following a save error.
- `python -m scripts.verify_demo`: actual local LLM + actual vector engine, all external socket connections blocked. `OFFLINE_DEMO_RESULT.json` records the successful run.
- `python -m scripts.verify_sync_http`: actual HTTP transport to the running authority. `SYNC_HTTP_RESULT.json` records the successful run.
- `npm run build`: production bundle with all assets served locally.
- `python -m scripts.benchmark`: measured byte counts, vector-value size, retrieval median and p95; `BENCHMARK.json`.

The API-plugin connection check was additionally exercised against the running local llama.cpp server through `/api/plugins/{id}/test` and returned a valid model response. Its temporary connection was deleted afterward. No external provider credential was supplied or live-tested.

The latest successful offline verification took **69.63 seconds for the full multi-message scenario**, including extraction and evolution. This is not per-query vector latency. The semantic score for the initial paraphrased query was **0.626**. The final record was version 2, with two pending operations while the authority was unavailable.

## Scope and remaining limitations

1. **Public cloud hosting has not been provisioned.** The actual persistent authority currently runs locally. Docker deployment files are supplied; the local Docker daemon was unavailable, so the image itself was not executed here. Remote HTTPS/TLS and credentials must be configured on the selected host.
2. **Connection state measures the configured authority's reachability.** A local authority remains reachable without Wi-Fi. The automated offline verifier blocks external sockets and points sync at an unavailable endpoint; it does not claim to have toggled the user's physical network adapter.
3. **Cloud LLM inference is not live-tested.** No cloud API key was supplied. Real local inference, simulated transport-failure routing tests, and real offline generation were verified separately.
4. **Model proposals require review.** The 1.5B CPU model can omit context or make imperfect summaries. Structured output fixes schema errors, not factual correctness. The evolution path retains history and exposes an explicit temporal draft if consolidation is unchanged; nothing is silently approved.
5. Responses are returned after completion rather than token-streamed. AI processing and failure states are explicit. Small-model inference may take tens of seconds on this hardware.
6. The sync authority is single-account with a shared token, not a multi-tenant identity service. No end-to-end encryption, key rotation UI, quotas or enterprise audit system is claimed.
7. Archive/delete controls remove content from active retrieval. Tombstones, history and source chats remain for traceability and conflict safety; deletion is not secure disk erasure. Full chat data is not synchronized.
8. The benchmark uses one memory per depth and one paraphrased query, repeated 20 times. It measures storage and latency, not large-scale retrieval relevance, formal faithfulness, or general response quality. Detailed memory can be larger than this short source; the report shows that honestly.
9. The UI is a local web application served by a running device backend. It does not claim a hosted PWA can access a stopped local process. After restarting the local services, the interface and memory work without internet.
10. Conflict merging is a user-reviewed combined draft. The app does not claim autonomous semantic conflict adjudication or automatic detection of every contradiction across unrelated memory IDs.

The verified deliverable is an end-to-end PS3 local-first application with a real deployable sync service, not a claim that unspecified cloud infrastructure has already been deployed.
