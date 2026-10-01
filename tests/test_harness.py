from fl_provider_adapter_kit import AdapterConformanceHarness, DemoAdapter


def test_demo_harness_passes_local_conformance() -> None:
    report = AdapterConformanceHarness().run()

    assert report.passed
    assert [scenario.scenario_id for scenario in report.scenarios] == [
        "FL-PAK-DUPLICATE-DISPATCH",
        "FL-PAK-RESPONSE-LOSS",
        "FL-PAK-STALE-VERIFIER",
        "FL-PAK-COMPENSATION-EXCEPTION",
    ]
    assert "no live provider credentials or network calls" in report.limitations


def test_duplicate_request_dispatches_once() -> None:
    adapter = DemoAdapter()
    report = AdapterConformanceHarness().run(lambda: adapter)  # type: ignore[arg-type]

    duplicate = report.scenarios[0]
    assert duplicate.passed
    assert "dispatch_count=1" in duplicate.details
