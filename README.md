# MarketEngineering

Principal/staff-level GTM engineering toolkit for AI projects.

## What is included

- Skill: `skills/ai-gtm-principal-engineer/`
- Research notes with citations: `skills/ai-gtm-principal-engineer/references/research-2026.md`
- Operating model and KPI taxonomy references
- Templates for GTM specs, experiment briefs, and monthly readouts
- Scripts to generate GTM plans, prioritize experiments, and auto-build scorecards from CRM exports
- Product-specific 90-day execution pack: `projects/ai-support-resolution-copilot/`

## Quick start

1. Copy `skills/ai-gtm-principal-engineer/assets/templates/gtm-spec.template.yaml` and fill it for your project.
2. Generate baseline artifacts:

```bash
python3 skills/ai-gtm-principal-engineer/scripts/generate_gtm_plan.py \
  --spec <your-spec.yaml> \
  --out output/<project-name>
```

3. Rank the experiment portfolio:

```bash
python3 skills/ai-gtm-principal-engineer/scripts/prioritize_experiments.py \
  --in <your-spec.yaml> \
  --out output/<project-name>/prioritized-experiments.csv \
  --summary output/<project-name>/prioritized-experiments.md
```

4. Build scorecard from CRM export CSV:

```bash
python3 skills/ai-gtm-principal-engineer/scripts/build_scorecard_from_crm.py \
  --csv <crm-export.csv> \
  --out-md output/<project-name>/auto-scorecard.md \
  --out-json output/<project-name>/auto-scorecard.json \
  --mapping skills/ai-gtm-principal-engineer/assets/templates/crm-column-mapping.template.yaml \
  --targets skills/ai-gtm-principal-engineer/assets/templates/scorecard-targets.template.yaml
```

5. Reference implementation (already generated):
- `projects/ai-support-resolution-copilot/90-day-execution-pack.md`

## Validation

Run the skill validator:

```bash
python3 /Users/computer/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/ai-gtm-principal-engineer
```
