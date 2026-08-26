import time
from swarmmemory.episodic import EpisodicStore
from swarmmemory.types import Episode, MemoryQuery

def test_store_and_recall_basic():
    store = EpisodicStore()
    ep = Episode(
        episode_id="ep1",
        agent_id="agent1",
        event_type="log",
        content="System started successfully.",
        metadata={},
        timestamp=time.time(),
        tags=["system"]
    )
    store.store(ep)
    
    results = store.recall(MemoryQuery(text="started"))
    assert len(results) == 1
    assert results[0].episode_id == "ep1"

def test_store_and_recall_tags():
    store = EpisodicStore()
    ep = Episode(
        episode_id="ep2",
        agent_id="agent1",
        event_type="error",
        content="Crash detected.",
        metadata={},
        timestamp=time.time(),
        tags=["error", "critical"]
    )
    store.store(ep)
    
    results = store.recall(MemoryQuery(text="Crash", tags=["error"]))
    assert len(results) == 1
    
    results_empty = store.recall(MemoryQuery(text="Crash", tags=["warning"]))
    assert len(results_empty) == 0

def test_forget():
    store = EpisodicStore()
    ep = Episode(
        episode_id="ep3",
        agent_id="agent2",
        event_type="msg",
        content="Delete me.",
        metadata={},
        timestamp=time.time()
    )
    store.store(ep)
    store.forget("ep3")
    
    results = store.recall(MemoryQuery(text="Delete"))
    assert len(results) == 0

def test_gc():
    store = EpisodicStore()
    old_time = time.time() - (40 * 24 * 60 * 60) # 40 days old
    ep = Episode(
        episode_id="ep4",
        agent_id="agent2",
        event_type="msg",
        content="Old message.",
        metadata={},
        timestamp=old_time
    )
    store.store(ep)
    
    count = store.gc(max_age_days=30)
    assert count == 1
    
    results = store.recall(MemoryQuery(text="Old"))
    assert len(results) == 0
