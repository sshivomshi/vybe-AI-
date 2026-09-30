"""Real local LLM + real Qdrant, with all non-loopback networking explicitly denied."""
import json
import socket
import tempfile
import time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app

def main():
    original=socket.socket.connect
    def loopback_only(self,address):
        if address[0] not in ('127.0.0.1','::1','localhost'):
            raise OSError('External network disabled for the offline demo verification')
        return original(self,address)
    socket.socket.connect=loopback_only
    start=time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix='ps3-offline-demo-') as tmp:
            settings=Settings(data_dir=Path(tmp),cloud_url='http://127.0.0.1:65530',cloud_model_url='',
                local_model_url='http://127.0.0.1:8081/v1',local_model='ps3-local')
            app=create_app(settings,enable_worker=False)
            with TestClient(app) as client:
                first=client.post('/api/chat',json={'content':'I am preparing CNN for my machine learning exam. I understand convolution and pooling but still need to revise backpropagation.'}).json()
                assert first['route']=='local' and first['candidate'],first
                memory=client.post('/api/memories',json=first['candidate']).json()
                search=client.get('/api/memories',params={'q':'What topic was I struggling with in CNN?'}).json()
                assert search[0]['memory_id']==memory['memory_id'],search
                second=client.post('/api/chat',json={'chat_id':first['chat_id'],'content':'What topic was I struggling with in CNN? Answer in one sentence.'}).json()
                assert 'backpropagation' in second['response'].lower(),second
                assert second['memories_used'][0]['memory_id']==memory['memory_id']
                third=client.post('/api/chat',json={'chat_id':first['chat_id'],'content':'I have now completed backpropagation.'}).json()
                assert third['candidate'] and third['related_id']==memory['memory_id'],third
                updated=client.put('/api/memories/'+memory['memory_id'],json={**third['candidate'],'expected_version':1}).json()
                assert updated['version']==2,updated
                assert 'completed' in updated['summary'].lower(),updated
                fourth=client.post('/api/chat',json={'content':'What is my latest backpropagation progress? Answer in one sentence.'}).json()
                assert fourth['memories_used'][0]['summary']==updated['summary']
                assert 'completed' in fourth['response'].lower(),fourth
                app.state.sync.run()
                status=client.get('/api/status').json()
                assert status['connection']=='OFFLINE' and status['pending']==2,status
                report={'external_network':'blocked','model_route':first['route'],'memory_created':True,
                    'semantic_retrieval_score':search[0]['score'],'memory_aware_answer':second['response'],
                    'evolved_summary':updated['summary'],'evolved_answer':fourth['response'],
                    'version':updated['version'],'pending_offline_operations':status['pending'],
                    'seconds':round(time.perf_counter()-start,2)}
                Path('docs/OFFLINE_DEMO_RESULT.json').write_text(json.dumps(report,indent=2))
                print(json.dumps(report,indent=2))
    finally:socket.socket.connect=original

if __name__=='__main__':main()
