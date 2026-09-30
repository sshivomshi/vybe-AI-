from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app


def test_explicit_local_applies_to_reply_and_extraction(tmp_path, monkeypatch):
    app=create_app(Settings(data_dir=tmp_path,cloud_url=''),enable_worker=False)
    calls=[]
    def reply(*args, **kwargs):
        calls.append(('reply',kwargs['force_local']))
        return 'Local response','local'
    def candidate(content,context,force_local):
        calls.append(('extraction',force_local))
        return {},'local'
    monkeypatch.setattr(app.state.models,'complete',reply)
    monkeypatch.setattr(app.state.models,'candidate',candidate)
    client=TestClient(app)
    assert client.post('/api/chat',json={'content':'Hello','inference':'local'}).json()['route']=='local'
    assert calls==[('reply',True),('extraction',True)]
    calls.clear()
    client.post('/api/chat',json={'content':'Another question','inference':'configured'})
    assert calls==[('reply',False),('extraction',False)]
    assert client.post('/api/chat',json={'content':'Hello','inference':'invalid'}).status_code==422
