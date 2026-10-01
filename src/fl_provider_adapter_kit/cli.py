from __future__ import annotations

import argparse
import json

from .harness import AdapterConformanceHarness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fl-provider-kit")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="run the local demo conformance harness")
    demo.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    if args.command == "demo":
        report = AdapterConformanceHarness().run()
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        else:
            print(f"{report.component} {report.version}: passed={report.passed}")
            for scenario in report.scenarios:
                print(f"- {scenario.scenario_id}: {scenario.passed} ({scenario.details})")
        return 0 if report.passed else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

