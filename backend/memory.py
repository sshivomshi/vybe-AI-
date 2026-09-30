import json
import time
from threading import RLock
from fastapi import HTTPException
from .storage import uid, now, dump

class MemoryService:
    def __init__(self, store, vectors=None):
        self.store, self.vectors = store, vectors
        self.lock = RLock()
        self.index_error = None
        self.latency = None
    def index(self, memory):
        if not self.vectors: return
        with self.lock:
            try:
                # Always index the latest committed value, even if two writes race.
                self.vectors.put(self.store.get(memory['memory_id']) or memory)
            except Exception as exc:
                self.index_error = type(exc).__name__
                self.store.set_setting('index_dirty',True)
    def repair(self):
        if not self.vectors: return
        self.index_error=None
        for memory in self.store.all(): self.index(memory)
        self.store.set_setting('index_dirty', bool(self.index_error))
    def save(self, value, id=None, expected=None, delete=False, operation='UPDATE'):
        with self.lock, self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old=self.store.get(id,db) if id else None
            if id and not old: raise HTTPException(404,'Memory not found')
            if old and old['sync_status']=='CONFLICT': raise HTTPException(409,'Resolve the conflict before editing')
            if old and expected != old['version']: raise HTTPException(409,'Memory changed; reload before saving')
            data=value.model_dump() if hasattr(value,'model_dump') else dict(value)
            data.pop('expected_version',None)
            if not old:
                for row in db.execute('SELECT data FROM memories'):
                    existing=json.loads(row[0])
                    if (not existing['deleted_at'] and existing['local_only']==data['local_only']
                        and existing.get('source_chat_id')==data.get('source_chat_id')
                        and existing['summary'].strip().casefold()==data['summary'].strip().casefold()
                        and existing['memory_type']==data['memory_type'] and existing['archived']==data['archived']):
                        return existing
            if old and old['local_only'] is False and data['local_only']:
                raise HTTPException(409,'A synchronized memory cannot become local-only. Delete it on all devices, then create a local-only copy.')
            id=id or uid()
            stamp=now()
            data.update(memory_id=id,user_id='owner',created_at=old['created_at'] if old else stamp,
                        updated_at=stamp,version=old['version']+1 if old else 1,
                        device_id=self.store.setting('device_id'),
                        embedding_model=self.vectors.embeddings.name if self.vectors else None,
                        deleted_at=stamp if delete else None,
                        sync_status='LOCAL_ONLY' if data['local_only'] else 'PENDING')
            self.store.put(db,data)
            if not data['local_only']:
                publishing_local=bool(old and old['local_only'])
                op=dict(operation_id=uid(),entity_id=id,device_id=data['device_id'],
                        base_version=old['version'] if old and not publishing_local else 0,new_version=data['version'],
                        operation_type=('DELETE' if delete else ('CREATE' if not old or publishing_local else
                            ('ARCHIVE' if data['archived'] and not old['archived'] else
                             ('RESTORE' if old['archived'] and not data['archived'] else operation)))),timestamp=stamp,payload=data)
                db.execute('INSERT INTO operations(id,entity,data,status) VALUES (?,?,?,?)',
                           (op['operation_id'],id,dump(op),'PENDING'))
        self.index(data)
        if data['local_only'] and data.get('source_chat_id'):
            self.store.set_setting('chat_local_only:'+data['source_chat_id'],True)
        return data
    def search(self, query, limit=5, tag=None):
        if not self.vectors: raise HTTPException(503,'Local embedding model / Qdrant Edge unavailable. Run the model setup command.')
        with self.lock:
            if self.store.setting('index_dirty',False): self.repair()
            if self.index_error: raise HTTPException(503,'Vector index needs repair; memories remain safe in SQLite.')
            start=time.perf_counter()
            hits=self.vectors.search(query,limit,tag)
            result=[]
            for id,score in hits:
                m=self.store.get(id)
                if m and not m['deleted_at'] and not m['archived'] and m['memory_type']!='ARCHIVE_ONLY':
                    result.append(dict(m,score=score))
            self.latency=round((time.perf_counter()-start)*1000,2)
            return result
