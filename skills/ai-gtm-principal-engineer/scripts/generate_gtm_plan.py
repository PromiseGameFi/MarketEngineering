#!/usr/bin/env python3
"""Generate GTM strategy artifacts from a project spec."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml


class SpecError(RuntimeError):
    pass


def load_spec(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw)

    if not isinstance(data, dict):
        raise SpecError("Spec root must be an object")
    return data


def require_path(data: dict[str, Any], dotted_path: str) -> Any:
    cur: Any = data
    for part in dotted_path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise SpecError(f"Missing required field: {dotted_path}")
    return cur


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def md_list(items: list[Any], empty: str = "- none") -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def serialize_segment(segment: dict[str, Any]) -> str:
    name = segment.get("name", "unknown")
    pains = md_list(as_list(segment.get("pains")))
    committee = md_list(as_list(segment.get("buying_committee")))
    success = md_list(as_list(segment.get("success_metrics")))

    return (
        f"### {name}\n"
        f"**Pains**\n{pains}\n\n"
        f"**Buying committee**\n{committee}\n\n"
        f"**Success metrics**\n{success}\n"
    )


def render_strategy(spec: dict[str, Any], generated_at: str) -> str:
    project = require_path(spec, "project")
    product = require_path(spec, "product")
    icp = require_path(spec, "icp")
    value_hypothesis = require_path(spec, "value_hypothesis")
    pricing = require_path(spec, "pricing_packaging")
    gtm = require_path(spec, "go_to_market")
    instr = require_path(spec, "instrumentation")

    project_name = project.get("name", "unnamed-project")
    owner = project.get("owner", "unassigned")
    stage = project.get("stage", "unknown")
    date = project.get("date", generated_at)
    region_focus = md_list(as_list(project.get("region_focus")))

    use_cases = md_list(as_list(product.get("use_cases")))
    constraints = md_list(as_list(product.get("constraints")))

    primary_segment = icp.get("primary_segment", {})
    icp_section = serialize_segment(primary_segment)

    statement = value_hypothesis.get("statement", "")
    proof_window = value_hypothesis.get("value_proof_window_days", "n/a")

    channels = md_list(as_list(gtm.get("channels")))
    enablement_assets = md_list(as_list(gtm.get("enablement_assets")))
    product_events = md_list(as_list(instr.get("product_events")))
    funnel_events = md_list(as_list(instr.get("funnel_events")))

    risks = md_list(as_list(spec.get("risks")))

    return f"""# GTM Strategy Plan: {project_name}

Generated: {generated_at}

## 1. Program Snapshot
- Owner: {owner}
- Stage: {stage}
- Plan date: {date}
- Region focus:
{region_focus}

## 2. Product and Use-Case Thesis
- Category: {product.get("category", "unknown")}
- Priority use cases:
{use_cases}
- Operating constraints:
{constraints}

## 3. ICP and Buying System
{icp_section}

## 4. Value Hypothesis and Proof Path
- Core hypothesis: {statement}
- Value proof window: {proof_window} days

## 5. Offer, Pricing, and Motion
- Motion: {pricing.get("motion", "unknown")}
- Entry offer: {pricing.get("entry_offer", "unknown")}
- Core plan: {pricing.get("core_plan", "unknown")}
- Enterprise add-on: {pricing.get("enterprise_addon", "unknown")}
- Channels:
{channels}
- Sales motion: {gtm.get("sales_motion", "unknown")}

## 6. Enablement and Collateral Requirements
{enablement_assets}

## 7. Instrumentation Architecture
### Product events
{product_events}

### Funnel events
{funnel_events}

## 8. Risk Register (Initial)
{risks}

## 9. 90-Day Execution Cadence
- Week 1-2: Baseline instrumentation and launch-gate alignment.
- Week 3-4: First two high-priority experiments launched.
- Week 5-8: Iterate based on readouts, enforce kill/scale decisions.
- Week 9-12: Standardize playbooks and package expansion motion.
"""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def write_experiment_csv(spec: dict[str, Any], out_path: Path) -> None:
    experiments = as_list(spec.get("experiments"))
    fieldnames = [
        "id",
        "name",
        "hypothesis",
        "metric",
        "baseline",
        "target",
        "confidence",
        "implementation_effort",
        "risk",
    ]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in experiments:
            if not isinstance(item, dict):
                continue
            writer.writerow({k: normalize_text(item.get(k)) for k in fieldnames})


def write_launch_gates(out_path: Path) -> None:
    content = """# Launch Gates

## Gate A: Commercial readiness
- ICP and pain statement validated with at least 10 target conversations.
- Offer and pricing hypothesis documented.
- Sales/CS ownership map complete.

## Gate B: AI quality readiness
- Eval suite defined for top tasks.
- Quality thresholds agreed (task success, hallucination/grounding, escalation).
- Incident and fallback behavior tested.

## Gate C: Trust and compliance readiness
- Data handling paths documented.
- Security artifacts prepared for buyer review.
- Regional/policy constraints reviewed for launch geographies.

## Gate D: Operational readiness
- Product + CRM instrumentation validated.
- Dashboard and weekly readout in place.
- Rollback and customer communication runbook approved.
"""
    out_path.write_text(content, encoding="utf-8")


def write_scorecard(out_path: Path) -> None:
    content = """# GTM Scorecard

| Metric | Baseline | Current | Target | Direction | Owner |
|---|---:|---:|---:|---|---|
| Activation rate |  |  |  | up |  |
| Pilot start rate |  |  |  | up |  |
| Pilot to production conversion |  |  |  | up |  |
| Win rate |  |  |  | up |  |
| TTFV (days) |  |  |  | down |  |
| Hallucination rate |  |  |  | down |  |
| Escalation rate |  |  |  | down |  |
"""
    out_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate principal-level GTM artifacts")
    parser.add_argument("--spec", required=True, help="Path to YAML/JSON GTM spec")
    parser.add_argument("--out", required=True, help="Output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec_path = Path(args.spec).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    if not spec_path.exists():
        raise SpecError(f"Spec not found: {spec_path}")

    spec = load_spec(spec_path)
    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    out_dir.mkdir(parents=True, exist_ok=True)

    strategy_path = out_dir / "gtm-strategy-plan.md"
    strategy_path.write_text(render_strategy(spec, generated_at), encoding="utf-8")

    write_experiment_csv(spec, out_dir / "experiment-backlog.csv")
    write_launch_gates(out_dir / "launch-gates.md")
    write_scorecard(out_dir / "gtm-scorecard.md")

    print(f"Generated GTM artifacts in: {out_dir}")
    print("- gtm-strategy-plan.md")
    print("- experiment-backlog.csv")
    print("- launch-gates.md")
    print("- gtm-scorecard.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
