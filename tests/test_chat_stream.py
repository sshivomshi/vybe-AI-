import asyncio
import json
import threading
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app
from backend.models import ChatInput


def test_answer_arrives_before_memory_extraction_finishes(tmp_path, monkeypatch):
    app=create_app(Settings(data_dir=tmp_path,cloud_url=''),enable_worker=False)
    release=threading.Event()
    monkeypatch.setattr(app.state.models,'complete',lambda *a,**kw:('Quick answer','local'))
    def candidate(*args):
        assert release.wait(5), 'Extraction was not released'
        return {'candidate':None},'local'
    monkeypatch.setattr(app.state.models,'candidate',candidate)
    endpoint=next(r.endpoint for r in app.routes if getattr(r,'path',None)=='/api/chat/stream')
    async def consume():
        response=endpoint(ChatInput(content='I prefer concise replies.',inference='local'))
        iterator=response.body_iterator
        try:
            first=json.loads(await asyncio.wait_for(iterator.__anext__(),2))
            assert first['type']=='answer' and first['result']['response']=='Quick answer'
            assert not release.is_set()
        finally: release.set()
        remaining=[json.loads(chunk) async for chunk in iterator if chunk.strip()]
        assert remaining[-1]['type']=='complete'
        assert len(TestClient(app).get('/api/chats/'+first['result']['chat_id']).json())==2
    asyncio.run(consume())


def test_stream_retry_does_not_repeat_generation_or_messages(tmp_path, monkeypatch):
    app=create_app(Settings(data_dir=tmp_path,cloud_url=''),enable_worker=False)
    calls=[]
    def complete(*a,**kw):
        calls.append(kw['force_local'])
        return 'Answer','local'
    monkeypatch.setattr(app.state.models,'complete',complete)
    monkeypatch.setattr(app.state.models,'candidate',lambda *a:({},'local'))
    client=TestClient(app)
    body={'content':'Test','inference':'local','request_id':str(uuid4())}
    def events(body):
        response=client.post('/api/chat/stream',json=body)
        assert response.status_code==200
        return [json.loads(line) for line in response.text.splitlines() if line.strip()]
    first=events(body)
    second=events(body)
    assert first[-1]==second[-1]
    assert calls==[True]
    assert len(client.get('/api/chats/'+first[-1]['result']['chat_id']).json())==2
    assert events({**body,'content':'Different'})[-1]['type']=='error'
