"""Credential resolution and thin pass-throughs to the neptune_query API.

Commands in :mod:`neptune_cli.cli` call the Neptune read API through the ``nq``
and ``nq_runs`` references exposed here. Keeping the imports in one module means
tests can monkeypatch ``neptune_cli.client.nq`` with a fake and exercise the CLI
fully offline.
"""

from __future__ import annotations

import os
from typing import Optional

import click
import neptune_query as nq
import neptune_query.runs as nq_runs

__all__ = ["nq", "nq_runs", "resolve_project"]


def resolve_project(
    project: Optional[str] = None, api_token: Optional[str] = None
) -> str:
    """Resolve the target project and API token, falling back to env vars.

    The token is pushed into ``NEPTUNE_API_TOKEN`` so both the experiments and
    runs query modules pick it up. Missing values raise a friendly
    :class:`click.UsageError` rather than a deep traceback.
    """
    project = project or os.environ.get("NEPTUNE_PROJECT")
    token = api_token or os.environ.get("NEPTUNE_API_TOKEN")

    if not project:
        raise click.UsageError(
            "No Neptune project specified. Pass --project or set NEPTUNE_PROJECT "
            "(format: workspace-name/project-name)."
        )
    if not token:
        raise click.UsageError(
            "No Neptune API token found. Pass --api-token or set NEPTUNE_API_TOKEN."
        )

    os.environ["NEPTUNE_API_TOKEN"] = token
    return project
