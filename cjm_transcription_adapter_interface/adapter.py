"""The typed transcription task contract — TranscriptionAdapter ABC + the REAL structural tool protocol (capability-unit Option C, pass-2 Thread 3; protocol born real at stage 8).

Canonical home (stage 8 / PILLAR 1c): the data noun is imported directly from
cjm_capability_primitives, not via the REMOVE-AFTER-OVERHAUL `.core` shim, so
the permanent ABC survives the shim's retirement."""

from abc import abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Dict, Protocol, runtime_checkable, Union

from cjm_capability_primitives.transcription import TranscriptionResult
from cjm_substrate.core.adapter import TaskAdapter


@runtime_checkable
class TranscriptionToolProtocol(Protocol):
    """Structural contract for transcription tool capabilities (BORN REAL at
    stage 8 — derived from the native tool surface, replacing the provisional
    `execute`-shaped mirror).

    Pure compute: `transcribe` loads the model + runs inference + builds the
    typed result. `get_current_config` supplies the effective config the
    generic adapter hashes for its cache key. Persistence is NOT here — the
    adapter owns it (the native-surface seam)."""
    def transcribe(self, audio: Union[str, Path], **kwargs) -> TranscriptionResult: ...
    def get_current_config(self) -> Dict[str, Any]: ...


class TranscriptionAdapter(TaskAdapter):
    """Typed transcription task adapter: model-ready audio in,
    `TranscriptionResult` out.

    Input contract (carried over from the fused-era TranscriptionPlugin):
    the caller guarantees MODEL-READY audio — format / sample-rate /
    channel handling happens upstream (ffmpeg `convert_for_model`), never
    in the adapter.

    Native-surface model (stage 8 / PILLAR 1c): the TOOL is pure compute;
    the ADAPTER owns the cache + persistence bookends (see
    `GenericTranscriptionAdapter`) + the per-call `force` control. Storage
    resolves from the substrate-injected `CAPABILITY_DATA_DIR`; `db_path` is not
    on the tool protocol.

    Implementations run in-worker beside their tool capability and are
    constructed with the bound tool instance: `AdapterClass(tool)` (mirrors
    `GraphStorageAdapter`). The result DTO is wire-registered
    ("transcription.result"): returned values cross the worker boundary typed.
    """

    task_name: ClassVar[str] = "transcription"
    required_tool_protocol: ClassVar[type] = TranscriptionToolProtocol

    def __init__(
        self,
        tool: TranscriptionToolProtocol,  # The bound tool capability instance (worker-side binding)
    ):
        self.tool = tool

    @abstractmethod
    def transcribe(
        self,
        audio: Union[str, Path],  # Path to MODEL-READY audio (converted upstream)
        **kwargs,                 # Provenance (job_id / source_*_time) + tool options
    ) -> TranscriptionResult:     # Typed transcription output
        """Transcribe model-ready audio to text."""
        ...
