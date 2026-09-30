"""Measured, reproducible local retrieval benchmark; no model-judged quality claims."""
import json
import statistics
import tempfile
import time
from pathlib import Path
from backend.config import Settings
from backend.vectors import Embeddings,VectorRepository
from backend.storage import Store
from backend.memory import MemoryService
from backend.models import MemoryInput

RAW='I am preparing CNN for my machine learning exam. I understand convolution and pooling but still need to revise backpropagation.'
CASES={
 'QUICK':'CNN exam: revise backpropagation.',
 'STANDARD':'Preparing for a machine learning exam. Understands CNN convolution and pooling; needs to revise backpropagation.',
 'DETAILED':'Preparing CNN for a machine learning exam. Understands convolution and pooling. Backpropagation still needs revision; this is the remaining study gap.'}

def main():
    embeddings=Embeddings(Settings());results=[]
    with tempfile.TemporaryDirectory(prefix='ps3-benchmark-') as root:
        for mode,summary in CASES.items():
            directory=Path(root)/mode
            vectors=VectorRepository(directory/'edge',embeddings);service=MemoryService(Store(directory/'db'),vectors)
            m=service.save(MemoryInput(title='CNN Study Progress',summary=summary,memory_type=mode))
            durations=[];hits=[]
            for _ in range(20):
                start=time.perf_counter();matches=service.search('What topic was I struggling with in CNN?');durations.append((time.perf_counter()-start)*1000)
                hits.append(bool(matches and matches[0]['memory_id']==m['memory_id']))
            results.append({'mode':mode,'raw_bytes':len(RAW.encode()),'summary_bytes':len(summary.encode()),
                'vector_value_bytes':embeddings.dimension*4,'retrieval_median_ms':round(statistics.median(durations),2),
                'retrieval_p95_ms':round(sorted(durations)[18],2),'retrieval_hits':sum(hits),'queries':len(hits),
                'scope':'One-memory fixture; relevance hit only, not general QA/faithfulness evaluation'})
            vectors.close()
    output={'embedding_model':embeddings.name,'results':results}
    Path('docs/BENCHMARK.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
