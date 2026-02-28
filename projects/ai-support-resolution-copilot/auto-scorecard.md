# Auto GTM Scorecard (CRM Export)

Generated: 2026-02-28 01:42 UTC
Input: `/Users/computer/Documents/GitHub/MarketEngineering/skills/ai-gtm-principal-engineer/assets/templates/crm-export.template.csv`

| Metric | Current | Target | Status | Definition |
|---|---:|---:|---|---|
| MQL -> SQL conversion | 100.0% | 82.0% | on-track | SQL accounts / MQL accounts |
| SQL -> Opportunity conversion | 100.0% | 75.0% | on-track | Opportunity accounts / SQL accounts |
| Opportunity win rate | 62.5% | 45.0% | on-track | Won opportunities / closed opportunities |
| Average sales cycle days | 21.8 | 26.0 | on-track | Average days from opportunity_date to close_date |
| Average deal size | $51,100.00 | n/a | no-target | Average deal amount for opportunity rows |
| Pipeline velocity | $14,683.91 | n/a | no-target | (Qualified opportunities * win rate * avg deal size) / avg sales cycle days |
| Activation rate | 100.0% | 88.0% | on-track | Accounts with first_value_date / accounts with signup_date |
| TTFV (median days) | 7.0 | 10.0 | on-track | Median days from signup_date to first_value_date |
| TTPV (median days) | 20.0 | 22.0 | on-track | Median days from signup_date to proven_value_date |
| Pilot -> Production conversion | 50.0% | 60.0% | off-track | Accounts with production_date / accounts with pilot_start_date |
| Escalation rate | 4.3% | 4.0% | off-track | Total ai_escalations / total ai_sessions |
| Hallucination rate | 2.9% | 2.0% | off-track | Total ai_hallucinations / total ai_audited_responses |
| Grounded response rate | 97.1% | 98.0% | watch | 1 - hallucination_rate |

## Diagnostics
- Rows processed: 10
- MQL accounts: 10
- SQL accounts: 10
- Opportunity accounts: 10
- Closed won / lost: 5 / 3
- Pilot accounts: 10
- Production accounts: 5
- AI sessions / escalations: 7265 / 315
- Audited responses / hallucinations: 2925 / 85
