from backend.memory import MemoryService
from backend.models import MemoryInput
from backend.storage import Store


def test_duplicate_memories_stay_with_their_source_chat(tmp_path):
    service = MemoryService(Store(tmp_path))
    first = MemoryInput(title='Preference', summary='Prefers concise answers', source_chat_id='chat-a')
    a = service.save(first)
    assert service.save(first)['memory_id'] == a['memory_id']
    b = service.save(first.model_copy(update={'source_chat_id': 'chat-b'}))
    manual = service.save(first.model_copy(update={'source_chat_id': None}))
    assert len({a['memory_id'], b['memory_id'], manual['memory_id']}) == 3
    assert service.store.get(a['memory_id'])['source_chat_id'] == 'chat-a'
