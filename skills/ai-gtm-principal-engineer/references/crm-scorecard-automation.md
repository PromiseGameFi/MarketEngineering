# CRM Scorecard Automation

## Purpose

Convert CRM/export CSV snapshots into a standardized GTM scorecard used by this skill.

## Script

Run:

```bash
python3 scripts/build_scorecard_from_crm.py \
  --csv <crm-export.csv> \
  --out-md <scorecard.md> \
  --out-json <scorecard.json> \
  --mapping <crm-column-mapping.yaml> \
  --targets <scorecard-targets.yaml>
```

Only `--csv` and `--out-md` are required.

## Canonical CSV fields

- `account_id`
- `mql_date`
- `sql_date`
- `opportunity_date`
- `close_date`
- `close_status` (`won`, `lost`, `open`)
- `deal_amount`
- `signup_date`
- `first_value_date`
- `proven_value_date`
- `pilot_start_date`
- `production_date`
- `ai_sessions`
- `ai_escalations`
- `ai_audited_responses`
- `ai_hallucinations`

Use `assets/templates/crm-column-mapping.template.yaml` if your export uses different column names.

## Output metrics

- MQL -> SQL conversion
- SQL -> Opportunity conversion
- Opportunity win rate
- Average sales cycle days
- Average deal size
- Pipeline velocity
- Activation rate
- TTFV (median days)
- TTPV (median days)
- Pilot -> Production conversion
- Escalation rate
- Hallucination rate
- Grounded response rate

## Included templates

- `assets/templates/crm-export.template.csv`
- `assets/templates/crm-column-mapping.template.yaml`
- `assets/templates/scorecard-targets.template.yaml`
