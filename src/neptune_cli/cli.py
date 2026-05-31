"""Command-line interface for read-only Neptune queries."""

from __future__ import annotations

from typing import Optional

import click

from neptune_cli import __version__, client, output

FORMAT_CHOICE = click.Choice(["table", "json", "csv"])

# Shared option decorators reused across commands.
match_option = click.option(
    "--match",
    "-m",
    "match",
    default=None,
    help="Regex matched against experiment (or run) names. Omit to match all.",
)
attributes_option = click.option(
    "--attributes",
    "-a",
    "attributes",
    multiple=True,
    help="Attribute path regex. Repeatable.",
)


def _resolve(ctx) -> tuple[str, str]:
    """Resolve project + token from the group context, return (project, fmt)."""
    opts = ctx.obj
    project = client.resolve_project(opts["project"], opts["api_token"])
    return project, opts["format"]


def _attrs(attributes) -> list:
    return list(attributes)


def _experiments_filter(match: Optional[str], *, required: bool) -> Optional[str]:
    """Experiments/runs filter; substitute match-all when a filter is mandatory."""
    if match:
        return match
    return r".*" if required else None


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--project",
    default=None,
    envvar="NEPTUNE_PROJECT",
    help="Neptune project (workspace-name/project-name). Defaults to $NEPTUNE_PROJECT.",
)
@click.option(
    "--api-token",
    default=None,
    envvar="NEPTUNE_API_TOKEN",
    help="Neptune API token. Defaults to $NEPTUNE_API_TOKEN (preferred).",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    type=FORMAT_CHOICE,
    default="table",
    show_default=True,
    help="Output format.",
)
@click.version_option(__version__, "-V", "--version", prog_name="neptune-cli")
@click.pass_context
def cli(ctx, project, api_token, fmt):
    """Query the Neptune experiment-tracking platform (read-only)."""
    ctx.obj = {"project": project, "api_token": api_token, "format": fmt}


# --------------------------------------------------------------------------- #
# Experiment-oriented commands
# --------------------------------------------------------------------------- #
@cli.command("list-experiments")
@match_option
@click.option("--limit", type=int, default=None, help="Keep at most this many names.")
@click.pass_context
def list_experiments(ctx, match, limit):
    """List experiment names."""
    project, fmt = _resolve(ctx)
    names = client.nq.list_experiments(project=project, experiments=match)
    if limit is not None:
        names = names[:limit]
    output.render(names, fmt)


@cli.command("list-attributes")
@match_option
@attributes_option
@click.pass_context
def list_attributes(ctx, match, attributes):
    """List attribute paths available on matching experiments."""
    project, fmt = _resolve(ctx)
    names = client.nq.list_attributes(
        project=project, experiments=match, attributes=_attrs(attributes) or None
    )
    output.render(names, fmt)


@cli.command("experiments")
@match_option
@attributes_option
@click.option("--sort-by", default=None, help="Attribute to sort by.")
@click.option(
    "--sort-direction",
    type=click.Choice(["asc", "desc"]),
    default="desc",
    show_default=True,
)
@click.option("--limit", type=int, default=None, help="Max rows.")
@click.pass_context
def experiments(ctx, match, attributes, sort_by, sort_direction, limit):
    """Fetch an experiments table (runs as rows, attributes as columns)."""
    project, fmt = _resolve(ctx)
    kwargs = dict(
        project=project,
        experiments=match,
        attributes=_attrs(attributes),
        sort_direction=sort_direction,
        limit=limit,
    )
    if sort_by:
        kwargs["sort_by"] = sort_by
    df = client.nq.fetch_experiments_table(**kwargs)
    output.render(df, fmt)


@cli.command("metrics")
@match_option
@attributes_option
@click.option("--tail", type=int, default=None, help="Keep only the last N steps.")
@click.pass_context
def metrics(ctx, match, attributes, tail):
    """Fetch metric series for matching experiments (steps as rows)."""
    project, fmt = _resolve(ctx)
    attrs = _require_attributes(attributes)
    df = client.nq.fetch_metrics(
        project=project,
        experiments=_experiments_filter(match, required=True),
        attributes=attrs,
        tail_limit=tail,
    )
    output.render(df, fmt)


@cli.command("series")
@match_option
@attributes_option
@click.option("--tail", type=int, default=None, help="Keep only the last N steps.")
@click.pass_context
def series(ctx, match, attributes, tail):
    """Fetch string / histogram series for matching experiments."""
    project, fmt = _resolve(ctx)
    attrs = _require_attributes(attributes)
    df = client.nq.fetch_series(
        project=project,
        experiments=_experiments_filter(match, required=True),
        attributes=attrs,
        tail_limit=tail,
    )
    output.render(df, fmt)


@cli.command("download")
@match_option
@attributes_option
@click.option(
    "--dest",
    type=click.Path(file_okay=False),
    default=None,
    help="Destination directory (defaults to the current directory).",
)
@click.pass_context
def download(ctx, match, attributes, dest):
    """Download files logged to matching experiments.

    Fetches an experiments table for the given file attributes, then downloads
    the referenced files.
    """
    project, fmt = _resolve(ctx)
    table = client.nq.fetch_experiments_table(
        project=project, experiments=match, attributes=_require_attributes(attributes)
    )
    result = client.nq.download_files(files=table, destination=dest)
    output.render(result, fmt)


# --------------------------------------------------------------------------- #
# Run-oriented commands (target individual runs by ID)
# --------------------------------------------------------------------------- #
@cli.group("runs")
def runs_group():
    """Query individual runs by ID (instead of experiments by name)."""


runs_option = click.option(
    "--runs",
    "-r",
    "runs",
    default=None,
    help="Regex matched against run IDs. Omit to match all.",
)


@runs_group.command("list")
@runs_option
@click.option("--limit", type=int, default=None, help="Keep at most this many IDs.")
@click.pass_context
def runs_list(ctx, runs, limit):
    """List run IDs."""
    project, fmt = _resolve(ctx)
    ids = client.nq_runs.list_runs(project=project, runs=runs)
    if limit is not None:
        ids = ids[:limit]
    output.render(ids, fmt)


@runs_group.command("table")
@runs_option
@attributes_option
@click.option("--limit", type=int, default=None, help="Max rows.")
@click.pass_context
def runs_table(ctx, runs, attributes, limit):
    """Fetch a runs table (runs as rows, attributes as columns)."""
    project, fmt = _resolve(ctx)
    df = client.nq_runs.fetch_runs_table(
        project=project, runs=runs, attributes=_attrs(attributes), limit=limit
    )
    output.render(df, fmt)


@runs_group.command("metrics")
@runs_option
@attributes_option
@click.option("--tail", type=int, default=None, help="Keep only the last N steps.")
@click.pass_context
def runs_metrics(ctx, runs, attributes, tail):
    """Fetch metric series for matching runs (steps as rows)."""
    project, fmt = _resolve(ctx)
    df = client.nq_runs.fetch_metrics(
        project=project,
        runs=_experiments_filter(runs, required=True),
        attributes=_require_attributes(attributes),
        tail_limit=tail,
    )
    output.render(df, fmt)


def _require_attributes(attributes) -> list:
    attrs = _attrs(attributes)
    if not attrs:
        raise click.UsageError(
            "At least one --attributes/-a is required for this command."
        )
    return attrs


if __name__ == "__main__":
    cli()
