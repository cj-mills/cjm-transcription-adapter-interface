"""Tests for cjm_transcription_adapter_interface.adapter — the typed task contract.

Projected from the adapter notebook's shape-test cell at the c25780e8 flip."""
import pytest

from cjm_capability_primitives.transcription import TranscriptionResult
from cjm_transcription_adapter_interface.adapter import (TranscriptionAdapter,
                                                         TranscriptionToolProtocol)


class _FakeTool:  # structural match, no inheritance
    def transcribe(self, audio, **kwargs) -> TranscriptionResult:
        return TranscriptionResult(text=f"t:{audio}")

    def get_current_config(self):
        return {"model": "fake"}


class _FakeTranscriptionAdapter(TranscriptionAdapter):
    def transcribe(self, audio, **kwargs) -> TranscriptionResult:
        return self.tool.transcribe(audio, **kwargs)


def test_abstract_gate_and_concrete_impl():
    with pytest.raises(TypeError):
        TranscriptionAdapter(_FakeTool())  # abstract ABC must not instantiate

    impl = _FakeTranscriptionAdapter(_FakeTool())
    out = impl.transcribe("a.wav")
    assert isinstance(out, TranscriptionResult) and out.text == "t:a.wav"
    assert TranscriptionAdapter.task_name == "transcription"
    assert TranscriptionAdapter.required_tool_protocol is TranscriptionToolProtocol


def test_real_protocol_matches_migrated_not_fused_era():
    # The REAL protocol: transcribe + get_current_config (stage 8).
    assert isinstance(_FakeTool(), TranscriptionToolProtocol)

    class _FusedEraTool:
        def execute(self, audio, **kwargs):
            return {"text": "hi"}

    # the provisional execute-shaped tool no longer satisfies the REAL protocol
    assert not isinstance(_FusedEraTool(), TranscriptionToolProtocol)
