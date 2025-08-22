from app.storage.state import StateStore


def test_state_roundtrip(tmp_path):
    db = tmp_path / 'state.sqlite'
    store = StateStore(path=db)
    key = 'CALL|2024-01-01T00:00:00Z|20m|SSB'
    assert store.get_by_key(key) is None
    store.upsert_attempt(1, key, error='x')
    rec = store.get_by_key(key)
    assert rec is not None
    assert rec['attempts'] == 1
    store.mark_sent(1, key, '/x.pdf', 'mid', '2024-01-01T00:00:00Z')
    rec2 = store.get_by_key(key)
    assert rec2 is not None
    assert rec2['email_message_id'] == 'mid'
    assert rec2['postcard_pdf_path'] == '/x.pdf'
