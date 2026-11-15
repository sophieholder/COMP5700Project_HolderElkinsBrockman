"""Task-1 (Extractor), first half: input validation, PDF reading, and prompt builders.

Order of use:
  1. validate_input_documents()          Function 1  - validate the two PDFs
  2. extract_recommendation_summary()    helper      - PDF -> parsed recommendations
     format_recommendations()            helper      - parsed recommendations -> prompt text
  3. build_zero_shot_prompt()            Function 2
     build_few_shot_prompt()             Function 3
     build_chain_of_thought_prompt()     Function 4
(Functions 5 and 6 - the Gemma runner and the text-file dump - are added below by teammates.)
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


# ==========================================================================
# FUNCTION 1: INPUT VALIDATION
# ==========================================================================

class InputValidationError(ValueError):
    """Raised when an input document fails validation."""


def _validate_single_pdf(path_like) -> Path:
    """Validate one path. Returns a resolved Path or raises InputValidationError."""
    if path_like is None or not isinstance(path_like, (str, os.PathLike)):
        raise InputValidationError(
            f"Input must be a file path (str or PathLike), got {type(path_like).__name__}."
        )
    if isinstance(path_like, str) and not path_like.strip():
        raise InputValidationError("Input path is an empty string.")

    path = Path(path_like).expanduser()

    if not path.exists():
        raise InputValidationError(f"File does not exist: {path}")
    if not path.is_file():
        raise InputValidationError(f"Path is not a regular file: {path}")
    if path.suffix.lower() != ".pdf":
        raise InputValidationError(f"File does not have a .pdf extension: {path}")
    if path.stat().st_size == 0:
        raise InputValidationError(f"File is empty: {path}")
    if not os.access(path, os.R_OK):
        raise InputValidationError(f"File is not readable (permission denied): {path}")

    # Magic-number check: real PDFs start with %PDF-
    with open(path, "rb") as fh:
        if fh.read(5) != b"%PDF-":
            raise InputValidationError(f"File is not a valid PDF (bad header): {path}")

    # Parse check: make sure a PDF library can actually open it.
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise InputValidationError(f"PDF is encrypted/password protected: {path}")
        if len(reader.pages) == 0:
            raise InputValidationError(f"PDF has no pages: {path}")
    except InputValidationError:
        raise
    except (PdfReadError, OSError, ValueError, KeyError) as exc:
        raise InputValidationError(f"PDF could not be parsed ({exc}): {path}") from exc

    return path.resolve()


def validate_input_documents(doc1, doc2) -> tuple[Path, Path]:
    """Validate the two input requirement documents.

    Checks, for each document: valid type, non-empty path, exists, is a file,
    has a .pdf extension, is non-empty, is readable, starts with the %PDF- header,
    is parseable, is not encrypted, and has at least one page.

    Identical inputs are allowed (the TA runs e.g. v1 vs v1).

    Returns:
        (path1, path2) as resolved pathlib.Path objects.

    Raises:
        InputValidationError: on the first failing check.
    """
    return _validate_single_pdf(doc1), _validate_single_pdf(doc2)

# ==========================================================================
# HELPERS: PDF TEXT EXTRACTION AND CIS SUMMARY-TABLE PARSING
# ==========================================================================

def extract_pdf_text(pdf_path, max_chars: int | None = None) -> str:
    """Extract and clean the text of a PDF.

    Args:
        pdf_path: path to an (already validated) PDF.
        max_chars: optional cap on returned length. Gemma-3-1B has a limited
            context window, so callers can truncate or chunk the text.

    Returns:
        The cleaned text (page breaks collapsed, excess whitespace removed).
    """
    reader = PdfReader(str(Path(pdf_path)))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    raw = "\n".join(pages)

    # Re-join words hyphenated across line breaks, then normalise whitespace.
    raw = re.sub(r"(\w)-\n(\w)", r"\1\2", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    cleaned = raw.strip()

    if max_chars is not None and len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars]
    return cleaned


def chunk_text(text: str, chunk_size: int = 6000, overlap: int = 300) -> list[str]:
    """Split text into overlapping chunks, preferring to break on newlines.

    Useful because the full CIS Docker benchmark is far longer than what a 1B
    model can handle in one prompt.
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            nl = text.rfind("\n", start + chunk_size // 2, end)
            if nl != -1:
                end = nl
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


# --------------------------------------------------------------------------
# CIS Benchmark summary-table parsing
#
# Each CIS benchmark ends with "Appendix: Summary Table", a compact list of
# every recommendation ("4.1 Ensure that a user ... (Manual)") grouped under
# numbered section headings. It is ~45 KB versus ~330 KB for the whole PDF, and
# it is clean enough for a 1B model, so the prompts are fed from it.
# --------------------------------------------------------------------------

_ENTRY_START = re.compile(r"^(\d+(?:\.\d+){0,2})\s+(\S.*)$")
_STATUS_END = re.compile(r"(Automated|Manual)\s*$")
_NOISE = re.compile(
    r"^(Page \d+|Internal Only.*|CIS Docker Benchmark.*|CIS Benchmark\s+Recommendation Set.*"
    r"|Correctly|Yes\s+No|(?:[o○☐]\s*){2}|Appendix:.*|v\d+\.\d+\.\d+.*)$"
)
# Top-level section headings look like "4 Container Images ..." (1-2 digits +
# capital letter). 3-digit numbers such as "755 or more restrictive" are the
# wrapped tail of a recommendation title, not a heading.
_TOP_HEADING = re.compile(r"^\d{1,2}\s+[A-Z]")
# The "Set Correctly: Yes / No" checkbox glyphs are sometimes glued to the end
# of a title line ("... (Manual)  "), which hides the status.
_CHECKBOX_TAIL = re.compile(r"(?:\s*[○☐]){1,2}\s*$")


def _summary_table_lines(text: str) -> list[str]:
    """Return the lines of the real 'Appendix: Summary Table' section."""
    lines = []
    for ln in text.splitlines():
        ln = _CHECKBOX_TAIL.sub("", ln.rstrip("\r")).strip()
        # plain-ASCII variant: "... (Manual) o o"
        ln = re.sub(r"((?:Automated|Manual))\s+o\s+o$", r"\1", ln)
        lines.append(ln)
    # The heading also appears in the table of contents (followed by dots and
    # a page number); the real section heading stands alone on its line.
    starts = [i for i, ln in enumerate(lines) if ln == "Appendix: Summary Table"]
    if not starts:
        return []
    start = starts[-1] + 1
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("Appendix:") and "...." not in lines[j]:
            end = j
            break
    return lines[start:end]


def parse_summary_table(text: str) -> dict:
    """Parse the CIS 'Summary Table' appendix into a nested structure.

    Returns an ordered dict keyed by top-level section number:
        {"4": {"title": "Container Images and Build File Configuration",
               "recommendations": [{"id": "4.1", "title": "...", "status": "Manual"}, ...]}}
    Returns {} when no summary table is found (e.g. unexpected PDF layout).
    """
    entries: list[tuple[str, str]] = []  # (number, text) with wrapped lines joined
    cur_num, cur_txt = None, ""
    for ln in _summary_table_lines(text):
        if not ln or _NOISE.match(ln):
            continue
        m = _ENTRY_START.match(ln)
        starts_entry = False
        if m:
            if "." in m.group(1):
                starts_entry = True
            elif _TOP_HEADING.match(ln):
                # an undotted number starts a section heading only if the
                # previous entry is finished (otherwise it is a wrapped line)
                starts_entry = (
                    cur_num is None or bool(_STATUS_END.search(cur_txt)) or "." not in cur_num
                    or cur_txt.count(" ") < 8 and not cur_txt.startswith("Ensure")
                )
        if starts_entry:
            if cur_num is not None:
                entries.append((cur_num, cur_txt))
            cur_num, cur_txt = m.group(1), m.group(2).strip()
        elif cur_num is not None:
            cur_txt = f"{cur_txt} {ln}".strip()
    if cur_num is not None:
        entries.append((cur_num, cur_txt))

    sections: dict = {}
    for num, txt in entries:
        txt = re.sub(r"\s+", " ", txt)
        top = num.split(".")[0]
        status = _STATUS_END.search(txt)
        if status:  # a recommendation
            sec = sections.setdefault(top, {"title": "", "recommendations": []})
            sec["recommendations"].append(
                {"id": num, "title": txt[: status.start()].strip(), "status": status.group(1)}
            )
        elif "." not in num:  # a top-level section heading
            sections.setdefault(top, {"title": "", "recommendations": []})["title"] = txt
        # sub-section headings (e.g. "1.1 Linux Hosts Specific Configuration") are skipped
    return {k: v for k, v in sections.items() if v["recommendations"]}


def format_recommendations(sections: dict, only: list[str] | None = None) -> str:
    """Render parsed sections as compact text for use inside a prompt.

    Pass `only=["4"]` to render just one section, which is how the text is
    split into model-sized chunks (one top-level section per prompt).
    """
    parts = []
    for num, sec in sections.items():
        if only is not None and num not in only:
            continue
        parts.append(f"## {num} {sec['title']}".rstrip())
        for rec in sec["recommendations"]:
            parts.append(f"{rec['id']} {rec['title']} ({rec['status']})")
        parts.append("")
    return "\n".join(parts).strip()


def extract_recommendation_summary(pdf_path) -> dict:
    """PDF -> parsed summary-table sections (see parse_summary_table)."""
    return parse_summary_table(extract_pdf_text(pdf_path))

# ==========================================================================
# FUNCTIONS 2-4: PROMPT BUILDERS
# ==========================================================================

OUTPUT_FORMAT = """\
Return ONLY valid YAML in exactly this structure (no commentary, no code fences):

element1:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <short name of the key data element>
  requirements:
    - <requirement 1>
"""

DEFINITION = """\
A key data element (KDE) is a distinct configuration target, object, or component
that the security benchmark gives requirements about (for example: Docker daemon
configuration, container images and build files, container runtime, host
configuration, Docker Swarm). A single KDE can map to several requirements. A
requirement is a concrete recommendation that applies to that KDE (for example:
"Ensure that a user for the container has been created"; "Ensure that COPY is used
instead of ADD in Dockerfiles").

The documents are lists of numbered recommendations such as
"4.1 Ensure that a user for the container has been created (Manual)", grouped under
section headings that start with "##". Write each requirement as the recommendation
title, without its number and without the (Manual) / (Automated) label.\
"""

ZERO_SHOT_TEMPLATE = """\
You are a security compliance analyst. Read the two CIS Docker Benchmark excerpts below and identify the key data elements (KDEs) and the requirements attached to each KDE.

{definition}

Rules:
- Use only information that appears in the documents.
- Group requirements under the KDE they belong to.
- Do not invent elements or requirements.

{output_format}
### DOCUMENT 1: {name1}
{text1}

### DOCUMENT 2: {name2}
{text2}

### YAML OUTPUT
"""

FEW_SHOT_EXAMPLES = """\
### EXAMPLE 1
Document excerpt:
## 4 Container Images and Build File Configuration
4.1 Ensure that a user for the container has been created (Manual)
4.6 Ensure that HEALTHCHECK instructions have been added to container images (Manual)
4.7 Ensure update instructions are not used alone in Dockerfiles (Manual)
4.9 Ensure that COPY is used instead of ADD in Dockerfiles (Manual)

YAML output:
element1:
  name: Container images and build files
  requirements:
    - Ensure that a user for the container has been created
    - Ensure that HEALTHCHECK instructions have been added to container images
    - Ensure update instructions are not used alone in Dockerfiles
    - Ensure that COPY is used instead of ADD in Dockerfiles

### EXAMPLE 2
Document excerpt:
## 2 Docker daemon configuration
2.2 Ensure network traffic is restricted between containers on the default bridge (Manual)
2.3 Ensure the logging level is set to 'info' (Manual)
2.5 Ensure insecure registries are not used (Manual)
2.6 Ensure aufs storage driver is not used (Manual)

YAML output:
element1:
  name: Docker daemon
  requirements:
    - Ensure network traffic is restricted between containers on the default bridge
    - Ensure the logging level is set to 'info'
    - Ensure insecure registries are not used
    - Ensure aufs storage driver is not used

### EXAMPLE 3
Document excerpt:
## 5 Container Runtime Configuration
5.5 Ensure that privileged containers are not used (Manual)
5.10 Ensure that the host's network namespace is not shared (Manual)
5.11 Ensure that the memory usage for containers is limited (Manual)

YAML output:
element1:
  name: Container runtime
  requirements:
    - Ensure that privileged containers are not used
    - Ensure that the host's network namespace is not shared
    - Ensure that the memory usage for containers is limited
"""

FEW_SHOT_TEMPLATE = """\
You are a security compliance analyst. Identify the key data elements (KDEs) and the requirements attached to each KDE in CIS Docker Benchmark documents.

{definition}

{output_format}
Here are worked examples of the task:

{examples}
Now do the same for the two real documents below. Use only information in the documents.

### DOCUMENT 1: {name1}
{text1}

### DOCUMENT 2: {name2}
{text2}

### YAML OUTPUT
"""

CHAIN_OF_THOUGHT_TEMPLATE = """\
You are a security compliance analyst. Identify the key data elements (KDEs) and their requirements in the two CIS Docker Benchmark excerpts below. Think step by step.

{definition}

Work through these steps in order:
Step 1: Read each document and list every numbered recommendation (for example "4.1 Ensure ...") together with its title.
Step 2: For each recommendation, decide which component it is about (Docker daemon, container images and build files, container runtime, host configuration, and so on). That component is the KDE.
Step 3: Group recommendations that share the same KDE. One KDE may have many requirements.
Step 4: Give each KDE a short, clear name and write each requirement as the recommendation title.
Step 5: Re-check that every KDE and requirement came from the documents and nothing was invented.

Write your reasoning briefly under the heading REASONING. Then write the final answer under the heading FINAL YAML.

{output_format}
### DOCUMENT 1: {name1}
{text1}

### DOCUMENT 2: {name2}
{text2}

### REASONING
"""


def _check_inputs(text1: str, text2: str, name1: str, name2: str) -> None:
    for label, value in (("text1", text1), ("text2", text2)):
        if not isinstance(value, str):
            raise TypeError(f"{label} must be a string, got {type(value).__name__}")
        if not value.strip():
            raise ValueError(f"{label} is empty")
    for label, value in (("name1", name1), ("name2", name2)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must be a non-empty string")


def build_zero_shot_prompt(
    text1: str, text2: str, name1: str = "document-1", name2: str = "document-2"
) -> str:
    """Zero-shot prompt: task description and output format only, no examples."""
    _check_inputs(text1, text2, name1, name2)
    return ZERO_SHOT_TEMPLATE.format(
        definition=DEFINITION,
        output_format=OUTPUT_FORMAT,
        name1=name1,
        text1=text1.strip(),
        name2=name2,
        text2=text2.strip(),
    )


def build_few_shot_prompt(
    text1: str, text2: str, name1: str = "document-1", name2: str = "document-2"
) -> str:
    """Few-shot prompt: task description plus three worked examples."""
    _check_inputs(text1, text2, name1, name2)
    return FEW_SHOT_TEMPLATE.format(
        definition=DEFINITION,
        output_format=OUTPUT_FORMAT,
        examples=FEW_SHOT_EXAMPLES,
        name1=name1,
        text1=text1.strip(),
        name2=name2,
        text2=text2.strip(),
    )


def build_chain_of_thought_prompt(
    text1: str, text2: str, name1: str = "document-1", name2: str = "document-2"
) -> str:
    """Chain-of-thought prompt: explicit step-by-step reasoning before the YAML."""
    _check_inputs(text1, text2, name1, name2)
    return CHAIN_OF_THOUGHT_TEMPLATE.format(
        definition=DEFINITION,
        output_format=OUTPUT_FORMAT,
        name1=name1,
        text1=text1.strip(),
        name2=name2,
        text2=text2.strip(),
    )

# ==========================================================================
# FUNCTION 5: KDE EXTRACTION WITH GEMMA-3-1B  (teammate: add code here)
# ==========================================================================

# TODO


# ==========================================================================
# FUNCTION 6: DUMP LLM OUTPUT TO TEXT FILE  (teammate: add code here)
# ==========================================================================

# TODO

