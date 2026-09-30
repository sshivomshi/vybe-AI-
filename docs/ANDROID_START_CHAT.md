# Android space chat design

The native Android app uses a midnight background, lavender accents, a rounded composer, a compact menu and new-chat header, and separate user/assistant message styling. The welcome screen contains a procedural black hole with an accretion disk, orbiting highlights, and twinkling stars. Topic and writing suggestions focus the composer. History, saved replies, copying, deletion confirmation, and draft preservation remain available.

SpaceView draws with Android Canvas without external assets. Animation stops when detached or hidden and follows the system disabled-animation setting. The conversation removes the animated welcome scene to keep messages readable. All main icon controls have accessibility descriptions.

API setup is not exposed. The app still reads its existing endpoint, model, and encrypted credential from ApiSettings. Backend .env credentials do not automatically configure the standalone Android application; no credentials are embedded in the APK. Missing configuration is shown honestly and preserves the draft.

Validation: scripts/build_android.py compiled Java, packaged resources, verified the APK signature, and checked zip alignment. Output: dist/android/Mnemos-Android.apk. No device was connected, so visual device QA, animation performance, and live chat have not been verified.
