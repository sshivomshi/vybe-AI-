"""Exercise the actual running sync authority over HTTP using two isolated devices."""
import json
import tempfile
from pathlib import Path
from backend.config import Settings
from backend.storage import Store
from backend.memory import MemoryService
from backend.sync import SyncEngine
from backend.models import MemoryInput,Resolution

def main():
    config=Settings()
    with tempfile.TemporaryDirectory(prefix='ps3-http-sync-') as tmp:
        a=MemoryService(Store(Path(tmp)/'a'));b=MemoryService(Store(Path(tmp)/'b'))
        sa=SyncEngine(a.store,a,config);sb=SyncEngine(b.store,b,config)
        try:
            value=MemoryInput(title='HTTP integration check',summary='Learning backpropagation')
            m=a.save(value);id=m['memory_id'];sa.run();sb.run()
            assert b.store.get(id)['version']==1
            a.save(value.model_copy(update={'summary':'Needs revision'}),id,1)
            b.save(value.model_copy(update={'summary':'Completed backpropagation'}),id,1)
            sa.run();sb.run()
            assert b.store.get(id)['sync_status']=='CONFLICT'
            with b.store.connect() as db:cid=db.execute('SELECT id FROM conflicts WHERE entity=? AND resolved=0',(id,)).fetchone()[0]
            sb.resolve(cid,Resolution(method='LOCAL'));sb.run();sa.run()
            assert a.store.get(id)==b.store.get(id)
            final=a.store.get(id)
            a.save(value,id,final['version'],delete=True);sa.run();sb.run()
            assert b.store.get(id)['deleted_at']
            report={'transport':'HTTP','authority':config.cloud_url,'two_device_sync':True,
                'conflict_detected':True,'resolved_summary':final['summary'],'resolved_version':final['version'],
                'deletion_propagated':True,'scope':'Development authority, not a public cloud deployment'}
            Path('docs/SYNC_HTTP_RESULT.json').write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2))
        finally:sa.client.close();sb.client.close()

if __name__=='__main__':main()
