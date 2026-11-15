# COMP5700Project_HolderElkinsBrockman
# CIS Docker Benchmark Requirement Analyzer

Pipeline that extracts key data elements (KDEs) and requirements from CIS Docker Benchmark PDFs, compares versions, and maps differences to Hadolint rules.

## Team

|       Name       | Banner ID |  University Email  |
|------------------|-----------|--------------------|
| Sophie Holder    | 904365730 | slh0140@auburn.edu |
| Elise Elkins     | 904000000 | eme0037@auburn.edu |
| Vivian Brockman  | 904000000 | vmb0020@auburn.edu |

## LLM used for Task-1

**Gemma-3-1B** (`google/gemma-3-1b-it`, loaded via Hugging Face `transformers`).

## Project structure

```
src/            source code (Task-1, 2, 3)
tests/          test cases
PROMPT.md       zero-shot, few-shot and chain-of-thought prompts
requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Gemma models are gated on Hugging Face: accept the license on the model page and log in with `huggingface-cli login` before the first run.

## Run tests

```bash
python -m pytest
```
