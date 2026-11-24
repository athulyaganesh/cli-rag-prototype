# Support Copilot

A prototype customer assistant that works with any set of PDF documents. It answers questions from those documents, cites the document and page it used, and says when it doesn't know instead of guessing.

> **Status:** early prototype, tested on publicly available product documentation. See [Example results](#example-results).

## How it works

1. **Ingest.** Put PDF documents in a folder. Each run reads them, splits them into chunks, embeds them with Gemini, and stores them in a local Chroma database (`db/`). Unchanged files are skipped and changed files are re-indexed.
2. **Retrieve.** For each question, it finds the 5 most relevant chunks and drops any below a relevance threshold.
3. **Answer.** Gemini Flash answers using only those chunks and cites them by number.
4. **Escalate.** If nothing relevant is found, the answer has no valid citations, or the topic is off-limits (pricing, warranties, passwords and so on), it replies "Sorry, I don't have access to that information." and flags the question for a human.

## Setup

Tested with Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your key
```

Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/) and set `GOOGLE_API_KEY` in `.env`. Never commit `.env`.

Optional: set `RELEVANCE_THRESHOLD` in `.env` (default `0.5`). Higher means stricter matching and more escalations.

## Usage

Run from the project root:

```bash
# Ask questions interactively
python src/copilot.py --docs docs/ --mode chat

# Draft a reply to a customer email
python src/copilot.py --docs docs/ --mode email < email.txt

# Index documents only
python src/ingest.py --docs docs/
```

Email mode prints a draft with a greeting and sign-off, and sources listed for the reviewer, or `NEEDS HUMAN: <reason>` if the question should go to support staff.

## Example results

From testing on publicly available product documentation. Product and vendor names are replaced with placeholders, and long answers are summarized.

### 1. Specifications

**Question:** What are the two capacity ranges and increments listed for Product A?

**Answer:** Two ranges, each with its own increment, in both imperial and metric units.

**Source:** Product A documentation, page 2.

### 2. Software integrations

**Question:** Which software platforms are mentioned as integrating with or managing Product A?

**Answer:** Two platforms:

1. An enterprise management tool for managing the vendor's devices.
2. An order-integration tool that sends online retail orders directly to the device.

**Source:** Product A documentation, page 5.

### 3. Unsupported question (escalation)

**Question:** How do you configure the built-in tap-to-pay card reader on Product A?

**Answer:** Sorry, I don't have access to that information.

**Escalation reason:** The documentation has no instructions for a tap-to-pay reader, so the assistant declines instead of inventing an answer, and flags the question for a human.

### 4. Answers across multiple pages

**Question:** What are the external dimensions of Product A with the optional customer display?

**Answer:** The documentation lists two configurations, depending on the size of the operator display, each with ten dimensions.

**Sources:** Product A documentation, pages 4 and 7.

The dimensions come from labeled diagrams, so the extracted text has the numbers but not which measurement each one is. The assistant gives them in source order and points to the diagrams instead of guessing.

## Project layout

| Path | Purpose |
| --- | --- |
| `src/ingest.py` | Load, chunk, embed and store PDFs |
| `src/rag.py` | `answer()`: retrieval, Gemini call, citation checks |
| `src/copilot.py` | Command-line tool: chat and email modes |
| `prompts/system_prompt.md` | Rules Gemini must follow |
| `ai-tool-principles/` | Project spec and coding conventions for AI coding assistants |

## Limits

- Prototype only, not deployed or measured in production.
- PDFs removed from the docs folder stay in the database until `db/` is deleted.
