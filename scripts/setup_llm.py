"""Download the official CPU llama.cpp runtime and Qwen's 1.5B GGUF to this project."""
from pathlib import Path
import hashlib
import json
import zipfile
import httpx

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'data'/'llm'
REPO='Qwen/Qwen2.5-1.5B-Instruct-GGUF'
MODEL='qwen2.5-1.5b-instruct-q4_k_m.gguf'

def download(client,url,path,expected=None):
    if path.exists() and expected and hashlib.sha256(path.read_bytes()).hexdigest()==expected:return
    part=path.with_suffix(path.suffix+'.part')
    digest=hashlib.sha256()
    with client.stream('GET',url) as r:
        r.raise_for_status()
        with part.open('wb') as f:
            for chunk in r.iter_bytes(1024*1024):f.write(chunk);digest.update(chunk)
    if expected and digest.hexdigest()!=expected:raise RuntimeError('Download checksum mismatch')
    part.replace(path)

def main():
    TARGET.mkdir(parents=True,exist_ok=True)
    with httpx.Client(follow_redirects=True,timeout=120) as client:
        releases=client.get('https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=20');releases.raise_for_status()
        release,asset=next((r,a) for r in releases.json() for a in r['assets'] if a['name'].endswith('bin-win-cpu-x64.zip'))
        print('Downloading official runtime:',asset['name'],flush=True)
        archive=TARGET/asset['name']
        download(client,asset['browser_download_url'],archive,(asset.get('digest') or '').removeprefix('sha256:') or None)
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not (TARGET/'runtime'/name).resolve().is_relative_to((TARGET/'runtime').resolve()):raise RuntimeError('Unsafe archive path')
            z.extractall(TARGET/'runtime')
        info=client.get(f'https://huggingface.co/api/models/{REPO}/revision/main?blobs=true');info.raise_for_status()
        info=info.json();revision=info['sha']
        file=next(f for f in info['siblings'] if f['rfilename']==MODEL)
        digest=file['lfs']['sha256']
        print('Downloading local language model (~1.1 GB):',MODEL,flush=True)
        download(client,f'https://huggingface.co/{REPO}/resolve/{revision}/{MODEL}',TARGET/MODEL,digest)
        (TARGET/'manifest.json').write_text(json.dumps({'runtime':release['tag_name'],'model':REPO,'revision':revision,'sha256':digest},indent=2))
        print('Local language model ready.',flush=True)

if __name__=='__main__':main()
