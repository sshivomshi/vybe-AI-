"""Single-account sync authority. Deploy behind HTTPS with a strong bearer token."""
import hmac
import json
from fastapi import FastAPI, Header, HTTPException, Depends, Query
from .config import Settings
from .storage import Store, dump
from .models import Operation, StoredMemory

def create_cloud(settings=None):
    settings=settings or Settings()
    store=Store(settings.cloud_dir)
    app=FastAPI(title='PS3 Sync Authority')
    app.state.store=store
    def authorize(authorization: str=Header(default='')):
        if not settings.sync_token: raise HTTPException(503,'Set PS3_SYNC_TOKEN before using the sync authority')
        if not hmac.compare_digest(authorization,'Bearer '+settings.sync_token): raise HTTPException(401,'Unauthorized')
    @app.get('/health',dependencies=[Depends(authorize)])
    def health(): return {'status':'ONLINE','memories':sum(not m['deleted_at'] for m in store.all())}
    @app.post('/operations',dependencies=[Depends(authorize)])
    def apply(op: Operation):
        try: payload=StoredMemory.model_validate(op.payload).model_dump()
        except ValueError: raise HTTPException(422,'Invalid memory payload')
        if (payload.get('memory_id')!=op.entity_id or payload.get('version')!=op.new_version
            or payload.get('device_id')!=op.device_id or payload.get('local_only')
            or (op.new_version!=op.base_version+1 and not (op.operation_type=='CREATE' and op.base_version==0))):
            raise HTTPException(422,'Invalid operation metadata')
        request=dump(op.model_dump())
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            receipt=db.execute('SELECT request,response FROM receipts WHERE id=?',(op.operation_id,)).fetchone()
            if receipt:
                if receipt['request']!=request: raise HTTPException(409,'Operation ID reused with different content')
                return json.loads(receipt['response'])
            remote=store.get(op.entity_id,db)
            if (remote['version'] if remote else 0)!=op.base_version:
                result={'status':'CONFLICT','remote':remote}
            else:
                stored=dict(payload,sync_status='SYNCED')
                store.put(db,stored)
                db.execute('INSERT INTO changes(data) VALUES (?)',(dump(stored),))
                result={'status':'SUCCESS','remote':stored}
            db.execute('INSERT INTO receipts VALUES (?,?,?)',(op.operation_id,request,dump(result)))
        return result
    @app.get('/changes',dependencies=[Depends(authorize)])
    def changes(after: int=Query(default=0,ge=0)):
        with store.connect() as db:
            rows=db.execute('SELECT seq,data FROM changes WHERE seq>? ORDER BY seq LIMIT 200',(after,)).fetchall()
        return {'cursor':rows[-1]['seq'] if rows else after,'changes':[json.loads(r['data']) for r in rows], 'has_more':len(rows)==200}
    return app

app=create_cloud()
