"""Real embedded Qdrant Edge. SQLite is the recoverable source of truth."""
import json
from pathlib import Path
from threading import RLock
from fastembed import TextEmbedding
from qdrant_edge import (EdgeShard, EdgeConfig, EdgeVectorParams, Distance,
                        Point, UpdateOperation, Query, QueryRequest, Filter,
                        FieldCondition, MatchValue)

class Embeddings:
    def __init__(self, settings, download=False):
        self.name = settings.embedding_model
        self.model = TextEmbedding(model_name=self.name, cache_dir=settings.model_cache,
                                   local_files_only=not download, threads=2)
        self.dimension = len(self.encode('dimension check'))
    def encode(self, text):
        return next(self.model.embed([text])).tolist()

class VectorRepository:
    def __init__(self, directory: Path, embeddings):
        self.embeddings = embeddings
        self.lock = RLock()
        directory.mkdir(parents=True, exist_ok=True)
        manifest = directory / 'embedding.json'
        expected = {'model': embeddings.name, 'dimension': embeddings.dimension}
        if manifest.exists() and json.loads(manifest.read_text()) != expected:
            raise RuntimeError('Embedding model changed. Rebuild the index before opening this device.')
        shard_path = directory / 'shard'
        exists = shard_path.exists() and any(shard_path.iterdir())
        shard_path.mkdir(parents=True, exist_ok=True)
        self.shard = (EdgeShard.load(str(shard_path)) if exists else
                      EdgeShard.create(str(shard_path), EdgeConfig(vectors={
                          'memory': EdgeVectorParams(size=embeddings.dimension, distance=Distance.Cosine)})))
        manifest.write_text(json.dumps(expected))
    def put(self, memory):
        with self.lock:
            if memory.get('deleted_at') or memory['archived'] or memory['memory_type']=='ARCHIVE_ONLY':
                self.shard.update(UpdateOperation.delete_points([memory['memory_id']]))
            else:
                vector = self.embeddings.encode(memory['title']+'\n'+memory['summary'])
                self.shard.update(UpdateOperation.upsert_points([Point(id=memory['memory_id'],
                    vector={'memory': vector}, payload={'tags':memory['tags'],'memory_type':memory['memory_type']})]))
    def search(self, query, limit=5, tag=None, threshold=.3):
        with self.lock:
            kwargs = {}
            if tag: kwargs['filter']=Filter(must=[FieldCondition(key='tags',match=MatchValue(value=tag))])
            return [(str(p.id), p.score) for p in self.shard.query(QueryRequest(
                query=Query.Nearest(self.embeddings.encode(query), using='memory'),
                limit=limit, with_payload=True, **kwargs)) if p.score >= threshold]
    def close(self):
        with self.lock: self.shard.close()
