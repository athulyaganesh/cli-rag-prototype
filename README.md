# Support Copilot

A prototype customer assistant that works with any set of PDF documents. It answers questions from those documents, cites the document and page it used, and says when it doesn't know instead of guessing.

> **Status:** early prototype. The code is written but hasn't been run end to end yet.

## How it works

1. **Ingest.** Put PDF documents in a folder. Each run reads them, splits them into chunks, embeds them with Gemini, and stores them in a local Chroma database (`db/`). Unchanged files are skipped and changed files are re-indexed.
2. **Retrieve.** For each question, it finds the 5 most relevant chunks and drops any below a relevance threshold.
3. **Answer.** Gemini Flash answers using only those chunks and cites them by number.
4. **Escalate.** If nothing relevant is found, the answer has no valid citations, or the topic is off-limits (pricing, warranties, passwords and so on), it replies "Sorry, I don't have access to that information." and flags the question for a human.

## Setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install langchain-community langchain-text-splitters langchain-google-genai langchain-chroma pymupdf python-dotenv
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
