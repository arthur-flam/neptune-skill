---
name: neptune-tracking
description: >-
  Query the Neptune experiment-tracking platform from the command line. Use when
  the user wants to list or inspect Neptune experiments/runs, fetch metric series
  or experiment tables, list attributes, or download files from Neptune. This is
  read-only — it never creates runs or logs metrics. Requires NEPTUNE_API_TOKEN
  and NEPTUNE_PROJECT.
---

# Neptune tracking (read-only)

This skill bundles `neptune-cli`, a small uv-based CLI that wraps the official
[`neptune-query`](https://github.com/neptune-ai/neptune-query) package to read
metadata from the [Neptune](https://neptune.ai) experiment tracker.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) is installed.
- Two environment variables are set (ask the user if missing — never invent a token):
  - `NEPTUNE_PROJECT` — `workspace-name/project-name`
  - `NEPTUNE_API_TOKEN` — the user's Neptune API token

## How to run

Run the bundled CLI through uv, pointing `--project` at this skill's directory
(the directory containing this `SKILL.md`). The first run resolves dependencies
automatically; subsequent runs are fast.

```bash
uv run --project <SKILL_DIR> neptune-cli [GLOBAL OPTIONS] COMMAND [OPTIONS]
```

Prefer `--format json` when you need to parse the output yourself; use the
default `table` when showing results to the user.

## Commands

All commands accept the global options `--project`, `--api-token`, and
`-f/--format {table,json,csv}`. `--match/-m` is a regex over experiment (or run)
names; `--attributes/-a` is a repeatable regex over attribute paths.

| Goal | Command |
|---|---|
| List experiment names | `neptune-cli list-experiments [-m REGEX] [--limit N]` |
| List available attributes | `neptune-cli list-attributes [-m REGEX] [-a REGEX]` |
| Experiments table | `neptune-cli experiments [-m REGEX] [-a ATTR ...] [--sort-by ATTR] [--limit N]` |
| Metric series (steps) | `neptune-cli metrics -m REGEX -a ATTR [-a ...] [--tail N]` |
| String/histogram series | `neptune-cli series -m REGEX -a ATTR [-a ...] [--tail N]` |
| Download files | `neptune-cli download -m REGEX -a ATTR [--dest DIR]` |
| List run IDs | `neptune-cli runs list [-r REGEX] [--limit N]` |
| Runs table (by ID) | `neptune-cli runs table [-r REGEX] [-a ATTR ...]` |
| Run metric series (by ID) | `neptune-cli runs metrics -r REGEX -a ATTR [--tail N]` |

`metrics`, `series`, and `download` require at least one `-a/--attributes`.

## Examples

```bash
# What experiments exist, and what can I query?
uv run --project <SKILL_DIR> neptune-cli list-experiments -m '^exp_'
uv run --project <SKILL_DIR> neptune-cli list-attributes -m '^exp_' -a 'metrics/.*'

# Compare a few metrics across experiments, as JSON for further processing
uv run --project <SKILL_DIR> neptune-cli -f json experiments -m '^exp_' \
  -a 'metrics/train_accuracy' -a 'learning_rate'

# Last 20 steps of validation loss
uv run --project <SKILL_DIR> neptune-cli metrics -m exp_dczjz -a 'metrics/val_loss' --tail 20

# Drill into a specific run by ID
uv run --project <SKILL_DIR> neptune-cli runs metrics -r RUN-123 -a 'metrics/.*'
```

## Troubleshooting

- **"No Neptune project / API token"** — the env vars are unset. Ask the user
  to export `NEPTUNE_PROJECT` and `NEPTUNE_API_TOKEN`, or pass `--project` /
  `--api-token`.
- **Empty results** — the `--match`/`--attributes` regex matched nothing. These
  are regexes, not globs; e.g. use `^exp_` rather than `exp_*`.
- **Resolution/version errors** — this CLI pins `neptune-query<2.0.0` and needs
  Python 3.10+. Let uv manage the environment (`uv sync` inside `<SKILL_DIR>`).

See `README.md` in this directory for full CLI documentation.
