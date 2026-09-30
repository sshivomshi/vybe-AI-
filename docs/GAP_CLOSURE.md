# PS3 gap closure — 2026-09-30

## Verified this session
- 55 backend tests passed, including retry receipt replay, recovery after model failure, and rejection of request-ID reuse with changed content.
- Website preserves failed-message drafts and reuses request IDs. Successful response receipts are committed with assistant messages. Single-process generation is serialized to avoid concurrent duplicate retries. This is not a multi-worker locking solution.
- Status distinguishes local backend, sync scope/state, and the last successful AI route. The last route is historical evidence, not an AI health probe.
- Cloud read timeout defaults to 20 seconds, local read timeout to 90 seconds. These are per-call inactivity timeouts, not an end-to-end deadline; extraction can add calls.
- Offline demo rerun with external sockets blocked: real local AI, semantic retrieval, memory evolution, fresh-chat recall, two queued operations. 45.13 seconds total.
- Real HTTP sync rerun: two independent local device stores, conflict, resolution, deletion propagation.
- Retrieval evaluation: 100 synthetic records, 10 labeled queries, top-1 10/10; topic medians 15–21 ms. Ninety distractors are templated inventory entries. This is not broad real-world relevance validation.

## Deployment preparation
compose.remote.yaml and Caddyfile provide a separate HTTPS authority deployment. On an authorized Docker host, set SYNC_DOMAIN and PS3_SYNC_TOKEN, point DNS to the host, allow ports 80/443, and run docker compose -f compose.remote.yaml up -d --build. Set each local device backend PS3_CLOUD_URL to that HTTPS hostname and the same private token. Keep the device API bound to loopback. These deployment files have not been executed remotely.

## Still open — do not claim complete compliance
- Hosting account/domain and actual remote deployment; independent physical-device sync and interrupted-network verification.
- Android memory integration, history sync and remote source conversation access.
- Multi-user authentication/isolation; authority remains single-account with a shared token.
- Standalone browser/phone offline semantic processing; the website requires its local Python backend and models.
- Broad extraction/evolution faithfulness tests. The latest demo update recalled completion but omitted the original exam goal; user review is still required.
- Automatic semantic contradiction detection across different records.
- End-to-end encryption, secure erasure, and full backup/restore tooling.
- Streaming/progress per generation stage and a strict overall generation deadline.
- Full browser regression suite after recovery changes and crash/concurrency stress testing.

The updated UI does not change these architecture limits. No hosting, sign-in, or mobile synchronization has been fabricated.
