# Reproducible PS3 demonstration

## Prepare

1. Run `scripts/start.ps1 -WithModel` from the project root. Open `http://127.0.0.1:8000`.
2. Start a second device using `scripts/start.ps1 -DeviceB`. Open `http://127.0.0.1:8001` in another tab.
3. Verify Settings says Qdrant Edge is ready. The local model must be running at port 8081; first responses may take tens of seconds on CPU.
4. For the offline portion, stop the local sync authority, or use a remote authority and disable the network. Do not disable loopback access to the local UI/model. Do not treat a reachable loopback authority as an internet-connectivity test.

## Judge flow

1. In Chat, send: “I am preparing CNN for my machine learning exam. I understand convolution and pooling but still need to revise backpropagation.”
2. Explain the **local model** label. Cloud inference is optional and only shown when configured and actually used.
3. Review the suggested memory. Edit any imperfect extraction, choose Standard, and save.
4. Open Memory Center. Show its title, tags, version, importance, sync badge and source conversation via its detail view.
5. Press Sync Now on A, then B. The same record appears on both devices.
6. Stop the sync authority (or disconnect from a remote authority). After a sync check, Sync Center reports OFFLINE.
7. Search “What topic was I struggling with in CNN?” in Memory Center. The answer comes from local ONNX embeddings and Qdrant Edge. Chat can also answer with the local model and show the memory used.
8. On A, say “I have now completed backpropagation.” Review the proposed update carefully and save it against the existing memory. Show the incremented version and actual pending operation count.
9. While still disconnected, edit that same memory on B to “I still need another backpropagation revision session.” Both edits share the same base version.
10. Restart the authority/reconnect. Sync A first, then B. B detects a conflict; no side is silently overwritten.
11. Open Conflicts. Show both device IDs, versions and summaries. Choose Keep Local, Keep Remote, or Review & Merge. Merge opens an editable combined draft; it is not represented as an autonomous semantic resolution.
12. Sync B, then A. Confirm the resolved content appears on both devices.
13. Start a **new chat** and ask for current CNN progress. Inspect the retrieved memory to verify the answer uses the resolved state rather than old chat history.
14. Show history in memory details. Show local storage, compact-summary bytes, estimated vector-value bytes, last sync, and measured query latency.
15. Demonstrate Don't Save on a fresh suggestion, Quick/Standard/Detailed plus optional refinement, Archive Only, restore, local-only creation, and deletion propagation.

## Restart and failure recovery

With the authority unavailable, edit a record and close/restart the device server with the same `PS3_DATA_DIR`. Its local data and queue survive. Reconnect and sync. Automated tests additionally cover the harder case where the server commits a write but its response is lost.

The two-device local demo uses real databases and real HTTP. It demonstrates the protocol but is not itself proof of a public cloud deployment. Deploy the authority remotely before claiming an internet-to-cloud demonstration.
