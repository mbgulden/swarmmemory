import sys
import time
from unittest.mock import patch

from swarmmemory.cli import main
from swarmmemory.episodic import EpisodicStore
from swarmmemory.types import Episode


def test_cli_query(capsys):
    test_args = ["swarmmemory", "query", "test", "--db", ":memory:"]
    with patch.object(sys, 'argv', test_args):
        main()
    captured = capsys.readouterr()
    assert captured.out == "" # Empty DB


def test_cli_stats(capsys, tmp_path):
    db = str(tmp_path / "memory.db")
    store = EpisodicStore(db)
    store.store(Episode(
        episode_id="ep1",
        agent_id="agent1",
        event_type="log",
        content="hello world",
        metadata={},
        timestamp=time.time(),
    ))
    test_args = ["swarmmemory", "stats", "--db", db]
    with patch.object(sys, 'argv', test_args):
        main()
    captured = capsys.readouterr()
    assert "Episodes: 1" in captured.out
    assert "Working entries: 0" in captured.out
