# AI GTM Metrics Taxonomy

## 1. Funnel metrics

- `MQL -> SQL conversion` = SQLs / MQLs
- `SQL -> Opportunity conversion` = Opportunities / SQLs
- `Opportunity win rate` = Closed won / Closed opportunities
- `Pipeline velocity` = (Qualified opportunities * win rate * average deal size) / sales cycle days

## 2. Product-qualified metrics

- `PQA rate` = accounts hitting PQA threshold / active accounts
- `Activation rate` = new accounts reaching first-value milestone / new accounts
- `Time-to-First-Value (TTFV)` = median days from signup to first successful outcome
- `Time-to-Proven-Value (TTPV)` = median days from signup to repeat measurable value outcome

## 3. AI quality metrics

- `Task success` = successful completions / total evaluated tasks
- `Grounded response rate` = responses with valid evidence / total responses requiring evidence
- `Hallucination rate` = unsupported claims / audited responses
- `Escalation rate` = human escalations / AI-served sessions

## 4. Commercial efficiency metrics

- `CAC payback` = customer acquisition cost / monthly gross profit per customer
- `Sales efficiency` = new ARR / sales and marketing spend
- `Expansion rate` = expansion ARR / starting ARR
- `Pilot-to-production conversion` = production deals / completed pilots

## 5. Reliability and support metrics

- `AI uptime` = available AI service minutes / total minutes
- `P95 latency` = 95th percentile end-to-end response time
- `Support contact rate` = support tickets / active accounts
- `Deflection accuracy` = correctly deflected support requests / total deflected requests

## 6. Decision thresholds

For each metric, store:
- Baseline value
- Target value
- Minimum detectable effect
- Decision deadline
- Owner

Use thresholds to prevent interpretation drift in experiment reviews.
