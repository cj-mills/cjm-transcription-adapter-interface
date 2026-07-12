# cjm-transcription-adapter-interface

<!-- generated from the context graph by `cjm-context-graph readme` — do not edit by hand; edit the graph (the urge to hand-edit = move it on-graph) -->

Typed transcription task-adapter interface — TranscriptionAdapter ABC, the generic cache/persist adapter, the REMOVE-AFTER-OVERHAUL core shim, and transcription persistence helpers.

## Modules

- **`cjm_transcription_adapter_interface.adapter`**
- **`cjm_transcription_adapter_interface.core`** — REMOVE-AFTER-OVERHAUL(option-c-cascade): class-identical legacy import surface; TranscriptionResult relocated to cjm_capability_primitives.transcription at execution stage 8 (Option C / PILLAR 1c — pure-compute tool capabilities depend on the data noun, never the adapter machinery).
- **`cjm_transcription_adapter_interface.generic`** — The generic (tool-agnostic) transcription adapter — cache-check, invoke the bound tool's pure-compute transcribe, persist. Reused across every tool capability satisfying TranscriptionToolProtocol (whisper, voxtral, ...), exactly as GenericGraphStorageAdapter is reused across graph backends.
- **`cjm_transcription_adapter_interface.storage`**

## API

### `cjm_transcription_adapter_interface.adapter`

- `TranscriptionAdapter` _class_ — Typed transcription task adapter: model-ready audio in,
- `TranscriptionToolProtocol` _class_ — Structural contract for transcription tool capabilities (BORN REAL at

### `cjm_transcription_adapter_interface.generic`

- `GenericTranscriptionAdapter` _class_ — Generic transcription adapter: cache-check -> pure-compute tool -> persist.

### `cjm_transcription_adapter_interface.storage`

- `TranscriptionRow` _class_ — A single row from the transcriptions table.
- `TranscriptionStorage` _class_ — Standardized SQLite storage for transcription results.

## Dependencies

**Depends on:** `cjm-substrate`
