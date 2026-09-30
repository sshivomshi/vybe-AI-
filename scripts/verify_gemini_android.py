"""Configure the debug app with Gemini, then verify a real device reply and saving.
The key is entered without echo and only staged briefly in the app's private storage.
"""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--from-env',action='store_true',help='Use the existing private backend .env configuration')
args=parser.parse_args()
adb=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'
def run(args,**kwargs):
    return subprocess.run([str(adb),*args],capture_output=True,check=True,**kwargs)
rows=run(['devices']).stdout.decode().splitlines()
devices=[line.split()[0] for line in rows if line.strip().endswith('\tdevice')]
if len(devices)!=1:raise SystemExit('Connect and authorize exactly one Android test device.')
serial=devices[0]
# Confirm the installed debug package can receive private test input before reading any secret.
run(['-s',serial,'shell','run-as','com.mnemos.mobile.dev','mkdir','-p','files'])
config={}
if args.from_env:
    from dotenv import dotenv_values
    values=dotenv_values(Path(__file__).resolve().parents[1]/'.env')
    key=values.get('PS3_CLOUD_API_KEY','')
    config={'base':values.get('PS3_CLOUD_MODEL_URL',''),'model':values.get('PS3_CLOUD_MODEL','')}
    if not all(config.values()):raise SystemExit('Missing backend endpoint or model in .env.')
else:
    key=getpass.getpass('Gemini API key (hidden): ')
if not key:raise SystemExit('No key supplied.')
try:
    run(['-s',serial,'shell','run-as','com.mnemos.mobile.dev','sh','-c',"'cat > files/gemini-check.json'"],input=json.dumps({**config,'key':key}).encode())
    output=run(['-s',serial,'shell','am','instrument','-w','-e','live','true','com.mnemos.mobile.dev.test/com.mnemos.mobile.SmokeInstrumentation']).stdout.decode(errors='replace')
    print(output.replace(key,'[REDACTED]'))
    if 'PASS: Real Android HTTPS reply' not in output:
        raise SystemExit('Android chat setup did not pass. Check the sanitized result above.')
finally:
    run(['-s',serial,'shell','run-as','com.mnemos.mobile.dev','rm','-f','files/gemini-check.json'])
