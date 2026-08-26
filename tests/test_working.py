from swarmmemory.working import WorkingScratchpad

def test_put_and_get():
    pad = WorkingScratchpad()
    pad.put("key1", {"data": 123}, "agent1")
    
    entry = pad.get("key1")
    assert entry is not None
    assert entry.key == "key1"
    assert entry.value == {"data": 123}
    assert entry.owner_agent_id == "agent1"
    assert entry.version == 1

def test_put_updates_version():
    pad = WorkingScratchpad()
    pad.put("key2", "val1", "agent1")
    pad.put("key2", "val2", "agent2")
    
    entry = pad.get("key2")
    assert entry is not None
    assert entry.value == "val2"
    assert entry.owner_agent_id == "agent2"
    assert entry.version == 2

def test_cas_success():
    pad = WorkingScratchpad()
    pad.put("key3", "val1", "agent1")
    
    success = pad.cas("key3", 1, "val2", "agent1")
    assert success is True
    
    entry = pad.get("key3")
    assert entry.version == 2
    assert entry.value == "val2"

def test_cas_conflict():
    pad = WorkingScratchpad()
    pad.put("key4", "val1", "agent1")
    
    # Another agent updates it
    pad.put("key4", "val2", "agent2")
    
    # First agent tries to CAS with old version
    success = pad.cas("key4", 1, "val3", "agent1")
    assert success is False
    
    entry = pad.get("key4")
    assert entry.version == 2
    assert entry.value == "val2"

def test_list_keys():
    pad = WorkingScratchpad()
    pad.put("prefix_1", "a", "agent1")
    pad.put("prefix_2", "b", "agent1")
    pad.put("other_1", "c", "agent1")
    
    keys = pad.list_keys("prefix")
    assert set(keys) == {"prefix_1", "prefix_2"}

def test_clear():
    pad = WorkingScratchpad()
    pad.put("k1", "v1", "agent1")
    pad.put("k2", "v2", "agent2")
    
    count = pad.clear("agent1")
    assert count == 1
    
    assert pad.get("k1") is None
    assert pad.get("k2") is not None
