# neptune-cli

A small, **read-only** command-line interface for the
[Neptune](https://neptune.ai) experiment-tracking platform, built on top of the
official [`neptune-query`](https://github.com/neptune-ai/neptune-query) package.

It lets you list and inspect experiments/runs, fetch metric series and
experiment tables, list attributes, and download files — all from the terminal,
with output as a rich table, JSON, or CSV.

> This tool **only reads** from Neptune. It never creates runs or logs metrics.

## Requirements

- [uv](https://docs.astral.sh/uv/) (manages Python + dependencies)
- A Neptune account, with these environment variables set:
  - `NEPTUNE_API_TOKEN` — your API token (from your Neptune profile)
  - `NEPTUNE_PROJECT` — the target project, e.g. `workspace-name/project-name`

## Install / run

No global install needed — run it through uv from the repo:

```bash
uv sync                       # one-time: create the venv and resolve deps
uv run neptune-cli --help
```

You can also run it from anywhere by pointing uv at this project directory:

```bash
uv run --project /path/to/neptune-skill neptune-cli list-experiments
```

## Usage

```bash
# List experiment names (optionally filter by regex)
uv run neptune-cli list-experiments --match '^exp_'

# List the attributes available on matching experiments
uv run neptune-cli list-attributes -m '^exp_' --attributes 'metrics/.*'

# Fetch an experiments table (runs as rows, attributes as columns)
uv run neptune-cli experiments -m '^exp_' -a 'metrics/train_accuracy' -a 'learning_rate'

# Fetch metric series (steps as rows); --tail keeps the last N steps
uv run neptune-cli metrics -m exp_dczjz -a 'metrics/val_.+' --tail 10

# Fetch string / histogram series
uv run neptune-cli series -m '^exp_' -a 'messages/.*'

# Download files logged to matching experiments
uv run neptune-cli download -m '^exp_' -a 'data/sample' --dest ./downloads

# Target individual runs by ID instead of experiments
uv run neptune-cli runs metrics -r RUN-123 -a 'metrics/loss'
```

### Global options

| Option | Default | Meaning |
|---|---|---|
| `--project` | `$NEPTUNE_PROJECT` | `workspace/project` to query |
| `--api-token` | `$NEPTUNE_API_TOKEN` | API token (prefer the env var) |
| `-f, --format` | `table` | Output format: `table`, `json`, or `csv` |
| `--version` | | Print version and exit |

`--match/-m` accepts a regular expression matched against experiment (or run)
names. Omit it to match everything. `--attributes/-a` can be repeated, and each
value is treated as a regex matched against attribute paths.

## Development

```bash
uv run pytest          # offline unit tests (neptune_query is mocked)
```

## Notes

- This CLI pins `neptune-query<2.0.0`; the 1.x line is the current read API.
- It requires Python 3.10+ (a constraint inherited from `neptune-query`).
