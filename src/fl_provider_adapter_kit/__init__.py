"""Provider adapter protocol and local conformance tools."""

from .core import (
    AdapterContext,
    AdapterEvidence,
    AdapterRequest,
    AdapterResult,
    CompensationResult,
    ConformanceReport,
    ConformanceScenarioResult,
    EffectAdapter,
    EffectOutcome,
)
from .harness import AdapterConformanceHarness, DemoAdapter

__all__ = [
    "AdapterContext",
    "AdapterConformanceHarness",
    "AdapterEvidence",
    "AdapterRequest",
    "AdapterResult",
    "CompensationResult",
    "ConformanceReport",
    "ConformanceScenarioResult",
    "DemoAdapter",
    "EffectAdapter",
    "EffectOutcome",
]

