"""Test cases for Task-1 functions 1-4 (one per function)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.task1 import (
    InputValidationError,
    build_chain_of_thought_prompt,
    build_few_shot_prompt,
    build_zero_shot_prompt,
    extract_pdf_text,
    validate_input_documents,
)


def _make_pdf(path: Path, text: str = "4.1 Ensure a user for the container has been created") -> Path:
    """Write a minimal one-page PDF containing `text` (no extra dependencies)."""
    content = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    path.write_bytes(bytes(out))
    return path


# Function 1: input validation
def test_validate_input_documents(tmp_path):
    good1 = _make_pdf(tmp_path / "docker-cis-v0.pdf")
    good2 = _make_pdf(tmp_path / "docker-cis-v1.pdf")

    p1, p2 = validate_input_documents(good1, good2)
    assert p1.name == "docker-cis-v0.pdf" and p2.name == "docker-cis-v1.pdf"

    # Bad inputs are rejected
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("this is not a pdf")
    wrong_ext = tmp_path / "notes.txt"
    wrong_ext.write_text("hello")
    for bad in (tmp_path / "missing.pdf", fake_pdf, wrong_ext, tmp_path, "", None, 42):
        with pytest.raises(InputValidationError):
            validate_input_documents(good1, bad)


# Function 2: zero-shot
def test_build_zero_shot_prompt():
    prompt = build_zero_shot_prompt("DOC ONE TEXT", "DOC TWO TEXT", "v0.pdf", "v1.pdf")
    assert isinstance(prompt, str)
    assert "DOC ONE TEXT" in prompt and "DOC TWO TEXT" in prompt
    assert "v0.pdf" in prompt and "element1" in prompt and "requirements" in prompt
    assert "### EXAMPLE" not in prompt  # zero-shot has no examples
    with pytest.raises(ValueError):
        build_zero_shot_prompt("", "x")


# Function 3: few-shot
def test_build_few_shot_prompt():
    prompt = build_few_shot_prompt("DOC ONE TEXT", "DOC TWO TEXT")
    assert isinstance(prompt, str)
    assert "DOC ONE TEXT" in prompt and "DOC TWO TEXT" in prompt
    assert prompt.count("### EXAMPLE") >= 2
    assert "element1" in prompt


# Function 4: chain of thought
def test_build_chain_of_thought_prompt():
    prompt = build_chain_of_thought_prompt("DOC ONE TEXT", "DOC TWO TEXT")
    assert isinstance(prompt, str)
    assert "DOC ONE TEXT" in prompt and "DOC TWO TEXT" in prompt
    assert "Step 1" in prompt and "FINAL YAML" in prompt


# Bonus: PDF text extraction (not one of the four required tests)
def test_extract_pdf_text(tmp_path):
    pdf = _make_pdf(tmp_path / "x.pdf", "Ensure HEALTHCHECK instructions have been added")
    assert "HEALTHCHECK" in extract_pdf_text(pdf)


# Bonus: summary-table parsing (wrapped titles, checkbox glyphs, TOC line, noise)
def test_parse_summary_table():
    from src.task1 import format_recommendations, parse_summary_table

    sample = (
        "Appendix: Summary Table.......................... 254\n"  # table-of-contents line
        "Appendix: Summary Table\n"
        "Internal Only - General\n"
        "CIS Benchmark Recommendation Set\nCorrectly\nYes No\n"
        "4 Container Images and Build File Configuration\n"
        "4.1 Ensure that a user for the container has been created (Manual)  \n"
        "4.6 Ensure that HEALTHCHECK instructions have been\n"
        "added to container images (Manual)\n"
        "o o\n"
        "Page 5\n"
        "5 Container Runtime Configuration\n"
        "5.5 Ensure that privileged containers are not used (Automated) o o\n"
        "Appendix: Change History\n"
        "9.9 Ensure this is ignored (Manual)\n"
    )
    sections = parse_summary_table(sample)
    assert list(sections) == ["4", "5"]
    assert sections["4"]["title"] == "Container Images and Build File Configuration"
    ids = [r["id"] for r in sections["4"]["recommendations"]]
    assert ids == ["4.1", "4.6"]
    assert sections["4"]["recommendations"][1]["title"] == (
        "Ensure that HEALTHCHECK instructions have been added to container images"
    )
    assert sections["5"]["recommendations"][0]["status"] == "Automated"
    assert "## 5 Container Runtime Configuration" in format_recommendations(sections, only=["5"])
    assert parse_summary_table("no summary table here") == {}

