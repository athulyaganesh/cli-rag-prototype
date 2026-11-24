"""Command-line support copilot.

Chat mode:  python src/copilot.py --docs docs/ --mode chat
Email mode: python src/copilot.py --docs docs/ --mode email < email.txt

Every run first syncs the docs folder into the vector store, then answers
through rag.answer(); this file never talks to the store or LLM directly.
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from ingest import ingest_docs
from rag import AnswerResult, Citation, answer

EXIT_COMMANDS = {"exit", "quit"}
EMAIL_GREETING = "Hello,\n\nThank you for contacting us."
EMAIL_SIGN_OFF = "Best regards,\nCustomer Support"

logger = logging.getLogger(__name__)


def format_sources(citations: list[Citation]) -> str:
    return "\n".join(f"- {citation.source}, page {citation.page}" for citation in citations)


def format_chat_reply(result: AnswerResult) -> str:
    """Answer plus sources, or the no-access message plus why it needs a human."""
    if result.escalate:
        return f"{result.answer}\n(Escalate to support: {result.reason})"
    return f"{result.answer}\n\nSources:\n{format_sources(result.citations)}"


def format_email_draft(result: AnswerResult) -> str:
    """A reply ready for staff review, or 'NEEDS HUMAN: <reason>'.

    Sources go below the sign-off so the reviewer can check them and
    delete them before sending.
    """
    if result.escalate:
        return f"NEEDS HUMAN: {result.reason}"
    return (
        f"{EMAIL_GREETING}\n\n{result.answer}\n\n{EMAIL_SIGN_OFF}\n\n"
        f"---\nSources (for reviewer, remove before sending):\n"
        f"{format_sources(result.citations)}"
    )


def run_chat() -> None:
    """Ask questions in a loop until 'exit', an empty line, or Ctrl+D/Ctrl+C."""
    print("Ask a question about your documents. Type 'exit' to quit.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not question or question.lower() in EXIT_COMMANDS:
            return
        # One failed question (e.g. a rate limit) shouldn't end the whole session.
        try:
            print(format_chat_reply(answer(question)))
        except Exception as error:
            logger.error("Could not answer: %s: %s", type(error).__name__, error)


def run_email() -> None:
    """Read one customer email from stdin and print a draft reply."""
    email_text = sys.stdin.read().strip()
    if not email_text:
        raise ValueError("No email text on stdin. Usage: --mode email < email.txt")
    print(format_email_draft(answer(email_text, mode="email")))


def main() -> None:
    parser = argparse.ArgumentParser(description="Support copilot.")
    parser.add_argument("--docs", type=Path, required=True, help="Folder of PDF files")
    parser.add_argument("--mode", choices=["chat", "email"], required=True)
    args = parser.parse_args()

    # Diagnostics go to stderr, so answers and drafts on stdout stay clean to redirect.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()

    try:
        ingest_docs(args.docs)
        if args.mode == "chat":
            run_chat()
        else:
            run_email()
    except Exception as error:
        logger.error("%s: %s", type(error).__name__, error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
