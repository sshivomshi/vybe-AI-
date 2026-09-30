from uuid import uuid4
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app


def test_capture_toggle_restart_and_retry(tmp_path, monkeypatch):
    settings = Settings(data_dir=tmp_path / 'capture', cloud_url='')
    app = create_app(settings, enable_worker=False)
    monkeypatch.setattr(app.state.models, 'complete', lambda *a, **k: ('Reply', 'local'))
    monkeypatch.setattr(app.state.models, 'candidate', lambda *a, **k: ({}, None))
    client = TestClient(app)
    request = {'content': 'First turn', 'capture': True, 'request_id': str(uuid4())}
    first = client.post('/api/chat', json=request)
    assert first.status_code == 200
    chat = first.json()['chat_id']
    assert len(client.get('/api/constellation').json()['messages']) == 2
    client.post('/api/chat', json=request)
    assert len(client.get('/api/constellation').json()['messages']) == 2
    assert client.put(f'/api/chats/{chat}/capture', json={'enabled': False}).status_code == 200
    client.post('/api/chat', json={'content': 'Uncaptured turn', 'chat_id': chat})
    assert len(client.get('/api/constellation').json()['messages']) == 2
    restarted = TestClient(create_app(settings, enable_worker=False))
    assert restarted.get('/api/chats').json()[0]['capture'] is False
    assert len(restarted.get('/api/constellation').json()['messages']) == 2
    restarted.put(f'/api/chats/{chat}/capture', json={'enabled': True})
    assert len(restarted.get('/api/constellation').json()['messages']) == 4
    assert restarted.put('/api/chats/missing/capture', json={'enabled': True}).status_code == 404


def test_default_chat_is_not_captured(tmp_path, monkeypatch):
    app = create_app(Settings(data_dir=tmp_path / 'default', cloud_url=''), enable_worker=False)
    monkeypatch.setattr(app.state.models, 'complete', lambda *a, **k: ('Reply', 'local'))
    monkeypatch.setattr(app.state.models, 'candidate', lambda *a, **k: ({}, None))
    client = TestClient(app)
    client.post('/api/chat', json={'content': 'Ordinary chat'})
    assert client.get('/api/constellation').json()['messages'] == []
