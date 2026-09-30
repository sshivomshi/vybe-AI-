"""Multi-topic synthetic retrieval evaluation; no general quality claims."""
import json,statistics,tempfile,time
from pathlib import Path
from backend.config import Settings
from backend.vectors import Embeddings,VectorRepository
from backend.storage import Store
from backend.memory import MemoryService
from backend.models import MemoryInput
CASES=[
('Food','I am allergic to peanuts and avoid all peanut products.','What food allergy must my meals respect?'),
('Travel','My flight to Tokyo leaves on Friday morning.','When do I fly to Japan?'),
('Study','I understand convolution but still need to revise backpropagation for my CNN exam.','Which neural network topic needs revision?'),
('Exercise','My physiotherapist advised swimming instead of running because of knee pain.','Which exercise is suitable for my injured knee?'),
('Work','The budget report is due next Tuesday before noon.','When must I submit the finance report?'),
('Language','I am learning Spanish and have completed the past tense lessons.','How far have I progressed with Spanish grammar?'),
('Garden','The basil plant needs watering every two days.','How often should I water my kitchen herb?'),
('Reading','I prefer science fiction novels with space exploration.','What kind of novels do I enjoy?'),
('Code','My application backend uses Python and PostgreSQL.','What language and database power my server?'),
('Music','I practice piano for thirty minutes every evening.','What is my daily musical practice routine?')]
def main():
 e=Embeddings(Settings());rows=[]
 with tempfile.TemporaryDirectory(prefix='ps3-evaluation-') as root:
  v=VectorRepository(Path(root)/'edge',e);m=MemoryService(Store(Path(root)/'db'),v)
  targets=[m.save(MemoryInput(title=t,summary=s))['memory_id'] for t,s,q in CASES]
  for i in range(90):m.save(MemoryInput(title=f'Inventory item {i}',summary=f'Storage box number {i} contains spare cables and office stationery with inventory label item-{i}.'))
  for (t,s,q),target in zip(CASES,targets):
   times=[];hits=[]
   for repeat in range(3):
    start=time.perf_counter();hits=m.search(q,5);times.append((time.perf_counter()-start)*1000)
   ids=[h['memory_id'] for h in hits];rank=ids.index(target)+1 if target in ids else None
   rows.append(dict(topic=t,rank=rank,median_ms=round(statistics.median(times),2)))
  v.close()
 report=dict(scope='100 synthetic memories, 10 hand-labeled paraphrases, three timings each; not a production or generated-answer quality evaluation',top1=sum(r['rank']==1 for r in rows)/len(rows),recall_at5=sum(r['rank'] is not None for r in rows)/len(rows),results=rows)
 Path('docs/RETRIEVAL_EVALUATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
