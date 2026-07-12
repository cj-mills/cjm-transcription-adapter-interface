"""Tests for cjm_transcription_adapter_interface.core — the REMOVE-AFTER-OVERHAUL shim.

Projected from the core notebook's verification cell at the c25780e8 flip."""
import json

import cjm_capability_primitives.transcription as _canonical
from cjm_substrate.core.wire import WIRE_KIND_KEY, wire_decode, wire_encode
from cjm_transcription_adapter_interface.core import TranscriptionResult


def test_shim_is_class_identical_and_wire_registered():
    # Class-identical re-export: ONE registration, shared class object.
    assert TranscriptionResult is _canonical.TranscriptionResult

    res = TranscriptionResult(text="shim round-trip")
    env = wire_encode(res)
    assert env[WIRE_KIND_KEY] == "transcription.result"
    back = wire_decode(json.loads(json.dumps(env)))
    assert isinstance(back, TranscriptionResult) and back == res
