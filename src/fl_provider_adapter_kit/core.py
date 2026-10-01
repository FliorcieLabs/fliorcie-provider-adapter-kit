"""Small provider adapter protocol types.

The kit deliberately models only provider-edge behavior. Runtime ownership such
as journaling, authority, contracts, and state transitions remains outside this
package.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Mapping, Protocol


class EffectOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class AdapterRequest:
    provider: str
    action: str
    scope: str
    idempotency_key: str
    payload_digest: str


@dataclass(frozen=True)
class AdapterContext:
    run_id: str
    effect_id: str
    authority_digest: str
    verifier_id: str


@dataclass(frozen=True)
class AdapterEvidence:
    provider_reference: str
    verifier_id: str
    observed_at: str
    payload_digest: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterResult:
    outcome: EffectOutcome
    evidence: AdapterEvidence | None = None
    message: str = ""


@dataclass(frozen=True)
class CompensationResult:
    outcome: EffectOutcome
    evidence: AdapterEvidence | None = None
    message: str = ""


class EffectAdapter(Protocol):
    def execute(self, request: AdapterRequest, context: AdapterContext) -> AdapterResult:
        """Dispatch the provider operation once."""

    def verify(self, request: AdapterRequest, context: AdapterContext) -> AdapterResult:
        """Read authoritative provider state without mutating it."""

    def compensate(
        self, request: AdapterRequest, context: AdapterContext
    ) -> CompensationResult:
        """Attempt explicit compensation for a prior provider mutation."""

    def verify_compensation(
        self, request: AdapterRequest, context: AdapterContext
    ) -> CompensationResult:
        """Verify the compensation result through provider evidence."""


@dataclass(frozen=True)
class ConformanceScenarioResult:
    scenario_id: str
    invariant: str
    passed: bool
    details: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ConformanceReport:
    component: str
    version: str
    scenarios: tuple[ConformanceScenarioResult, ...]
    limitations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(scenario.passed for scenario in self.scenarios)

    def to_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "version": self.version,
            "passed": self.passed,
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
            "limitations": list(self.limitations),
        }

