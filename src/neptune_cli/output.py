"""Render query results as a rich table, JSON, or CSV."""

from __future__ import annotations

import json
from typing import Sequence, Union

import click
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()

Result = Union[pd.DataFrame, Sequence[str]]


def render(data: Result, fmt: str) -> None:
    """Print ``data`` (a DataFrame or a flat list) in the requested format."""
    if isinstance(data, pd.DataFrame):
        _render_df(data, fmt)
    else:
        _render_list(list(data), fmt)


def _render_list(items: list, fmt: str) -> None:
    if not items:
        console.print("[dim]No matching results.[/dim]")
        return
    if fmt == "json":
        click.echo(json.dumps(items, indent=2))
    else:  # table and csv are both just one item per line
        for item in items:
            click.echo(item)


def _render_df(df: pd.DataFrame, fmt: str) -> None:
    if df.empty:
        console.print("[dim]No matching results.[/dim]")
        return
    if fmt == "json":
        flat = _flatten_columns(df).reset_index()
        click.echo(flat.to_json(orient="records", indent=2, date_format="iso"))
    elif fmt == "csv":
        click.echo(_flatten_columns(df).to_csv())
    else:
        _print_rich_table(_flatten_columns(df))


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Join MultiIndex column tuples into ``a/b`` strings for serialization."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [_label(c) for c in df.columns]
    return df


def _label(col) -> str:
    if isinstance(col, tuple):
        return "/".join(str(part) for part in col if part not in (None, ""))
    return str(col)


def _print_rich_table(df: pd.DataFrame) -> None:
    df = df.reset_index()
    table = Table(show_lines=False)
    for col in df.columns:
        table.add_column(_label(col), overflow="fold")
    for _, row in df.iterrows():
        table.add_row(*[_cell(v) for v in row.tolist()])
    console.print(table)


def _cell(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass  # arrays / non-scalars aren't NA-checkable
    return str(value)
