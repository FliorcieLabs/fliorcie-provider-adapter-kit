# Fliorcie Provider Adapter Kit

Local-first authoring kit for provider-specific consequential action adapters.

This package is intentionally small and dependency-free. It defines the adapter
protocol and a deterministic conformance harness for duplicate dispatch,
response loss, stale verification, and compensation failure. It does not call
live providers, load credentials, or certify production readiness.

## Boundary

- `FL-PAK`: provider adapter kit and local conformance only.
- LLMWitness owns runtime state, journaling, authority, idempotency reservation,
  verification state, and compensation state.
- Adapters translate provider APIs into the protocol. They do not decide global
  reliability semantics.
- A passing report means the local protocol fixtures behaved as expected. It is
  not a live-provider approval.

## Quick Start

```bash
python -m pip install -e .
python -m pytest
fl-provider-kit demo --json
```

## Adapter Lifecycle

An adapter implements:

- `execute`
- `verify`
- `compensate`
- `verify_compensation`

The conformance harness exercises failure cases and returns a report with
scenario-level outcomes, limitations, and no universal score.

