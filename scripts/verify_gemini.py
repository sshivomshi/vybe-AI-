"""Small live Gemini compatibility check. Reads a key without saving it or echoing it."""
import getpass
import json
import httpx

BASE = 'https://generativelanguage.googleapis.com/v1beta/openai'

def main():
    key = getpass.getpass('Gemini API key (hidden): ')
    if not key:
        raise SystemExit('No key supplied.')
    def safe_error(response):
        try:
            error=response.json().get('error', {})
            print(json.dumps({'http_status':response.status_code,'status':error.get('status'),'message':str(error.get('message','Request failed')).replace(key,'[REDACTED]')[:1800]}))
        except Exception:
            print(json.dumps({'http_status':response.status_code,'message':'Non-JSON provider error'}))
    with httpx.Client(timeout=60,follow_redirects=False,headers={'Authorization':'Bearer '+key}) as client:
        models=client.get(BASE+'/models')
        if not models.is_success:
            safe_error(models);return
        ids=[m['id'].removeprefix('models/') for m in models.json().get('data',[])]
        print(json.dumps({'models_status':models.status_code,'text_flash_models':[x for x in ids if 'flash' in x and not any(t in x for t in ('image','audio','tts','live'))][:20]}))
        preferred=['gemini-3.1-flash-lite','gemini-2.5-flash-lite','gemini-2.5-flash','gemini-3.8-flash']
        model=next((m for m in preferred if m in ids),None)
        if model is None:
            print('No known small text model is available; select an ID from the returned list.');return
        response=client.post(BASE+'/chat/completions',json={'model':model,'messages':[{'role':'user','content':'Reply with exactly: Mnemos connection works.'}],'stream':False,'max_tokens':100})
        if not response.is_success:
            safe_error(response);return
        data=response.json()
        print(json.dumps({'http_status':response.status_code,'model':model,'reply':data['choices'][0]['message'].get('content'),'usage':data.get('usage')},ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except httpx.HTTPError as error: print('Network failure: '+type(error).__name__)
