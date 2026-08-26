import sys
import pytest
from unittest.mock import patch
from swarmmemory.cli import main

def test_cli_query(capsys):
    test_args = ["swarmmemory", "query", "test", "--db", ":memory:"]
    with patch.object(sys, 'argv', test_args):
        main()
    captured = capsys.readouterr()
    assert captured.out == "" # Empty DB

def test_cli_stats(capsys):
    test_args = ["swarmmemory", "stats", "--db", ":memory:"]
    with patch.object(sys, 'argv', test_args):
        main()
    captured = capsys.readouterr()
    assert "Stats logic here" in captured.out
