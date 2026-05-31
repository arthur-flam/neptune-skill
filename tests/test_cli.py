"""Offline tests for neptune-cli.

``neptune_query`` is replaced with a fake recording module so the CLI is
exercised end-to-end without credentials or network access.
"""

import json

import pandas as pd
import pytest
from click.testing import CliRunner

from neptune_cli import client
from neptune_cli.cli import cli


class FakeNq:
    """Records calls and returns canned values."""

    def __init__(self):
        self.calls = []

    def list_experiments(self, **kwargs):
        self.calls.append(("list_experiments", kwargs))
        return ["exp_a", "exp_b", "exp_c"]

    def list_attributes(self, **kwargs):
        self.calls.append(("list_attributes", kwargs))
        return ["metrics/loss", "learning_rate"]

    def fetch_experiments_table(self, **kwargs):
        self.calls.append(("fetch_experiments_table", kwargs))
        return pd.DataFrame(
            {"metrics/loss": [0.1, 0.2]}, index=["exp_a", "exp_b"]
        )

    def fetch_metrics(self, **kwargs):
        self.calls.append(("fetch_metrics", kwargs))
        return pd.DataFrame({"loss": [0.5, 0.3]}, index=[0, 1])

    def fetch_series(self, **kwargs):
        self.calls.append(("fetch_series", kwargs))
        return pd.DataFrame({"msg": ["a", "b"]}, index=[0, 1])

    def download_files(self, **kwargs):
        self.calls.append(("download_files", kwargs))
        return pd.DataFrame({"path": ["./x.txt"]})

    # runs submodule mirror
    def list_runs(self, **kwargs):
        self.calls.append(("list_runs", kwargs))
        return ["RUN-1", "RUN-2"]

    def fetch_runs_table(self, **kwargs):
        self.calls.append(("fetch_runs_table", kwargs))
        return pd.DataFrame({"sys/id": ["RUN-1"]}, index=["RUN-1"])


@pytest.fixture
def fake(monkeypatch):
    nq = FakeNq()
    monkeypatch.setattr(client, "nq", nq)
    monkeypatch.setattr(client, "nq_runs", nq)
    monkeypatch.setenv("NEPTUNE_PROJECT", "ws/proj")
    monkeypatch.setenv("NEPTUNE_API_TOKEN", "tok")
    return nq


@pytest.fixture
def run():
    return CliRunner()


def test_help(run):
    result = run.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Query the Neptune" in result.output


def test_version(run):
    result = run.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "neptune-cli" in result.output


def test_missing_project(run, monkeypatch):
    monkeypatch.delenv("NEPTUNE_PROJECT", raising=False)
    monkeypatch.delenv("NEPTUNE_API_TOKEN", raising=False)
    result = run.invoke(cli, ["list-experiments"])
    assert result.exit_code != 0
    assert "No Neptune project" in result.output


def test_missing_token(run, monkeypatch):
    monkeypatch.setenv("NEPTUNE_PROJECT", "ws/proj")
    monkeypatch.delenv("NEPTUNE_API_TOKEN", raising=False)
    result = run.invoke(cli, ["list-experiments"])
    assert result.exit_code != 0
    assert "API token" in result.output


def test_list_experiments(run, fake):
    result = run.invoke(cli, ["list-experiments", "--match", "^exp_"])
    assert result.exit_code == 0
    assert "exp_a" in result.output
    name, kwargs = fake.calls[-1]
    assert name == "list_experiments"
    assert kwargs == {"project": "ws/proj", "experiments": "^exp_"}


def test_list_experiments_limit(run, fake):
    result = run.invoke(cli, ["list-experiments", "--limit", "1"])
    assert result.exit_code == 0
    assert result.output.strip() == "exp_a"


def test_experiments_table_table_format(run, fake):
    result = run.invoke(cli, ["experiments", "-a", "metrics/loss"])
    assert result.exit_code == 0
    assert "metrics/loss" in result.output


def test_experiments_table_json_format(run, fake):
    result = run.invoke(cli, ["-f", "json", "experiments", "-a", "metrics/loss"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["metrics/loss"] == 0.1


def test_experiments_table_csv_format(run, fake):
    result = run.invoke(cli, ["-f", "csv", "experiments"])
    assert result.exit_code == 0
    assert "metrics/loss" in result.output
    assert "0.1" in result.output


def test_metrics_requires_attributes(run, fake):
    result = run.invoke(cli, ["metrics"])
    assert result.exit_code != 0
    assert "--attributes" in result.output


def test_metrics_match_all_substitution(run, fake):
    result = run.invoke(cli, ["metrics", "-a", "loss"])
    assert result.exit_code == 0
    name, kwargs = fake.calls[-1]
    assert name == "fetch_metrics"
    assert kwargs["experiments"] == r".*"
    assert kwargs["attributes"] == ["loss"]


def test_download_composes_fetch_then_download(run, fake):
    result = run.invoke(cli, ["download", "-a", "data/sample", "--dest", "out"])
    assert result.exit_code == 0
    called = [c[0] for c in fake.calls]
    assert called == ["fetch_experiments_table", "download_files"]


def test_runs_metrics(run, fake):
    result = run.invoke(cli, ["runs", "metrics", "-r", "RUN-1", "-a", "loss"])
    assert result.exit_code == 0
    name, kwargs = fake.calls[-1]
    assert name == "fetch_metrics"
    assert kwargs["runs"] == "RUN-1"


def test_empty_result_notice(run, fake, monkeypatch):
    monkeypatch.setattr(fake, "list_experiments", lambda **k: [])
    result = run.invoke(cli, ["list-experiments"])
    assert result.exit_code == 0
    assert "No matching results" in result.output
