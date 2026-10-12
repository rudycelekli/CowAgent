import pytest
from agent.memory.conversation_store import ConversationStore, _live_runs

def test_duplicate_creation_does_not_revive_interrupted_run(tmp_path):
    store = ConversationStore(tmp_path / 'messages.db')
    run_id = 'test-stale-idempotent-run'
    try:
        assert store.create_run(run_id, session_id='session') is True
        _live_runs.discard(run_id)  # No executor survived the simulated restart.
        conn = store._connect()
        try:
            assert store._unfinished_runs(conn, 'session') == {run_id: 'interrupted'}
            assert store.create_run(run_id, session_id='session') is False
            assert store._unfinished_runs(conn, 'session') == {run_id: 'interrupted'}
        finally:
            conn.close()
    finally:
        _live_runs.discard(run_id)

def test_failed_serialization_does_not_register_live_run(tmp_path):
    store = ConversationStore(tmp_path / 'messages.db')
    run_id = 'test-unserializable-run'
    try:
        with pytest.raises(TypeError):
            store.create_run(run_id, extras={'value': object()})
        assert run_id not in _live_runs
        assert store.get_run(run_id) is None
    finally:
        _live_runs.discard(run_id)

def test_successful_creation_still_registers_running_work(tmp_path):
    store = ConversationStore(tmp_path / 'messages.db')
    run_id = 'test-new-live-run'
    try:
        assert store.create_run(run_id) is True
        assert run_id in _live_runs
        assert store.get_run(run_id)['status'] == 'running'
        assert store.finish_run(run_id) is True
        assert run_id not in _live_runs
    finally:
        _live_runs.discard(run_id)
