
from pathlib import Path


def read_comparison_files(element_file, requirement_file):
    """
    Task 3 - Function 1

    Read the two TEXT files produced by Task 2.

    Args:
        element_file: Path to the element-name differences file.
        requirement_file: Path to the requirement differences file.

    Returns:
        A tuple containing the contents of both files.

    Raises:
        FileNotFoundError: If an input file does not exist.
        ValueError: If an input file is empty.
    """

    element_path = Path(element_file)
    requirement_path = Path(requirement_file)

    if not element_path.is_file():
        raise FileNotFoundError(
            f"Element differences file not found: {element_path}"
        )

    if not requirement_path.is_file():
        raise FileNotFoundError(
            f"Requirement differences file not found: {requirement_path}"
        )

    element_text = element_path.read_text(encoding="utf-8").strip()
    requirement_text = requirement_path.read_text(encoding="utf-8").strip()

    if not element_text:
        raise ValueError("Element differences file is empty.")

    if not requirement_text:
        raise ValueError("Requirement differences file is empty.")

    return element_text, requirement_text


import re


# Only map CIS requirements to Hadolint rules when
# there is a clear Dockerfile-level relationship.
CIS_HADOLINT_MAPPINGS = {
    "non-root user": "DL3002",
    "non root user": "DL3002",
    "root user": "DL3002",
    "use a user": "DL3002",
    "user for the container": "DL3002",
    "healthcheck": "DL3057",
    "health check": "DL3057",
}


def map_hadolint_rules(element_text, requirement_text, output_file):
    """
    Task 3 - Function 2

    Identify relevant Hadolint rules from CIS Docker differences
    and write the result to a text file.

    Returns:
        A list of mapped rule IDs.
    """

    combined_text = f"{element_text}\n{requirement_text}"
    normalized_text = combined_text.lower()

    no_difference_messages = {
        "no differences found",
        "no differences in regards to element names",
        "no differences in regards to requirements",
        "no differences in regard to element names",
        "no differences in regard to requirements",
    }

    def has_real_difference(text):
        cleaned = text.strip().lower()

        if not cleaned:
            return False

        return cleaned not in no_difference_messages

    differences_exist = (
        has_real_difference(element_text)
        or has_real_difference(requirement_text)
    )

    if not differences_exist:
        result = "NO DIFFERENCES FOUND"
        mapped_rules = []

    else:
        mapped_rules = set()

        for phrase, rule_id in CIS_HADOLINT_MAPPINGS.items():
            if phrase in normalized_text:
                mapped_rules.add(rule_id)

        mapped_rules = sorted(mapped_rules)

        if mapped_rules:
            result = "\n".join(mapped_rules)
        else:
            result = "NO MAPPING FOUND"

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result + "\n", encoding="utf-8")

    return mapped_rules



import json
import subprocess
import pandas as pd


REPORT_COLUMNS = [
    "FilePath",
    "DefaultSeverity",
    "RULEID",
    "COUNT",
]


def execute_hadolint(dockerfile_paths, mapped_rules=None):
    """
    Task 3 - Function 3

    Run Hadolint against Dockerfiles and return a pandas
    DataFrame summarizing the findings.

    Args:
        dockerfile_paths: List of Dockerfile paths.
        mapped_rules: List of rule IDs to include.
            None or an empty list means include all rules.

    Returns:
        DataFrame with FilePath, DefaultSeverity, RULEID, COUNT.
    """

    findings = []

    for dockerfile in dockerfile_paths:
        dockerfile = Path(dockerfile)

        if not dockerfile.is_file():
            raise FileNotFoundError(
                f"Dockerfile not found: {dockerfile}"
            )

        result = subprocess.run(
            ["hadolint", "--format", "json", str(dockerfile)],
            capture_output=True,
            text=True,
            check=False,
        )

        # Hadolint may return 1 when lint violations are found.
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"Hadolint failed for {dockerfile}: {result.stderr}"
            )

        try:
            violations = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Invalid Hadolint JSON output for {dockerfile}"
            ) from exc

        for violation in violations:
            rule_id = violation["code"]

            if mapped_rules and rule_id not in mapped_rules:
                continue

            findings.append({
                "FilePath": str(dockerfile),
                "DefaultSeverity": violation["level"],
                "RULEID": rule_id,
            })

    if not findings:
        return pd.DataFrame(columns=REPORT_COLUMNS)

    df = pd.DataFrame(findings)

    df = (
        df.groupby(
            ["FilePath", "DefaultSeverity", "RULEID"],
            as_index=False
        )
        .size()
        .rename(columns={"size": "COUNT"})
    )

    return df[REPORT_COLUMNS]



def export_hadolint_csv(df, output_file):
    """
    Task 3 - Function 4

    Export Hadolint findings to a CSV file.

    Args:
        df: Pandas DataFrame containing Hadolint findings.
        output_file: Destination CSV file path.

    Returns:
        Path to the generated CSV file.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    missing_columns = [
        column for column in REPORT_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df[REPORT_COLUMNS].to_csv(
        output_path,
        index=False
    )

    return output_path
