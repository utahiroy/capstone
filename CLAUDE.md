# Capstone Project Instructions

## Project mission

This repository is for a reproducible U.S. state-level research project on life-stage migration patterns.

The goal is to analyze how interstate migration differs by age group across the 50 U.S. states in 2024, and which state-level characteristics are statistically associated with those differences.

This is a research and analysis repository, not a generic software project. Prioritize methodological consistency, reproducibility, and traceable data provenance over speed.

---

## Before doing substantial work in any new session

1. Read `docs/research-brief.md` before making methodological or implementation decisions.
2. Restate the current objective in 5-10 bullet points.
3. Identify any missing assumptions or ambiguities before proceeding.
4. Propose a concrete execution plan before large code changes or data downloads.
5. Do not silently change research definitions, DV formulas, geographic scope, or year.

---

## Non-negotiable research constraints

- Geography: 50 U.S. states only.
- Exclude DC, Puerto Rico, and other non-state geographies.
- Time scope: 2024 cross-section only.
- Primary dependent variables: age-group-specific interstate net migration rates per 1,000 population.
- Supplemental dependent variables: `IN_RATE`, `OUT_RATE`, `NET_COUNT`.
- Age groups are fixed as:
  - 18-24
  - 25-34
  - 35-54
  - 55-64
  - 65+
- Main modeling strategy:
  1. descriptive statistics
  2. Spearman rank correlation
  3. single-variable OLS
  4. multiple OLS
  5. mapping and residual visualization
- Models must be estimated separately by age group.
- Do not replace the main design with pooled interaction models unless explicitly asked.

---

## Data and pipeline rules

- Build a reproducible pipeline.
- Prefer scripts and modular Python code over manual one-off notebook steps.
- Never overwrite raw downloaded data.
- Keep raw, interim, processed, and output artifacts separated.
- Every dataset must have a clear source, retrieval method, and transformation logic.
- Preserve variable names and IDs consistently across the pipeline.
- When a transformation is nontrivial, document it in code comments and in a project note.
- If a source fails or changes format, stop and report the issue clearly before inventing substitutes.

---

## Repository conventions

When scaffolding the repo, prefer this structure unless there is a strong reason to revise it:

- `docs/` for research specs, notes, and methodological memos
- `src/` for reusable Python modules
- `scripts/` for executable pipeline scripts
- `data_raw/` for unmodified source downloads
- `data_interim/` for cleaned but not final datasets
- `data_processed/` for final analysis-ready tables
- `outputs/tables/` for regression tables and summary tables
- `outputs/figures/` for charts and maps
- `outputs/logs/` for run logs and diagnostics

---

## Analytical standards

- Keep the methodology aligned with `docs/research-brief.md`.
- Separate facts from interpretation in written outputs.
- Always state formulas, units, and denominators clearly.
- For each derived variable, ensure the formula is explicit and reproducible.
- Prefer compact, interpretable models over unstable models with marginally better fit.
- Check coefficient signs against theory before treating a model as acceptable.
- Report limitations honestly.

---

## Model selection rules

Use these rules unless explicitly overridden:

- Variable screening: absolute Spearman rho
- Single-variable comparison: Adjusted R²
- Multiple regression comparison:
  - Adjusted R²
  - AIC / BIC
  - theoretical sign plausibility
  - no extreme multicollinearity
- Do not choose models by p-value alone.
- Do not treat correlation as causal proof.

---

## Output expectations

When asked to deliver progress or results:

1. Start with a concise summary of what was completed.
2. Then show what files were created or modified.
3. Then show remaining gaps, risks, and decisions needed.
4. Distinguish clearly between:
   - verified result
   - implementation assumption
   - interpretation or opinion

For tables and exports:
- Use machine-readable CSVs where appropriate.
- Use clear file names.
- Keep columns stable across reruns when possible.

---

## Escalate instead of guessing when

Stop and ask for confirmation if any of the following happens:

- a data source conflicts with the agreed research definition
- multiple valid ACS interpretations exist for the same DV
- a source no longer provides the needed 2024 state-level series
- a methodological shortcut would materially change the research design
- a variable must be replaced, dropped, or redefined

---

## Preferred working style

- Be direct, structured, and implementation-oriented.
- Show plans before major execution.
- Avoid unnecessary file proliferation.
- Make each commit-sized change logically coherent.
- Optimize for a final repository that another researcher can audit and rerun.
