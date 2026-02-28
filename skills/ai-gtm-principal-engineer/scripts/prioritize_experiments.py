#!/usr/bin/env python3
"""Prioritize GTM experiments using weighted business scoring."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import yaml


TEXT_SCALE = {
    "very low": 1.0,
    "low": 1.5,
    "medium": 2.5,
    "high": 3.5,
    "very high": 4.5,
}

RISK_SCALE = {
    "very low": 1.0,
    "low": 1.5,
    "medium": 2.5,
    "high": 3.5,
    "critical": 4.5,
}

TIME_TO_SIGNAL_SCALE = {
    "short": 3.0,
    "medium": 2.0,
    "long": 1.0,
}


class PriorityError(RuntimeError):
    pass


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_scaled(value: Any, scale: dict[str, float], default: float = 2.5) -> float:
    if value is None:
        return default

    numeric = parse_float(value)
    if numeric is not None:
        return clamp(numeric, 0.0, 5.0)

    key = str(value).strip().lower()
    return scale.get(key, default)


def infer_impact(exp: dict[str, Any]) -> float:
    if "impact" in exp:
        explicit = parse_float(exp.get("impact"))
        if explicit is not None:
            return clamp(explicit, 0.0, 5.0)

        return parse_scaled(exp.get("impact"), TEXT_SCALE)

    baseline = parse_float(exp.get("baseline"))
    target = parse_float(exp.get("target"))

    if baseline is None or target is None:
        return 2.0

    denom = abs(baseline) if abs(baseline) > 1e-9 else 1.0
    relative_move = abs(target - baseline) / denom
    return clamp(relative_move * 5.0, 0.5, 5.0)


def load_input(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    data: Any

    if path.suffix.lower() == ".json":
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw)

    if isinstance(data, dict):
        experiments = data.get("experiments")
    else:
        experiments = data

    if not isinstance(experiments, list):
        raise PriorityError("Input must be a list of experiments or an object with an 'experiments' list")

    out: list[dict[str, Any]] = []
    for item in experiments:
        if isinstance(item, dict):
            out.append(item)
    return out


def recommendation(score: float, risk: float) -> str:
    if score >= 2.3 and risk <= 2.0:
        return "ship-now"
    if score >= 1.5:
        return "prototype"
    return "defer"


def score_experiment(
    exp: dict[str, Any],
    w_impact: float,
    w_confidence: float,
    w_fit: float,
    w_effort: float,
    w_risk: float,
    w_time: float,
) -> dict[str, Any]:
    impact = infer_impact(exp)
    confidence = parse_scaled(exp.get("confidence"), TEXT_SCALE)
    strategic_fit = parse_scaled(exp.get("strategic_fit"), TEXT_SCALE)
    effort = parse_scaled(exp.get("implementation_effort"), TEXT_SCALE)
    risk = parse_scaled(exp.get("risk"), RISK_SCALE)
    time_signal = parse_scaled(exp.get("time_to_signal"), TIME_TO_SIGNAL_SCALE, default=2.0)

    score = (
        impact * w_impact
        + confidence * w_confidence
        + strategic_fit * w_fit
        + time_signal * w_time
        - effort * w_effort
        - risk * w_risk
    )

    return {
        "id": str(exp.get("id", "")),
        "name": str(exp.get("name", "")),
        "metric": str(exp.get("metric", "")),
        "hypothesis": str(exp.get("hypothesis", "")),
        "impact": round(impact, 3),
        "confidence": round(confidence, 3),
        "strategic_fit": round(strategic_fit, 3),
        "effort": round(effort, 3),
        "risk": round(risk, 3),
        "time_to_signal": round(time_signal, 3),
        "score": round(score, 4),
        "recommendation": recommendation(score, risk),
    }


def write_csv(rows: list[dict[str, Any]], out_path: Path) -> None:
    fields = [
        "rank",
        "id",
        "name",
        "metric",
        "score",
        "recommendation",
        "impact",
        "confidence",
        "strategic_fit",
        "effort",
        "risk",
        "time_to_signal",
        "hypothesis",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            data = dict(row)
            data["rank"] = idx
            writer.writerow(data)


def write_markdown(rows: list[dict[str, Any]], out_path: Path, top: int) -> None:
    lines = [
        "# Experiment Prioritization",
        "",
        "| Rank | Experiment | Score | Recommendation | Primary metric |",
        "|---:|---|---:|---|---|",
    ]

    for idx, row in enumerate(rows[:top], start=1):
        lines.append(
            f"| {idx} | {row['name'] or row['id']} | {row['score']:.3f} | {row['recommendation']} | {row['metric']} |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prioritize GTM experiments")
    parser.add_argument("--in", dest="input_path", required=True, help="YAML or JSON file with experiments")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--summary", help="Optional markdown summary path")
    parser.add_argument("--top", type=int, default=10, help="Rows to include in markdown summary")

    parser.add_argument("--w-impact", type=float, default=0.35)
    parser.add_argument("--w-confidence", type=float, default=0.20)
    parser.add_argument("--w-fit", type=float, default=0.15)
    parser.add_argument("--w-effort", type=float, default=0.15)
    parser.add_argument("--w-risk", type=float, default=0.10)
    parser.add_argument("--w-time", type=float, default=0.05)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_path).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not input_path.exists():
        raise PriorityError(f"Input not found: {input_path}")

    experiments = load_input(input_path)
    scored = [
        score_experiment(
            exp,
            w_impact=args.w_impact,
            w_confidence=args.w_confidence,
            w_fit=args.w_fit,
            w_effort=args.w_effort,
            w_risk=args.w_risk,
            w_time=args.w_time,
        )
        for exp in experiments
    ]

    scored.sort(key=lambda x: x["score"], reverse=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(scored, out_path)

    if args.summary:
        summary_path = Path(args.summary).expanduser().resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(scored, summary_path, max(1, args.top))

    print(f"Scored {len(scored)} experiments -> {out_path}")
    if args.summary:
        print(f"Summary written -> {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
