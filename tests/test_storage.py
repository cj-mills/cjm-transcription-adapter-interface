"""Tests for cjm_transcription_adapter_interface.storage — the canonical transcriptions table.

Projected from the storage notebook's test cells at the c25780e8 flip."""
import logging
import sqlite3

from cjm_substrate.utils.hashing import hash_bytes
from cjm_transcription_adapter_interface.storage import TranscriptionRow, TranscriptionStorage

AUDIO_HASH = "sha256:" + "e3b0c44298" * 6 + "e3b0"
CFG1 = "sha256:" + "1" * 64
TEST_TEXT = "Laying Plans Sun Tzu said, The art of war is of vital importance to the state."


def _seeded_storage(path):
    storage = TranscriptionStorage(str(path))
    storage.save(
        job_id="job_test_001",
        audio_path="/tmp/test_audio.mp3",
        audio_hash=AUDIO_HASH,
        config_hash=CFG1,
        text=TEST_TEXT,
        text_hash=hash_bytes(TEST_TEXT.encode()),
        segments=[{"start": 0.0, "end": 5.0, "text": TEST_TEXT}],
        metadata={"model": "whisper-large-v3", "language": "en"},
    )
    return storage


def test_row_dataclass():
    row = TranscriptionRow(
        job_id="job_abc123",
        audio_path="/tmp/test.mp3",
        audio_hash="sha256:" + "a" * 64,
        config_hash="sha256:" + "f" * 64,
        text="Hello world",
        text_hash="sha256:" + "b" * 64,
        segments=[{"start": 0.0, "end": 1.0, "text": "Hello world"}],
        metadata={"model": "whisper-large-v3"},
    )
    assert row.job_id == "job_abc123" and row.segments[0]["text"] == "Hello world"


def test_save_get_list_and_missing(tmp_path):
    storage = _seeded_storage(tmp_path / "t.db")
    row = storage.get_by_job_id("job_test_001")
    assert row is not None and row.job_id == "job_test_001"
    assert row.text == TEST_TEXT and row.text_hash == hash_bytes(TEST_TEXT.encode())
    assert row.audio_hash == AUDIO_HASH and row.segments is not None
    assert row.metadata["model"] == "whisper-large-v3" and row.created_at is not None

    assert storage.get_by_job_id("nonexistent") is None

    storage.save(job_id="job_test_002", audio_path="/tmp/test_audio_2.mp3",
                 audio_hash="sha256:" + "f" * 64, config_hash="sha256:" + "2" * 64,
                 text="Second transcription.", text_hash=hash_bytes(b"Second transcription."))
    jobs = storage.list_jobs()
    assert [j.job_id for j in jobs] == ["job_test_002", "job_test_001"]  # newest first


def test_get_cached_content_correct(tmp_path):
    storage = _seeded_storage(tmp_path / "t.db")
    hit = storage.get_cached("/tmp/test_audio.mp3", AUDIO_HASH, CFG1)
    assert hit is not None and hit.job_id == "job_test_001"
    # Changed audio content -> miss; different config -> miss
    assert storage.get_cached("/tmp/test_audio.mp3", "sha256:" + "9" * 64, CFG1) is None
    assert storage.get_cached("/tmp/test_audio.mp3", AUDIO_HASH, "sha256:" + "0" * 64) is None


def test_insert_or_replace_on_cache_key(tmp_path):
    s2 = TranscriptionStorage(str(tmp_path / "r.db"))
    s2.save(job_id="r1", audio_path="/tmp/a.wav", audio_hash="sha256:" + "a" * 64,
            config_hash="sha256:" + "c" * 64, text="v1", text_hash=hash_bytes(b"v1"))
    # Same audio_path + config, changed audio content -> replaces the stale row
    s2.save(job_id="r2", audio_path="/tmp/a.wav", audio_hash="sha256:" + "b" * 64,
            config_hash="sha256:" + "c" * 64, text="v2", text_hash=hash_bytes(b"v2"))
    rows = s2.list_jobs()
    assert len(rows) == 1 and rows[0].job_id == "r2"
    assert s2.get_cached("/tmp/a.wav", "sha256:" + "a" * 64, "sha256:" + "c" * 64) is None
    assert s2.get_cached("/tmp/a.wav", "sha256:" + "b" * 64, "sha256:" + "c" * 64).job_id == "r2"


def test_pre_cache_schema_migration_and_dedup(tmp_path):
    # A pre-cache table (no config_hash, duplicate-audio rows) gains config_hash
    # on open AND de-dups so the UNIQUE cache index can build (newest kept).
    db = tmp_path / "m.db"
    with sqlite3.connect(db) as con:
        con.execute("""
            CREATE TABLE transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                audio_path TEXT NOT NULL,
                audio_hash TEXT NOT NULL,
                text TEXT NOT NULL,
                text_hash TEXT NOT NULL,
                segments JSON,
                metadata JSON,
                created_at REAL NOT NULL
            )
        """)
        con.executemany(
            "INSERT INTO transcriptions (job_id, audio_path, audio_hash, text, text_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [("dup_old", "/tmp/a.wav", "sha256:a1", "old", "sha256:t1", 0.0),
             ("dup_new", "/tmp/a.wav", "sha256:a2", "new", "sha256:t2", 1.0),
             ("uniq", "/tmp/b.wav", "sha256:b1", "other", "sha256:t3", 2.0)],
        )

    s3 = TranscriptionStorage(str(db))  # __init__ migrates + de-dups + builds the index
    with sqlite3.connect(db) as con:
        cols = {r[1] for r in con.execute("PRAGMA table_info(transcriptions)")}
    assert "config_hash" in cols
    assert s3.get_by_job_id("dup_old") is None
    assert s3.get_by_job_id("dup_new") is not None
    assert s3.get_by_job_id("uniq") is not None
    assert len(s3.list_jobs()) == 2

    s3.save(job_id="new", audio_path="/tmp/new.wav", audio_hash="sha256:new",
            config_hash="sha256:cfg", text="new", text_hash=hash_bytes(b"new"))
    assert s3.get_cached("/tmp/new.wav", "sha256:new", "sha256:cfg").job_id == "new"


def test_save_with_logging_success_and_swallowed_failure(tmp_path):
    storage = _seeded_storage(tmp_path / "t.db")
    logger = logging.getLogger("transcription_storage_test")

    ok = storage.save_with_logging(
        job_id="job_test_swl", audio_path="/tmp/test_audio_swl.mp3",
        audio_hash="sha256:" + "c" * 64, config_hash="sha256:" + "3" * 64,
        text="Logged save.", text_hash=hash_bytes(b"Logged save."), logger=logger)
    assert ok is True and storage.get_by_job_id("job_test_swl") is not None

    # Failure path: if save() raises, the helper logs + returns False (swallowed).
    orig_save = storage.save

    def _boom(**kwargs):
        raise RuntimeError("simulated DB failure")

    storage.save = _boom
    try:
        ok_fail = storage.save_with_logging(
            job_id="job_fail", audio_path="/tmp/x.mp3",
            audio_hash="sha256:" + "d" * 64, config_hash="sha256:" + "4" * 64,
            text="x", text_hash=hash_bytes(b"x"), logger=logger)
    finally:
        storage.save = orig_save
    assert ok_fail is False


def test_verify_text_tamper_detection(tmp_path):
    db = tmp_path / "t.db"
    storage = _seeded_storage(db)
    assert storage.verify_text("job_test_001") is True

    with sqlite3.connect(db) as con:
        con.execute("UPDATE transcriptions SET text = 'TAMPERED' WHERE job_id = 'job_test_001'")
    assert storage.verify_text("job_test_001") is False
    assert storage.verify_text("nonexistent") is None
