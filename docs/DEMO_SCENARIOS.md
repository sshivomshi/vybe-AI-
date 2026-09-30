# PS3 Hackathon Demo Scenarios

## Demo Objective
Prove the complete PS3 workflow:
AI → Memory → Offline → Semantic Retrieval → Local Changes → Reconnect → Cloud Sync → Conflict → Resolution → Updated AI Context.

## Demo 1 — Create Memory
Online user says:
"I am preparing CNN for my machine learning exam. I understand convolution and pooling but still need to revise backpropagation."

AI proposes:
Title: CNN Study Progress.
Summary: Understands convolution and pooling; needs revision of backpropagation.
User saves it.

## Demo 2 — Show Local Memory
Open Memory Center and show title, type, tags, status, and source conversation.

## Demo 3 — Disable Internet
Turn network OFF. Show OFFLINE state.

## Demo 4 — Offline Semantic Search
Ask:
"What was I struggling with in CNN?"
Expected: retrieve the CNN memory without requiring the exact word "backpropagation".

## Demo 5 — Offline Memory Update
Tell the AI:
"I have now completed backpropagation."
AI proposes an updated memory. User approves.

## Demo 6 — Pending Sync
Show Sync Center:
OFFLINE, Pending Operations: actual measured count.

## Demo 7 — Reconnect
Turn network ON:
ONLINE → SYNCING → SYNCED.

## Demo 8 — Create Conflict
Device A and Device B independently modify the same memory. Synchronize and show CONFLICT DETECTED.

## Demo 9 — Resolve Conflict
Show local and remote versions. Demonstrate Keep Local, Keep Remote, or Merge. If semantic merge is implemented, show the AI proposal before confirmation.

## Demo 10 — Memory Evolution
Show memory versions from initial learning through updated progress.

## Demo 11 — Memory Compression
Show original conversation versus compact active memory. Use measured storage values; never invent benchmark numbers.

## Demo 12 — User Memory Control
Demonstrate Don't Save, Quick, Standard, Detailed, and Archive Only.

## Demo 13 — Memory Center
Show actual counts for active memories, pending sync, conflicts, local storage, and cloud state.

## Demo 14 — Failure Recovery
Disconnect during synchronization. Show that local changes remain safe. Reconnect and retry.

## Final Judge Flow
1. Explain problem.
2. Chat normally.
3. Save compact memory.
4. Show Memory Center.
5. Disable Internet.
6. Retrieve memory semantically.
7. Create/update memory offline.
8. Show pending sync.
9. Reconnect.
10. Show sync.
11. Demonstrate conflict.
12. Resolve conflict.
13. Show evolved memory.
14. Show measured metrics.
15. Explain architecture.

## Technical Talking Points
- Qdrant Edge provides local semantic retrieval.
- Offline-first design allows core memory operations without continuous connectivity.
- Evolving memory updates useful context instead of blindly accumulating duplicates.
- Sync queues local changes until connectivity returns.
- Conflict handling prevents silent loss of competing updates.
- Edge-to-cloud workflow connects local AI/memory operation with cloud synchronization.
- User controls what is remembered and synchronized.

## Pre-Demo Tests
Test Wi-Fi disabled, restart while offline, sync failure, duplicate operations, conflict creation, conflict resolution, memory deletion, empty states, slow network, local model availability, and cloud failure.
