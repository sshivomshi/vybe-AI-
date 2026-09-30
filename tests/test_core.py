import json
from pathlib import Path
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.storage import Store
from backend.memory import MemoryService
from backend.models import MemoryInput, Resolution
from backend.cloud import create_cloud
from backend.sync import SyncEngine

def payload(**kwargs):
    return MemoryInput(title='CNN Study Progress',summary='Understands convolution and pooling; needs revision of backpropagation.',tags=['CNN'],**kwargs)

@pytest.fixture
def world(tmp_path):
    config=Settings(cloud_dir=tmp_path/'cloud',cloud_url='http://testserver',sync_token='test-secret')
    cloud=create_cloud(config)
    clients=[]
    def device(name):
        store=Store(tmp_path/name); mem=MemoryService(store)
        client=TestClient(cloud,headers={'Authorization':'Bearer test-secret'}); clients.append(client)
        return mem,SyncEngine(store,mem,config,client)
    yield device,cloud
    for c in clients:c.close()

def test_local_transactions_restart_and_privacy(tmp_path):
    service=MemoryService(Store(tmp_path))
    first=service.save(payload())
    service.save(payload(local_only=True))
    restarted=Store(tmp_path)
    assert restarted.get(first['memory_id'])==first
    with restarted.connect() as db: assert db.execute('SELECT count(*) FROM operations').fetchone()[0]==1
    with pytest.raises(HTTPException):service.save(payload(),first['memory_id'],99)

def test_idempotency_and_out_of_order(world):
    device,cloud=world; m,s=device('a'); first=m.save(payload())
    with m.store.connect() as db: op=json.loads(db.execute('SELECT data FROM operations').fetchone()[0])
    one=s.client.post('/operations',json=op); two=s.client.post('/operations',json=op)
    assert one.json()==two.json()
    assert len(s.client.get('/changes').json()['changes'])==1
    op['payload']['summary']='changed'
    assert s.client.post('/operations',json=op).status_code==409

@pytest.mark.parametrize('method',['LOCAL','REMOTE','MERGE'])
def test_two_devices_conflict_resolution(world,method):
    device,cloud=world; a,sa=device('a'); b,sb=device('b')
    original=a.save(payload()); id=original['memory_id'];sa.run();sb.run()
    assert b.store.get(id)['version']==1
    a.save(payload().model_copy(update={'summary':'Needs more revision.'}),id,1)
    b.save(payload().model_copy(update={'summary':'Completed backpropagation.'}),id,1)
    sa.run();sb.run()
    assert b.store.get(id)['sync_status']=='CONFLICT'
    with b.store.connect() as db: conflict=db.execute('SELECT id FROM conflicts WHERE resolved=0').fetchone()[0]
    sb.resolve(conflict,Resolution(method=method,merged=payload().model_copy(update={'summary':'Completed fundamentals; revise advanced derivatives.'}) if method=='MERGE' else None))
    sb.run();sa.run()
    assert a.store.get(id)==b.store.get(id)
    expected={'LOCAL':'Completed backpropagation.','REMOTE':'Needs more revision.','MERGE':'Completed fundamentals; revise advanced derivatives.'}[method]
    assert a.store.get(id)['summary']==expected

def test_multiple_offline_edits_and_deletion(world):
    device,_=world;a,sa=device('a');b,sb=device('b')
    m=a.save(payload());id=m['memory_id']
    a.save(payload(),id,1);a.save(payload(),id,2)
    sa.run();sb.run();assert b.store.get(id)['version']==3
    a.save(payload(),id,3,delete=True);sa.run();sb.run()
    assert b.store.get(id)['deleted_at']

def test_publish_existing_local_only_memory(world):
    device,_=world;a,sa=device('a');b,sb=device('b')
    m=a.save(payload(local_only=True));id=m['memory_id']
    a.save(payload(local_only=True),id,1)
    a.save(payload(local_only=False),id,2)
    sa.run();sb.run()
    assert a.store.get(id)['sync_status']=='SYNCED'
    assert b.store.get(id)['version']==3

def test_response_lost_after_commit_retries_idempotently(world):
    device,_=world;m,s=device('a');memory=m.save(payload());real=s.client
    class LostResponse:
        def get(self,*a,**k): return real.get(*a,**k)
        def post(self,*a,**k):
            real.post(*a,**k)
            raise httpx.ReadTimeout('Response lost after commit')
    s.client=LostResponse();s.run()
    with m.store.connect() as db:
        row=db.execute('SELECT status,retries,next_retry FROM operations').fetchone()
        assert row['status']=='FAILED' and row['retries']==1 and row['next_retry']>0
    s.client=real;s.run(manual=True)
    assert m.store.get(memory['memory_id'])['sync_status']=='SYNCED'
    assert len(real.get('/changes').json()['changes'])==1

def test_cloud_authentication(world):
    _,cloud=world
    with TestClient(cloud) as client:
        assert client.get('/changes').status_code==401

def test_cloud_rejects_incomplete_payload(world):
    device,_=world;m,s=device('a');m.save(payload())
    with m.store.connect() as db:op=json.loads(db.execute('SELECT data FROM operations').fetchone()[0])
    del op['payload']['created_at']
    assert s.client.post('/operations',json=op).status_code==422
    assert s.client.get('/health').json()['memories']==0

def test_delete_update_conflict(world):
    device,_=world;a,sa=device('a');b,sb=device('b');m=a.save(payload());id=m['memory_id'];sa.run();sb.run()
    a.save(payload(),id,1,delete=True);b.save(payload(),id,1);sa.run();sb.run()
    with b.store.connect() as db: c=json.loads(db.execute('SELECT data FROM conflicts').fetchone()[0])
    assert c['conflict_type']=='DELETE_UPDATE_CONFLICT'

def test_validation():
    with pytest.raises(ValueError):MemoryInput(title=' ',summary='x')
    with pytest.raises(ValueError):payload(importance=2)

def test_exact_duplicate_reuses_memory_and_queue(tmp_path):
    m=MemoryService(Store(tmp_path))
    first=m.save(payload());again=m.save(payload())
    assert first['memory_id']==again['memory_id']
    with m.store.connect() as db:assert db.execute('SELECT count(*) FROM operations').fetchone()[0]==1

def test_local_only_source_pins_conversation(tmp_path):
    m=MemoryService(Store(tmp_path));m.save(payload(local_only=True,source_chat_id='source-chat'))
    assert m.store.setting('chat_local_only:source-chat') is True

def test_embedding_model_mismatch_rejected(tmp_path,embeddings):
    from backend.vectors import VectorRepository
    v=VectorRepository(tmp_path,embeddings);v.close()
    (tmp_path/'embedding.json').write_text(json.dumps({'model':'different-model','dimension':384}))
    with pytest.raises(RuntimeError,match='Embedding model changed'):VectorRepository(tmp_path,embeddings)

def test_cloud_fallback_and_local_only_routing(monkeypatch):
    from backend.ai import Models
    calls=[]
    def post(url,**kwargs):
        calls.append(url)
        if url.startswith('https://cloud.example'):raise httpx.ConnectError('Offline')
        return httpx.Response(200,json={'choices':[{'message':{'content':'local answer'}}]},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'post',post)
    m=Models(Settings(cloud_model_url='https://cloud.example/v1',cloud_model='cloud',cloud_api_key='test',local_model_url='http://127.0.0.1:8081/v1',cloud_fallback_to_local=True))
    assert m.complete([{'role':'user','content':'hello'}])==('local answer','local')
    assert len(calls)==2
    calls.clear();m.complete([{'role':'user','content':'private'}],force_local=True)
    assert len(calls)==1 and calls[0].startswith('http://127.0.0.1')

def test_restart_recovers_inflight_queue(tmp_path):
    m=MemoryService(Store(tmp_path));m.save(payload())
    with m.store.connect() as db:db.execute("UPDATE operations SET status='SYNCING'")
    recovered=Store(tmp_path)
    with recovered.connect() as db:assert db.execute('SELECT status FROM operations').fetchone()[0]=='PENDING'

def test_cloud_unavailable_preserves_offline_edits(world):
    device,_=world;m,s=device('a');saved=m.save(payload())
    class Offline:
        def get(self,*a,**k):raise httpx.ConnectError('No network')
    s.client=Offline();s.run()
    assert s.state=='OFFLINE'
    assert m.store.get(saved['memory_id'])['sync_status']=='PENDING'

def test_index_failure_preserves_sqlite_and_recovers(tmp_path,embeddings):
    from backend.vectors import VectorRepository
    real=VectorRepository(tmp_path/'vectors',embeddings)
    class Broken:
        embeddings=real.embeddings
        def put(self,*args):raise OSError('Disk error')
    m=MemoryService(Store(tmp_path/'db'),Broken());saved=m.save(payload())
    assert m.store.get(saved['memory_id'])
    assert m.store.setting('index_dirty')
    m.vectors=real
    assert m.search('CNN revision')[0]['memory_id']==saved['memory_id']
    assert not m.store.setting('index_dirty')
    real.close()

def test_local_embeddings_and_restart_without_network(tmp_path,monkeypatch):
    import socket
    def deny(*args,**kwargs):raise AssertionError('Network access attempted during offline operation')
    monkeypatch.setattr(socket.socket,'connect',deny)
    from backend.vectors import Embeddings,VectorRepository
    e=Embeddings(Settings());v=VectorRepository(tmp_path/'edge',e)
    m=MemoryService(Store(tmp_path/'db'),v);saved=m.save(payload());v.close()
    e=Embeddings(Settings());v=VectorRepository(tmp_path/'edge',e)
    m=MemoryService(Store(tmp_path/'db'),v)
    assert m.search('What was difficult in CNN?')[0]['memory_id']==saved['memory_id']
    v.close()

@pytest.fixture(scope='module')
def embeddings():
    from backend.vectors import Embeddings
    return Embeddings(Settings())

def test_real_edge_semantics_filters_archive_restart(tmp_path,embeddings):
    from backend.vectors import VectorRepository
    repository=VectorRepository(tmp_path/'index',embeddings)
    m=MemoryService(Store(tmp_path/'db'),repository)
    first=m.save(payload());id=first['memory_id']
    assert m.search('What topic was I struggling with in CNN?')[0]['memory_id']==id
    assert m.search('CNN',tag='other')==[]
    repository.close()
    repository=VectorRepository(tmp_path/'index',embeddings);m=MemoryService(Store(tmp_path/'db'),repository)
    assert m.search('What should I revise for machine learning?')[0]['memory_id']==id
    m.save(payload(archived=True),id,1);assert m.search('CNN')==[]
    m.save(payload(),id,2);assert len(m.search('CNN'))==1
    m.save(payload(),id,3,delete=True);assert m.search('CNN')==[]
    repository.close()

def test_api_validation_source_and_missing_model(tmp_path,embeddings,monkeypatch):
    from backend.main import create_app
    from backend.vectors import VectorRepository
    app=create_app(Settings(data_dir=tmp_path/'device'),VectorRepository(tmp_path/'index',embeddings),False)
    def missing(*args,**kwargs):raise RuntimeError('Local model unavailable')
    monkeypatch.setattr(app.state.models,'complete',missing)
    with TestClient(app) as client:
        assert client.post('/api/memories',json={'title':'','summary':''}).status_code==422
        assert client.post('/api/memories',headers={'Origin':'https://attacker.example'},json=payload().model_dump()).status_code==403
        m=client.post('/api/memories',json=payload().model_dump()).json()
        assert client.get('/api/memories',params={'q':'CNN struggle'}).json()[0]['memory_id']==m['memory_id']
        reply=client.post('/api/chat',json={'content':'What should I revise?'}).json()
        assert reply['response'] is None
        assert 'Local model unavailable' in reply['warnings']
        assert len(client.get('/api/chats/'+reply['chat_id']).json())==1
        assert client.get('/api/status').json()['active_memories']==1


def test_chat_retry_receipt_preserves_single_exchange(tmp_path,embeddings,monkeypatch):
    from backend.main import create_app
    from backend.vectors import VectorRepository
    from uuid import uuid4
    app=create_app(Settings(data_dir=tmp_path/'device'),VectorRepository(tmp_path/'index',embeddings),False)
    app.state.store.set_setting('preferences',{'memory_enabled':False})
    def unavailable(*a,**k):raise RuntimeError('Temporary outage')
    monkeypatch.setattr(app.state.models,'complete',unavailable)
    body={'content':'Hello','request_id':str(uuid4())}
    with TestClient(app) as client:
        first=client.post('/api/chat',json=body).json()
        assert first['response'] is None
        monkeypatch.setattr(app.state.models,'complete',lambda *a,**k:('Hello back','local'))
        second=client.post('/api/chat',json=body).json()
        assert second['chat_id']==first['chat_id']
        assert client.post('/api/chat',json=body).json()==second
        assert len(client.get('/api/chats/'+second['chat_id']).json())==2
        assert client.post('/api/chat',json={**body,'content':'Different'}).status_code==409
