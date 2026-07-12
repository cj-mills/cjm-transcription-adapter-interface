"""REMOVE-AFTER-OVERHAUL(option-c-cascade): class-identical legacy import surface; TranscriptionResult relocated to cjm_capability_primitives.transcription at execution stage 8 (Option C / PILLAR 1c — pure-compute tool capabilities depend on the data noun, never the adapter machinery)."""

from cjm_capability_primitives.transcription import TranscriptionResult

# REMOVE-AFTER-OVERHAUL(option-c-cascade): re-export shim; the class lives in
# cjm_capability_primitives.transcription (born-final home, relocated stage 8).
# The single @wire_type("transcription.result") registration lives in the
# canonical home — re-exporting here does NOT re-register. The tuple keeps the
# side-effect re-export import referenced so the canonical emit cannot prune
# it (DEC 7288c788).

__all__ = ["TranscriptionResult"]

_REEXPORTS = (TranscriptionResult,)
