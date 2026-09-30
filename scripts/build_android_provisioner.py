"""Build the device provisioning instrumentation with local SDK tools, without Gradle."""
import os, subprocess, zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk'
tools=sdk/'build-tools/36.0.0'
java=Path('C:/Program Files/Android/Android Studio/jbr/bin')
jar=sdk/'platforms/android-35/android.jar'
out=root/'android/build/provisioner'
out.mkdir(parents=True,exist_ok=True)
(out/'classes').mkdir(exist_ok=True)
(out/'dex').mkdir(exist_ok=True)
def run(*args):subprocess.run([str(a) for a in args],check=True)
(out/'AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.mnemos.mobile.dev.test"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34"/><application android:label="Mnemos checks"/><instrumentation android:name="com.mnemos.mobile.SmokeInstrumentation" android:targetPackage="com.mnemos.mobile.dev"/></manifest>')
run(tools/'aapt2.exe','link','-o',out/'test.apk','--manifest',out/'AndroidManifest.xml','-I',jar)
sources=list((root/'android/src/com/mnemos/mobile').glob('*.java'))+list((root/'android/checks/com/mnemos/mobile').glob('*.java'))
run(java/'javac.exe','-encoding','UTF-8','--release','8','-classpath',jar,'-d',out/'classes',*sources)
run(java/'jar.exe','cf',out/'classes.jar','-C',out/'classes','.')
run(java/'java.exe','-cp',tools/'lib/d8.jar','com.android.tools.r8.D8','--lib',jar,'--min-api','26','--output',out/'dex',out/'classes.jar')
with zipfile.ZipFile(out/'test.apk','a') as archive:archive.write(out/'dex/classes.dex','classes.dex')
run(tools/'zipalign.exe','-f','4',out/'test.apk',out/'aligned.apk')
run(java/'java.exe','-jar',tools/'lib/apksigner.jar','sign','--ks',Path.home()/'.android/debug.keystore','--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',out/'provisioner.apk',out/'aligned.apk')
print('Provisioner built.')
