import json
import time
import threading
import httpx
from fastapi import HTTPException
from .storage import dump, uid, now

class SyncEngine:
    def __init__(self, store, memory, settings, client=None):
        self.store,self.memory,self.settings=store,memory,settings
        self.client=client or httpx.Client(base_url=settings.cloud_url or 'http://127.0.0.1:8090',
            headers={'Authorization':'Bearer '+settings.sync_token},timeout=8)
        self.lock=threading.Lock()
        self.state='NOT_CONFIGURED' if not settings.cloud_url else 'CHECKING'
        self.cloud_count=None
    def conflict(self, db, local, remote):
        existing=db.execute('SELECT id FROM conflicts WHERE entity=? AND resolved=0',(local['memory_id'],)).fetchone()
        if existing: return
        value={'conflict_id':uid(),'entity_id':local['memory_id'],'local':local,'remote':remote,
               'detected_at':now(),'conflict_type':'DELETE_UPDATE_CONFLICT' if bool(local.get('deleted_at'))!=bool((remote or {}).get('deleted_at')) else 'VERSION_CONFLICT'}
        db.execute('INSERT INTO conflicts VALUES (?,?,?,0)',(value['conflict_id'],value['entity_id'],dump(value)))
        local=dict(local,sync_status='CONFLICT')
        db.execute('UPDATE memories SET data=? WHERE id=?',(dump(local),local['memory_id']))
        db.execute("UPDATE operations SET status='CONFLICT' WHERE entity=? AND status IN ('PENDING','SYNCING','FAILED')",(local['memory_id'],))
    def run(self, manual=False):
        if not self.settings.cloud_url: return
        if not self.lock.acquire(blocking=False): return
        try:
            r=self.client.get('/health'); r.raise_for_status()
            self.cloud_count=r.json()['memories']; self.state='SYNCING'
            with self.store.connect() as db:
                rows=db.execute("SELECT * FROM operations WHERE status IN ('PENDING','FAILED') ORDER BY seq").fetchall()
            blocked=set()
            for row in rows:
                if row['entity'] in blocked: continue
                if not manual and row['next_retry']>time.time(): blocked.add(row['entity']); continue
                with self.store.connect() as db:
                    fresh=db.execute('SELECT status FROM operations WHERE id=?',(row['id'],)).fetchone()
                    if fresh[0] not in ('PENDING','FAILED'): continue
                    db.execute("UPDATE operations SET status='SYNCING' WHERE id=?",(row['id'],))
                try:
                    response=self.client.post('/operations',json=json.loads(row['data'])); response.raise_for_status()
                    result=response.json()
                    with self.memory.lock, self.store.connect() as db:
                        local=self.store.get(row['entity'],db)
                        if result['status']=='CONFLICT':
                            self.conflict(db,local,result['remote']); blocked.add(row['entity'])
                        else:
                            db.execute("UPDATE operations SET status='SUCCESS',error=NULL WHERE id=?",(row['id'],))
                            if local['version']==result['remote']['version']:
                                local['sync_status']='SYNCED'
                                db.execute('UPDATE memories SET data=? WHERE id=?',(dump(local),row['entity']))
                except (httpx.HTTPError,ValueError,KeyError):
                    with self.store.connect() as db:
                        db.execute("UPDATE operations SET status='FAILED', retries=retries+1,next_retry=?,error=? WHERE id=?",
                                   (time.time()+min(300,2**min(row['retries']+1,8)),'Sync request failed; local data preserved',row['id']))
                    self.state='SYNC_FAILED'
                    return
            while True:
                cursor=self.store.setting('cursor',0)
                response=self.client.get('/changes',params={'after':cursor}); response.raise_for_status()
                page=response.json()
                changed=[]
                with self.memory.lock, self.store.connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    for remote in page['changes']:
                        local=self.store.get(remote['memory_id'],db)
                        pending=db.execute("SELECT 1 FROM operations WHERE entity=? AND status IN ('PENDING','FAILED','SYNCING','CONFLICT')",(remote['memory_id'],)).fetchone()
                        if local and (local['local_only'] or pending):
                            if remote['version']>local['version'] or (remote['version']==local['version'] and remote['device_id']!=local['device_id']):
                                self.conflict(db,local,remote)
                            continue
                        if not local or remote['version']>local['version']:
                            self.store.put(db,remote); changed.append(remote)
                    db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('cursor',dump(page['cursor'])))
                for memory in changed: self.memory.index(memory)
                if not page['has_more']: break
            self.store.set_setting('last_sync',now()); self.state='ONLINE'
        except (httpx.HTTPError,ValueError,KeyError): self.state='OFFLINE'
        finally: self.lock.release()
    def resolve(self, id, resolution):
        with self.lock, self.memory.lock, self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT data FROM conflicts WHERE id=? AND resolved=0',(id,)).fetchone()
            if not row: raise HTTPException(404,'Open conflict not found')
            conflict=json.loads(row[0]); remote=conflict['remote']; local=conflict['local']
            db.execute("UPDATE operations SET status='SUPERSEDED' WHERE entity=? AND status IN ('PENDING','FAILED','SYNCING','CONFLICT')",(local['memory_id'],))
            if resolution.method=='REMOTE':
                if remote is None: raise HTTPException(409,'Remote memory is absent; choose local or merge')
                value=dict(remote,sync_status='SYNCED')
            else:
                if resolution.method=='MERGE' and resolution.merged is None: raise HTTPException(422,'Merged memory is required')
                value=dict(local)
                if resolution.method=='MERGE': value.update(resolution.merged.model_dump(),deleted_at=None)
                value.update(version=(remote['version'] if remote else 0)+1,updated_at=now(),
                             device_id=self.store.setting('device_id'),sync_status='PENDING',local_only=False)
                op=dict(operation_id=uid(),entity_id=value['memory_id'],device_id=value['device_id'],
                        base_version=remote['version'] if remote else 0,new_version=value['version'],
                        operation_type='MERGE',timestamp=now(),payload=value)
                db.execute('INSERT INTO operations(id,entity,data,status) VALUES (?,?,?,?)',(op['operation_id'],op['entity_id'],dump(op),'PENDING'))
            self.store.put(db,value)
            conflict.update(resolution_method=resolution.method,resolved_value=value,resolved_at=now())
            db.execute('UPDATE conflicts SET resolved=1,data=? WHERE id=?',(dump(conflict),id))
        self.memory.index(value)
        return value
