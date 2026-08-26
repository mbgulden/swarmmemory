import time
from swarmmemory.episodic import EpisodicStore
from swarmmemory.working import WorkingScratchpad
from swarmmemory.index import MemoryIndex
from swarmmemory.types import Episode, MemoryQuery

def test_search():
    ep_store = EpisodicStore()
    w_store = WorkingScratchpad()
    index = MemoryIndex(ep_store, w_store)
    
    ep = Episode(
        episode_id="idx_ep1",
        agent_id="ag1",
        event_type="log",
        content="Testing index search capabilities",
        metadata={},
        timestamp=time.time()
    )
    ep_store.store(ep)
    
    results = index.search(MemoryQuery(text="capabilities"))
    assert len(results) == 1
    assert getattr(results[0], 'episode_id', None) == "idx_ep1"

def test_stats():
    ep_store = EpisodicStore()
    w_store = WorkingScratchpad()
    index = MemoryIndex(ep_store, w_store)
    
    ep_store.store(Episode("1", "a", "e", "c", {}, time.time()))
    w_store.put("k1", "v1", "a")
    w_store.put("k2", "v2", "b")
    
    stats = index.stats()
    assert stats.total_episodes == 1
    assert stats.total_working_entries == 2
    assert stats.total_semantic_nodes == 0

def test_export_context():
    ep_store = EpisodicStore()
    w_store = WorkingScratchpad()
    index = MemoryIndex(ep_store, w_store)
    
    ep = Episode("1", "ag1", "log", "Important context here", {}, 1000.0)
    ep_store.store(ep)
    
    ctx = index.export_context(MemoryQuery(text="Important"))
    assert "Important context here" in ctx
    assert "ag1" in ctx
    assert "[1000.0]" in ctx
