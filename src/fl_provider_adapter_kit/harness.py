"""Deterministic local conformance harness for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

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


def default_request() -> AdapterRequest:
    return AdapterRequest(
        provider="demo",
        action="refund",
        scope="tenant-local/demo-order-1",
        idempotency_key="idem-demo-1",
        payload_digest="sha256:payload",
    )


def default_context() -> AdapterContext:
    return AdapterContext(
        run_id="018f0000-0000-7000-8000-000000000001",
        effect_id="demo.refund:tenant-local/demo-order-1",
        authority_digest="sha256:authority",
        verifier_id="demo-verifier",
    )


@dataclass
class DemoAdapter:
    """In-memory reference adapter used by docs and tests."""

    dispatch_count: int = 0
    provider_mutated: bool = False
    compensated: bool = False
    stale_verification: bool = False
    compensation_raises: bool = False

    def _evidence(self, request: AdapterRequest, context: AdapterContext) -> AdapterEvidence:
        observed = "1970-01-01T00:00:00Z" if self.stale_verification else "2026-01-01T00:00:00Z"
        return AdapterEvidence(
            provider_reference=f"{request.provider}:{request.idempotency_key}",
            verifier_id=context.verifier_id,
            observed_at=observed,
            payload_digest=request.payload_digest,
        )

    def execute(self, request: AdapterRequest, context: AdapterContext) -> AdapterResult:
        if not self.provider_mutated:
            self.dispatch_count += 1
            self.provider_mutated = True
        return AdapterResult(EffectOutcome.SUCCEEDED, self._evidence(request, context))

    def verify(self, request: AdapterRequest, context: AdapterContext) -> AdapterResult:
        if not self.provider_mutated:
            return AdapterResult(EffectOutcome.UNKNOWN, message="provider mutation not visible")
        evidence = self._evidence(request, context)
        if self.stale_verification:
            return AdapterResult(EffectOutcome.STALE, evidence, "stale provider evidence")
        return AdapterResult(EffectOutcome.VERIFIED, evidence)

    def compensate(
        self, request: AdapterRequest, context: AdapterContext
    ) -> CompensationResult:
        if self.compensation_raises:
            raise RuntimeError("provider compensation failed after dispatch")
        self.compensated = True
        return CompensationResult(EffectOutcome.SUCCEEDED, self._evidence(request, context))

    def verify_compensation(
        self, request: AdapterRequest, context: AdapterContext
    ) -> CompensationResult:
        if not self.compensated:
            return CompensationResult(EffectOutcome.MANUAL_REVIEW, message="not compensated")
        return CompensationResult(EffectOutcome.VERIFIED, self._evidence(request, context))


@dataclass
class AdapterConformanceHarness:
    component: str = "FL-PAK"
    version: str = "0.1"
    limitations: tuple[str, ...] = field(
        default=(
            "local deterministic fixtures only",
            "no live provider credentials or network calls",
            "no production certification claim",
        )
    )

    def run(self, adapter_factory: type[EffectAdapter] | None = None) -> ConformanceReport:
        factory = adapter_factory or DemoAdapter
        request = default_request()
        context = default_context()
        scenarios = (
            self._duplicate_dispatch(factory(), request, context),
            self._response_loss(factory(), request, context),
            self._stale_verification(DemoAdapter(stale_verification=True), request, context),
            self._compensation_exception(
                DemoAdapter(compensation_raises=True), request, context
            ),
        )
        return ConformanceReport(self.component, self.version, scenarios, self.limitations)

    def _duplicate_dispatch(
        self, adapter: EffectAdapter, request: AdapterRequest, context: AdapterContext
    ) -> ConformanceScenarioResult:
        first = adapter.execute(request, context)
        second = adapter.execute(request, context)
        dispatch_count = getattr(adapter, "dispatch_count", None)
        passed = (
            first.outcome == EffectOutcome.SUCCEEDED
            and second.outcome == EffectOutcome.SUCCEEDED
            and dispatch_count == 1
        )
        return ConformanceScenarioResult(
            "FL-PAK-DUPLICATE-DISPATCH",
            "Duplicate request dispatches at most once for the same idempotency key.",
            passed,
            f"dispatch_count={dispatch_count}",
        )

    def _response_loss(
        self, adapter: EffectAdapter, request: AdapterRequest, context: AdapterContext
    ) -> ConformanceScenarioResult:
        adapter.execute(request, context)
        verification = adapter.verify(request, context)
        passed = verification.outcome in {EffectOutcome.VERIFIED, EffectOutcome.UNKNOWN}
        return ConformanceScenarioResult(
            "FL-PAK-RESPONSE-LOSS",
            "Post-dispatch ambiguity remains visible and is not blindly retried.",
            passed,
            f"verification={verification.outcome.value}",
        )

    def _stale_verification(
        self, adapter: EffectAdapter, request: AdapterRequest, context: AdapterContext
    ) -> ConformanceScenarioResult:
        adapter.execute(request, context)
        verification = adapter.verify(request, context)
        return ConformanceScenarioResult(
            "FL-PAK-STALE-VERIFIER",
            "Stale evidence must not become VERIFIED.",
            verification.outcome != EffectOutcome.VERIFIED,
            f"verification={verification.outcome.value}",
        )

    def _compensation_exception(
        self, adapter: EffectAdapter, request: AdapterRequest, context: AdapterContext
    ) -> ConformanceScenarioResult:
        try:
            adapter.compensate(request, context)
        except RuntimeError as exc:
            return ConformanceScenarioResult(
                "FL-PAK-COMPENSATION-EXCEPTION",
                "Compensation exceptions remain manual-review evidence.",
                True,
                str(exc),
            )
        return ConformanceScenarioResult(
            "FL-PAK-COMPENSATION-EXCEPTION",
            "Compensation exceptions remain manual-review evidence.",
            False,
            "adapter did not expose compensation failure",
        )

