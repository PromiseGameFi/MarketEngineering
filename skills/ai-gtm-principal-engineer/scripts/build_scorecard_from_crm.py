#!/usr/bin/env python3
"""Build a GTM scorecard from CRM/export CSV data."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
from pathlib import Path
from typing import Any

import yaml


DEFAULT_MAPPING = {
    "account_id": "account_id",
    "mql_date": "mql_date",
    "sql_date": "sql_date",
    "opportunity_date": "opportunity_date",
    "close_date": "close_date",
    "close_status": "close_status",
    "deal_amount": "deal_amount",
    "signup_date": "signup_date",
    "first_value_date": "first_value_date",
    "proven_value_date": "proven_value_date",
    "pilot_start_date": "pilot_start_date",
    "production_date": "production_date",
    "ai_sessions": "ai_sessions",
    "ai_escalations": "ai_escalations",
    "ai_audited_responses": "ai_audited_responses",
    "ai_hallucinations": "ai_hallucinations",
}

WON_STATUSES = {"won", "closed_won", "closed won", "won deal"}
LOST_STATUSES = {"lost", "closed_lost", "closed lost", "lost deal"}

PERCENT_METRICS = {
    "mql_to_sql_conversion",
    "sql_to_opportunity_conversion",
    "opportunity_win_rate",
    "activation_rate",
    "pilot_to_production_conversion",
    "escalation_rate",
    "hallucination_rate",
    "grounded_response_rate",
}

DAY_METRICS = {
    "avg_sales_cycle_days",
    "ttfv_days",
    "ttpv_days",
}

CURRENCY_METRICS = {
    "avg_deal_size",
    "pipeline_velocity",
}


class ScorecardError(RuntimeError):
    pass


def load_structured_file(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    return yaml.safe_load(raw)


def load_mapping(path: Path | None) -> dict[str, str]:
    mapping = dict(DEFAULT_MAPPING)
    if path is None:
        return mapping

    data = load_structured_file(path)
    if not isinstance(data, dict):
        raise ScorecardError("Mapping file must be an object")

    for key, value in data.items():
        if key in DEFAULT_MAPPING and isinstance(value, str) and value.strip():
            mapping[key] = value.strip()
    return mapping


def load_targets(path: Path | None) -> dict[str, float]:
    if path is None:
        return {}

    data = load_structured_file(path)
    if not isinstance(data, dict):
        raise ScorecardError("Targets file must be an object")

    targets: dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            val = value.get("target")
        else:
            val = value

        parsed = parse_float(val)
        if parsed is not None:
            targets[str(key)] = parsed
    return targets


def parse_date(value: Any) -> dt.date | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
    ):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    try:
        # Support ISO timestamp strings like 2026-02-28T10:00:00Z.
        normalized = text.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def safe_div(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.median(values)


def get_value(row: dict[str, Any], key: str, mapping: dict[str, str]) -> Any:
    return row.get(mapping[key])


def has_date(row: dict[str, Any], key: str, mapping: dict[str, str]) -> bool:
    return parse_date(get_value(row, key, mapping)) is not None


def normalize_status(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def days_between(start: dt.date | None, end: dt.date | None) -> float | None:
    if start is None or end is None:
        return None
    delta = (end - start).days
    if delta < 0:
        return None
    return float(delta)


def format_metric(metric: str, value: float | None) -> str:
    if value is None:
        return "n/a"
    if metric in PERCENT_METRICS:
        return f"{value * 100:.1f}%"
    if metric in DAY_METRICS:
        return f"{value:.1f}"
    if metric in CURRENCY_METRICS:
        return f"${value:,.2f}"
    return f"{value:.3f}"


def evaluate_status(metric: str, current: float | None, target: float | None, direction: str) -> str:
    if current is None:
        return "no-data"
    if target is None:
        return "no-target"

    # 5% tolerance band for watch state.
    if direction == "up":
        if current >= target:
            return "on-track"
        if current >= target * 0.95:
            return "watch"
        return "off-track"

    if current <= target:
        return "on-track"
    if current <= target * 1.05:
        return "watch"
    return "off-track"


def metric_definitions() -> dict[str, dict[str, str]]:
    return {
        "mql_to_sql_conversion": {
            "label": "MQL -> SQL conversion",
            "direction": "up",
            "definition": "SQL accounts / MQL accounts",
        },
        "sql_to_opportunity_conversion": {
            "label": "SQL -> Opportunity conversion",
            "direction": "up",
            "definition": "Opportunity accounts / SQL accounts",
        },
        "opportunity_win_rate": {
            "label": "Opportunity win rate",
            "direction": "up",
            "definition": "Won opportunities / closed opportunities",
        },
        "avg_sales_cycle_days": {
            "label": "Average sales cycle days",
            "direction": "down",
            "definition": "Average days from opportunity_date to close_date",
        },
        "avg_deal_size": {
            "label": "Average deal size",
            "direction": "up",
            "definition": "Average deal amount for opportunity rows",
        },
        "pipeline_velocity": {
            "label": "Pipeline velocity",
            "direction": "up",
            "definition": "(Qualified opportunities * win rate * avg deal size) / avg sales cycle days",
        },
        "activation_rate": {
            "label": "Activation rate",
            "direction": "up",
            "definition": "Accounts with first_value_date / accounts with signup_date",
        },
        "ttfv_days": {
            "label": "TTFV (median days)",
            "direction": "down",
            "definition": "Median days from signup_date to first_value_date",
        },
        "ttpv_days": {
            "label": "TTPV (median days)",
            "direction": "down",
            "definition": "Median days from signup_date to proven_value_date",
        },
        "pilot_to_production_conversion": {
            "label": "Pilot -> Production conversion",
            "direction": "up",
            "definition": "Accounts with production_date / accounts with pilot_start_date",
        },
        "escalation_rate": {
            "label": "Escalation rate",
            "direction": "down",
            "definition": "Total ai_escalations / total ai_sessions",
        },
        "hallucination_rate": {
            "label": "Hallucination rate",
            "direction": "down",
            "definition": "Total ai_hallucinations / total ai_audited_responses",
        },
        "grounded_response_rate": {
            "label": "Grounded response rate",
            "direction": "up",
            "definition": "1 - hallucination_rate",
        },
    }


def compute_metrics(rows: list[dict[str, Any]], mapping: dict[str, str]) -> tuple[dict[str, float | None], dict[str, Any]]:
    mql = 0
    sql = 0
    opp = 0
    mql_sql = 0
    sql_opp = 0

    won = 0
    lost = 0

    cycle_days: list[float] = []
    deal_sizes: list[float] = []

    signups = 0
    activated = 0
    ttfv_values: list[float] = []
    ttpv_values: list[float] = []

    pilots = 0
    produced = 0

    ai_sessions_total = 0.0
    ai_escalations_total = 0.0
    ai_audited_total = 0.0
    ai_hallucinations_total = 0.0

    for row in rows:
        has_mql = has_date(row, "mql_date", mapping)
        has_sql = has_date(row, "sql_date", mapping)
        has_opp = has_date(row, "opportunity_date", mapping)

        if has_mql:
            mql += 1
        if has_sql:
            sql += 1
        if has_opp:
            opp += 1

        if has_mql and has_sql:
            mql_sql += 1
        if has_sql and has_opp:
            sql_opp += 1

        status = normalize_status(get_value(row, "close_status", mapping))
        if status in WON_STATUSES:
            won += 1
        elif status in LOST_STATUSES:
            lost += 1

        deal_amount = parse_float(get_value(row, "deal_amount", mapping))
        if has_opp and deal_amount is not None and deal_amount > 0:
            deal_sizes.append(deal_amount)

        opp_date = parse_date(get_value(row, "opportunity_date", mapping))
        close_date = parse_date(get_value(row, "close_date", mapping))
        cycle = days_between(opp_date, close_date)
        if cycle is not None and status in WON_STATUSES.union(LOST_STATUSES):
            cycle_days.append(cycle)

        signup_date = parse_date(get_value(row, "signup_date", mapping))
        first_value_date = parse_date(get_value(row, "first_value_date", mapping))
        proven_value_date = parse_date(get_value(row, "proven_value_date", mapping))

        if signup_date is not None:
            signups += 1

        if signup_date is not None and first_value_date is not None:
            activated += 1
            ttfv = days_between(signup_date, first_value_date)
            if ttfv is not None:
                ttfv_values.append(ttfv)

        if signup_date is not None and proven_value_date is not None:
            ttpv = days_between(signup_date, proven_value_date)
            if ttpv is not None:
                ttpv_values.append(ttpv)

        pilot_date = parse_date(get_value(row, "pilot_start_date", mapping))
        production_date = parse_date(get_value(row, "production_date", mapping))

        if pilot_date is not None:
            pilots += 1
        if pilot_date is not None and production_date is not None:
            produced += 1

        ai_sessions_total += parse_float(get_value(row, "ai_sessions", mapping)) or 0.0
        ai_escalations_total += parse_float(get_value(row, "ai_escalations", mapping)) or 0.0
        ai_audited_total += parse_float(get_value(row, "ai_audited_responses", mapping)) or 0.0
        ai_hallucinations_total += parse_float(get_value(row, "ai_hallucinations", mapping)) or 0.0

    win_rate = safe_div(float(won), float(won + lost))
    avg_cycle = statistics.mean(cycle_days) if cycle_days else None
    avg_deal = statistics.mean(deal_sizes) if deal_sizes else None

    pipeline_velocity = None
    if avg_cycle is not None and avg_cycle > 0 and avg_deal is not None and win_rate is not None:
        pipeline_velocity = (float(opp) * win_rate * avg_deal) / avg_cycle

    activation_rate = safe_div(float(activated), float(signups))
    ttfv_days = median(ttfv_values)
    ttpv_days = median(ttpv_values)

    pilot_to_prod = safe_div(float(produced), float(pilots))

    escalation_rate = safe_div(ai_escalations_total, ai_sessions_total)
    hallucination_rate = safe_div(ai_hallucinations_total, ai_audited_total)
    grounded_rate = None if hallucination_rate is None else max(0.0, 1.0 - hallucination_rate)

    metrics: dict[str, float | None] = {
        "mql_to_sql_conversion": safe_div(float(mql_sql), float(mql)),
        "sql_to_opportunity_conversion": safe_div(float(sql_opp), float(sql)),
        "opportunity_win_rate": win_rate,
        "avg_sales_cycle_days": avg_cycle,
        "avg_deal_size": avg_deal,
        "pipeline_velocity": pipeline_velocity,
        "activation_rate": activation_rate,
        "ttfv_days": ttfv_days,
        "ttpv_days": ttpv_days,
        "pilot_to_production_conversion": pilot_to_prod,
        "escalation_rate": escalation_rate,
        "hallucination_rate": hallucination_rate,
        "grounded_response_rate": grounded_rate,
    }

    diagnostics = {
        "row_count": len(rows),
        "mql_accounts": mql,
        "sql_accounts": sql,
        "opportunity_accounts": opp,
        "won_opportunities": won,
        "lost_opportunities": lost,
        "pilot_accounts": pilots,
        "production_accounts": produced,
        "ai_sessions_total": ai_sessions_total,
        "ai_escalations_total": ai_escalations_total,
        "ai_audited_responses_total": ai_audited_total,
        "ai_hallucinations_total": ai_hallucinations_total,
    }

    return metrics, diagnostics


def render_markdown(
    input_csv: Path,
    generated_at: str,
    metrics: dict[str, float | None],
    targets: dict[str, float],
    diagnostics: dict[str, Any],
) -> str:
    defs = metric_definitions()

    lines = [
        "# Auto GTM Scorecard (CRM Export)",
        "",
        f"Generated: {generated_at}",
        f"Input: `{input_csv}`",
        "",
        "| Metric | Current | Target | Status | Definition |",
        "|---|---:|---:|---|---|",
    ]

    for key, meta in defs.items():
        current = metrics.get(key)
        target = targets.get(key)
        status = evaluate_status(key, current, target, meta["direction"])
        lines.append(
            "| {label} | {current} | {target} | {status} | {definition} |".format(
                label=meta["label"],
                current=format_metric(key, current),
                target=format_metric(key, target),
                status=status,
                definition=meta["definition"],
            )
        )

    lines.extend(
        [
            "",
            "## Diagnostics",
            f"- Rows processed: {diagnostics['row_count']}",
            f"- MQL accounts: {diagnostics['mql_accounts']}",
            f"- SQL accounts: {diagnostics['sql_accounts']}",
            f"- Opportunity accounts: {diagnostics['opportunity_accounts']}",
            f"- Closed won / lost: {diagnostics['won_opportunities']} / {diagnostics['lost_opportunities']}",
            f"- Pilot accounts: {diagnostics['pilot_accounts']}",
            f"- Production accounts: {diagnostics['production_accounts']}",
            f"- AI sessions / escalations: {diagnostics['ai_sessions_total']:.0f} / {diagnostics['ai_escalations_total']:.0f}",
            f"- Audited responses / hallucinations: {diagnostics['ai_audited_responses_total']:.0f} / {diagnostics['ai_hallucinations_total']:.0f}",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build GTM scorecard from CRM/export CSV")
    parser.add_argument("--csv", required=True, help="Input CRM/export CSV path")
    parser.add_argument("--out-md", required=True, help="Output markdown path")
    parser.add_argument("--out-json", help="Optional output JSON path")
    parser.add_argument("--mapping", help="Optional YAML/JSON file mapping canonical field names to CSV columns")
    parser.add_argument("--targets", help="Optional YAML/JSON file with metric targets")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_csv = Path(args.csv).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()

    if not input_csv.exists():
        raise ScorecardError(f"CSV not found: {input_csv}")

    mapping_path = Path(args.mapping).expanduser().resolve() if args.mapping else None
    targets_path = Path(args.targets).expanduser().resolve() if args.targets else None

    mapping = load_mapping(mapping_path)
    targets = load_targets(targets_path)

    with input_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for r in reader]

    if not rows:
        raise ScorecardError("CSV has no data rows")

    metrics, diagnostics = compute_metrics(rows, mapping)
    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(
        render_markdown(
            input_csv=input_csv,
            generated_at=generated_at,
            metrics=metrics,
            targets=targets,
            diagnostics=diagnostics,
        ),
        encoding="utf-8",
    )

    if args.out_json:
        out_json = Path(args.out_json).expanduser().resolve()
        out_json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": generated_at,
            "input_csv": str(input_csv),
            "metrics": metrics,
            "targets": targets,
            "diagnostics": diagnostics,
        }
        out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Scorecard written: {out_md}")
    if args.out_json:
        print(f"Metrics JSON written: {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
