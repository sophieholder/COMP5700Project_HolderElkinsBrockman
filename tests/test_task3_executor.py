
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source.task3_executor import read_comparison_files


def test_read_comparison_files(tmp_path):
    """Verify that both comparison files are read correctly."""

    element_file = tmp_path / "element_differences.txt"
    requirement_file = tmp_path / "requirement_differences.txt"

    element_file.write_text(
        "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES",
        encoding="utf-8"
    )

    requirement_file.write_text(
        "Container User,Ensure that a user for the container has been created",
        encoding="utf-8"
    )

    elements, requirements = read_comparison_files(
        element_file, requirement_file
    )

    assert elements == "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"

    assert requirements == (
        "Container User,Ensure that a user for the container has been created"
    )


from source.task3_executor import map_hadolint_rules


def test_no_differences(tmp_path):
    output_file = tmp_path / "mapped_rules.txt"

    rules = map_hadolint_rules(
        "NO DIFFERENCES FOUND",
        "NO DIFFERENCES FOUND",
        output_file
    )

    assert rules == []
    assert output_file.read_text().strip() == "NO DIFFERENCES FOUND"


def test_valid_hadolint_mapping(tmp_path):
    output_file = tmp_path / "mapped_rules.txt"

    rules = map_hadolint_rules(
        "Container User",
        "Ensure that a non-root user is used for the container",
        output_file
    )

    assert rules == ["DL3002"]
    assert output_file.read_text().strip() == "DL3002"


def test_no_hadolint_mapping(tmp_path):
    output_file = tmp_path / "mapped_rules.txt"

    rules = map_hadolint_rules(
        "Docker daemon configuration",
        "Ensure Docker daemon logging is configured",
        output_file
    )

    assert rules == []
    assert output_file.read_text().strip() == "NO MAPPING FOUND"


import shutil
import pytest

from source.task3_executor import execute_hadolint


@pytest.mark.skipif(
    shutil.which("hadolint") is None,
    reason="Hadolint is not installed"
)
def test_execute_hadolint(tmp_path):
    dockerfile = tmp_path / "Dockerfile"

    dockerfile.write_text(
        "FROM ubuntu:22.04\n"
        "RUN apt-get update\n",
        encoding="utf-8"
    )

    df = execute_hadolint([dockerfile])

    assert list(df.columns) == [
        "FilePath",
        "DefaultSeverity",
        "RULEID",
        "COUNT",
    ]

    assert "DL3009" in df["RULEID"].values
    assert df["COUNT"].sum() >= 1


import pandas as pd

from source.task3_executor import export_hadolint_csv


def test_export_hadolint_csv(tmp_path):
    """Verify the Hadolint DataFrame is exported correctly."""

    df = pd.DataFrame([
        {
            "FilePath": "Dockerfile",
            "DefaultSeverity": "warning",
            "RULEID": "DL3009",
            "COUNT": 1,
        }
    ])

    output_file = tmp_path / "reports" / "hadolint_results.csv"

    result = export_hadolint_csv(df, output_file)

    assert result.exists()

    loaded_df = pd.read_csv(result)

    assert list(loaded_df.columns) == [
        "FilePath",
        "DefaultSeverity",
        "RULEID",
        "COUNT",
    ]

    assert loaded_df.loc[0, "RULEID"] == "DL3009"
    assert loaded_df.loc[0, "COUNT"] == 1
