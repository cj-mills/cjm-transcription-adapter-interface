"""Tests for cjm_transcription_adapter_interface.generic — cache/persistence bookends.

Projected from the generic notebook's bookends cell at the c25780e8 flip."""
from cjm_capability_primitives.transcription import TranscriptionResult
from cjm_substrate.core.wire import CallEnvelope, reset_call_envelope, set_call_envelope
from cjm_transcription_adapter_interface.generic import GenericTranscriptionAdapter


class _FakeTool:  # PURE COMPUTE: no cache, no persistence
    def __init__(self):
        self.calls = 0

    def get_current_config(self):
        return {"model": "fake-1"}

    def transcribe(self, audio, **kwargs) -> TranscriptionResult:
        self.calls += 1
        return TranscriptionResult(text=f"compute:{self.calls}",
                                   metadata={"src": kwargs.get("source_start_time")})


def test_cache_miss_hit_and_force(tmp_path, monkeypatch):
    monkeypatch.setenv("CAPABILITY_DATA_DIR", str(tmp_path))
    wav = tmp_path / "in.wav"
    wav.write_bytes(b"audiobytes")

    tool = _FakeTool()
    ad = GenericTranscriptionAdapter(tool)

    # 1. cache MISS -> compute (calls=1) + persist
    r1 = ad.transcribe(str(wav), job_id="j1", source_start_time=1.0)
    assert tool.calls == 1 and r1.text == "compute:1"

    # 2. cache HIT -> no recompute, same text
    r2 = ad.transcribe(str(wav), job_id="j2")
    assert tool.calls == 1, f"expected cache hit, calls={tool.calls}"
    assert r2.text == r1.text

    # 3. force via CallEnvelope.control -> bypass cache, recompute (calls=2)
    tok = set_call_envelope(CallEnvelope(job_id="j3", control={"force": True}))
    try:
        ad.transcribe(str(wav))
    finally:
        reset_call_envelope(tok)
    assert tool.calls == 2, f"force should bypass cache, calls={tool.calls}"
