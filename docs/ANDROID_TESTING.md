# Android v2.0: standalone internet client

The current APK starts in standalone mode. Install with `scripts/install_android.ps1`, then open API setup and enter an HTTPS Chat Completions base URL, model ID, and your API key. No PC or USB is needed after installation. Chats save on the phone; Save reply bookmarks an answer for offline reading.

The API receives up to the last 20 messages in the selected chat plus your new message. Saved replies are not automatically added as AI memory. Phone chats are separate from the existing PC database and are not synchronized or migrated automatically. Clearing app data or uninstalling removes phone history and credentials. Debug and normal packages have separate data.

Your API key is encrypted using Android Keystore. It is never bundled in the APK. HTTPS is required and redirects are rejected. Changing the base URL clears its old key. This is a bring-your-own-key client for personal testing. A public app should use a hosted authenticated gateway for any shared provider credential; do not embed a developer key in the APK.

Check a live reply after configuring your provider, save it, restart the app, and confirm both history and saved replies remain. Turn off internet and verify saved content is readable; sending should fail with a useful message and retain the draft.

Automated device checks use a fake HTTPS transport and isolated SQLite/preferences. They verify request format, errors, credential encryption, and persistence; they do not establish that a real provider works. Build with `gradlew.bat :android:assembleDebug :android:assembleDebugAndroidTest`, install both APKs, then run `adb shell am instrument -w com.mnemos.mobile.dev.test/com.mnemos.mobile.SmokeInstrumentation`.

---

The following instructions apply only to **Menu > PC live preview (optional)**.

# Test on an Android phone using the PC backend

This mode runs the mobile browser interface on Android. The PC runs the AI, memory database, and sync service. No APK installation is needed. Labels such as "this device" in the interface refer to the PC backend in this testing mode. The phone shares the PC's existing chats and memories.

## Connect

1. Start the PC app with `.\scripts\start.ps1 -WithModel` if it is not running.
2. On Android, enable Developer options (tap Build number seven times), then enable USB debugging. The exact settings location depends on the phone.
3. Connect a data-capable USB cable. Unlock the phone and accept its USB debugging prompt for this PC.
4. Run `.\scripts\test_android.ps1`. It checks the running app, maps phone port 8000 to PC port 8000 using ADB reverse, and opens the phone browser.
5. Keep the cable connected and PC awake. Re-run the script after reconnecting or rebooting.

With multiple phones, use `-Serial <device-id>` from `adb devices`. To remove the port mapping, run `.\scripts\test_android.ps1 -Disconnect`.

The API stays bound to PC loopback; no LAN firewall changes are needed. Only the app port is forwarded. This connection works without Wi-Fi or mobile data while USB and the local PC services remain available.

## Real-device checklist

- Open the navigation menu; visit Saved memories, AI connections, Device sync, and Settings.
- Start a new chat, choose a starter, edit its text, and send it. Check the keyboard does not obscure the Send button.
- Send a follow-up, scroll a longer conversation, rotate the screen, and return to portrait.
- Add a clearly named test memory, search it, edit it, and remove it when done. These actions change the PC's data.
- Reload the page and confirm conversation and memory persistence.
- Disable phone Wi-Fi/mobile data and send another message with USB attached to confirm this connection does not require internet. Any separately configured remote AI provider may still require the PC's internet.
- Unplug USB and confirm the unavailable-service message; reconnect and re-run the script.

Record phone model, Android version, RAM, browser version, initial page load time, keyboard/scroll responsiveness, and time to reply. Reply generation speed is principally a PC measurement in this mode. Desktop CPU throttling is only an approximation of phone UI performance, not evidence of real low-end hardware results.

## Install the Android APK

The installable package is `dist/android/Mnemos-Android.apk` (Android 8.0+, package `com.mnemos.mobile`). This is a locally signed testing APK, not a Play Store release. It uses the phone's Android System WebView to display the app and contains no model weights. Keep Android System WebView updated.

With a USB-authorized phone connected, run:

```powershell
.\scripts\install_android.ps1
```

This installs the APK, forwards the app port, and opens Mnemos. Alternatively, copy the APK to your phone and open it to install; Android may ask to allow installations from that source. USB forwarding is still required, using `scripts/test_android.ps1` on the PC. Use the app's Connect / Reload button after reconnecting.

The APK's top bar explicitly identifies the PC as the AI and storage host. A native connection-help page appears if the PC cannot be reached. No data port is exposed to the LAN, and cleartext traffic is permitted only for loopback. No native JavaScript bridge is exposed.

Build again with:

```powershell
.\.venv\Scripts\python.exe scripts/build_android.py
```

The build uses Android SDK platform 35, build tools 36.0.0, and Android Studio's bundled Java (override with `MNEMOS_JAVA_HOME`). Set `ANDROID_HOME` for another SDK location. Build dependencies are local; no Gradle downloads are required. The local test signing key is kept in `android/keys` and excluded from Git. Keep it to install updates over this APK without uninstalling. Do not use this test key for production distribution.
