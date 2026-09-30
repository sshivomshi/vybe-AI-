# Android internet client verification

Verified on 2026-09-29, OnePlus 6T / Android 11.

- Gradle debug app and instrumentation APK builds: passed.
- Locally signed normal APK build and signature verification: passed.
- Debug and normal package updates installed successfully.
- Device-side checks: passed for SQLite chat and saved-reply persistence across reopen, deletion, bounded recent-message context, Keystore encrypt/decrypt, clearing keys when endpoints change, HTTPS URL validation, request JSON and bearer header, response parsing, rejection of empty output, and HTTP 401/429/500/302 handling.
- API checks used a fake HTTPS connection inside an isolated instrumentation process; no requests were sent to an AI provider.
- Live Gemini compatibility requests now verified from both the PC and Android emulator; see the live check below.
- Original OnePlus screen capture was blocked by its lock screen. Later emulator capture verified the native chat screen and saved reply.

Internet chat is now the launcher activity. The PC WebView remains an optional menu item. No PC/USB port forwarding is needed for internet chat after installation.

## Live Gemini check

Google accepted the user-provided auth key for model listing (HTTP 200). The compatibility endpoint returned HTTP 200 for gemini-3.1-flash-lite with the text "Mnemos connection works." Usage: 10 prompt tokens + 5 response tokens = 15 total. The key was supplied through a hidden terminal prompt and was not saved in source or the APK.

The app setup screen now includes a Use Google Gemini preset for the verified base URL and model.

The live Android check passed in a temporary read-only Pixel 9 Pro emulator session. It used the real ChatApi implementation, encrypted the key with Android Keystore, received "Mnemos Android connection works.", saved the conversation, bookmarked the reply, and verified both after reopening SQLite. The native UI displayed the actual response and Saved indicator. Screenshot: frontend/test-results/gemini-android-live.png. The expanded mock checks for sanitized provider errors and bounded reads also passed.

The physical phone was not connected during this check. Its new Gemini configuration has not been applied. The temporary emulator session was stopped after testing; the key was not added to source or the APK.
