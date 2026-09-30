"""Build a locally signed Android test APK using installed SDK tools (no downloads)."""
import os
import sys
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('ANDROID_HOME') or Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk')
JDK = Path(os.environ.get('MNEMOS_JAVA_HOME') or 'C:/Program Files/Android/Android Studio/jbr')
TOOLS = SDK / 'build-tools/36.0.0'
ANDROID = SDK / 'platforms/android-35/android.jar'
BUILD = ROOT / 'android/build'
KEY = ROOT / 'android/keys/local-test.jks'
DEBUG = '--debug' in sys.argv
OUTPUT = ROOT / ('dist/android/Mnemos-Dev.apk' if DEBUG else 'dist/android/Mnemos-Android.apk')
if DEBUG: KEY = Path.home()/'.android/debug.keystore'

def run(*args):
    subprocess.run([str(x) for x in args], check=True, cwd=ROOT)

for path in [TOOLS/'aapt2.exe', TOOLS/'lib/d8.jar', TOOLS/'lib/apksigner.jar', ANDROID, JDK/'bin/javac.exe']:
    if not path.exists(): raise SystemExit(f'Missing build tool: {path}')
for path in [BUILD, BUILD/'classes', BUILD/'dex', KEY.parent, OUTPUT.parent]:
    path.mkdir(parents=True, exist_ok=True)
java=JDK/'bin/java.exe'
run(TOOLS/'aapt2.exe','compile','--dir',ROOT/'android/res','-o',BUILD/'resources.zip')
manifest = (ROOT/'android/AndroidManifest.xml').read_text(encoding='utf-8')
manifest = manifest.replace('<manifest ', '<manifest package="com.mnemos.mobile" android:versionCode="3" android:versionName="2.0" ', 1)
if DEBUG:
    manifest = manifest.replace('package="com.mnemos.mobile"','package="com.mnemos.mobile.dev"').replace('<application ', '<application android:debuggable="true" ',1).replace('android:label="@string/app_name"','android:label="Mnemos Dev"').replace('android:name=".MainActivity"','android:name="com.mnemos.mobile.MainActivity"').replace('android:name=".PcActivity"','android:name="com.mnemos.mobile.PcActivity"')
manifest = manifest.replace('<uses-permission', '<uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34"/><uses-permission', 1)
(BUILD/'AndroidManifest.xml').write_text(manifest, encoding='utf-8')
run(TOOLS/'aapt2.exe','link','-o',BUILD/'resources.apk','--manifest',BUILD/'AndroidManifest.xml','-I',ANDROID,BUILD/'resources.zip')
run(JDK/'bin/javac.exe','-encoding','UTF-8','--release','8','-classpath',ANDROID,'-d',BUILD/'classes',*sorted((ROOT/'android/src/com/mnemos/mobile').glob('*.java')))
run(JDK/'bin/jar.exe','cf',BUILD/'classes.jar','-C',BUILD/'classes','.')
run(java,'-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--lib',ANDROID,'--min-api','26','--output',BUILD/'dex',BUILD/'classes.jar')
shutil.copyfile(BUILD/'resources.apk',BUILD/'unsigned.apk')
with zipfile.ZipFile(BUILD/'unsigned.apk','a',zipfile.ZIP_DEFLATED) as archive:
    archive.write(BUILD/'dex/classes.dex','classes.dex')
run(TOOLS/'zipalign.exe','-f','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
if not KEY.exists():
    run(JDK/'bin/keytool.exe','-genkeypair','-keystore',KEY,'-storepass','android','-keypass','android','-alias','mnemos-test','-keyalg','RSA','-keysize','2048','-validity','10000','-dname','CN=Mnemos Local Testing','-noprompt')
run(java,'-jar',TOOLS/'lib/apksigner.jar','sign','--ks',KEY,'--ks-key-alias','androiddebugkey' if DEBUG else 'mnemos-test','--ks-pass','pass:android','--key-pass','pass:android','--out',OUTPUT,BUILD/'aligned.apk')
run(java,'-jar',TOOLS/'lib/apksigner.jar','verify','--verbose',OUTPUT)
run(TOOLS/'zipalign.exe','-c','4',OUTPUT)
print(f'APK ready: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)')

