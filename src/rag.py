"""Answer support questions from the indexed docs, or escalate to a human.

answer() is the only entry point; the CLI and web app both call it.
"""

import logging
import os
from functools import cache
from pathlib import Path
from typing import Literal

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from ingest import open_vector_store

CHAT_MODEL = "gemini-3.5-flash"
RETRIEVAL_K = 5
DEFAULT_RELEVANCE_THRESHOLD = "0.5"
NO_ACCESS_MESSAGE = "Sorry, I don't have access to that information."
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.md"
EMAIL_PROMPT_PATH = PROMPTS_DIR / "email_prompt.md"

Mode = Literal["chat", "email"]

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """Where part of an answer came from."""

    source: str
    page: int


class AnswerResult(BaseModel):
    """What answer() returns. When escalate is True, answer is NO_ACCESS_MESSAGE."""

    answer: str
    citations: list[Citation]
    escalate: bool
    reason: str


class ModelReply(BaseModel):
    """The structured reply the LLM must fill in."""

    answer: str = Field(description="Answer for the customer, using only the numbered chunks.")
    cited_chunks: list[int] = Field(description="Numbers of the chunks the answer relies on.")
    escalate: bool = Field(description="True if the chunks don't cover it or it's a forbidden topic.")
    reason: str = Field(description="Short note for support staff on why it was escalated, else empty.")


@cache
def get_vector_store() -> Chroma:
    return open_vector_store()


@cache
def get_llm() -> Runnable:
    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)
    return llm.with_structured_output(ModelReply)


@cache
def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_system_prompt(mode: Mode) -> str:
    """The shared rules, plus reply-writing instructions in email mode."""
    system_prompt = load_prompt(SYSTEM_PROMPT_PATH)
    if mode == "email":
        return f"{system_prompt}\n\n{load_prompt(EMAIL_PROMPT_PATH)}"
    return system_prompt


def retrieve_relevant_chunks(question: str) -> list[Document]:
    """Return the top-k chunks whose relevance score meets RELEVANCE_THRESHOLD."""
    # Read at call time so a value from .env (loaded by the CLI) takes effect.
    threshold = float(os.getenv("RELEVANCE_THRESHOLD", DEFAULT_RELEVANCE_THRESHOLD))
    scored_chunks = get_vector_store().similarity_search_with_relevance_scores(
        question, k=RETRIEVAL_K
    )
    for chunk, score in scored_chunks:
        logger.debug("score %.3f  %s p.%s", score, chunk.metadata["source"], chunk.metadata["page"])
    return [chunk for chunk, score in scored_chunks if score >= threshold]


def build_user_message(question: str, chunks: list[Document]) -> str:
    """Number each chunk with its source and page, then append the customer's text."""
    numbered_chunks = "\n\n".join(
        f"[{number}] {chunk.metadata['source']}, page {chunk.metadata['page']}\n{chunk.page_content}"
        for number, chunk in enumerate(chunks, start=1)
    )
    return (
        f"Documentation chunks:\n\n{numbered_chunks}\n\n"
        f"<customer_text>\n{question}\n</customer_text>"
    )


def collect_citations(cited_numbers: list[int], chunks: list[Document]) -> list[Citation]:
    """Map cited chunk numbers to unique {source, page} pairs.

    Returns an empty list if any number points to a chunk that wasn't sent,
    so an invented citation can never pass the check in answer().
    """
    citations: list[Citation] = []
    for number in cited_numbers:
        if not 1 <= number <= len(chunks):
            return []
        metadata = chunks[number - 1].metadata
        citation = Citation(source=metadata["source"], page=metadata["page"])
        if citation not in citations:
            citations.append(citation)
    return citations


def escalate(reason: str) -> AnswerResult:
    return AnswerResult(answer=NO_ACCESS_MESSAGE, citations=[], escalate=True, reason=reason)


def answer(question: str, mode: Mode = "chat") -> AnswerResult:
    """Answer a question (or, in email mode, a customer email) from the docs, or escalate.

    Escalates without calling the LLM when no chunk is relevant enough.
    API errors from Gemini or Chroma are not caught here; the CLI and app handle them.
    """
    chunks = retrieve_relevant_chunks(question)
    if not chunks:
        return escalate("No documentation passed the relevance threshold.")

    reply = get_llm().invoke(
        [("system", build_system_prompt(mode)), ("human", build_user_message(question, chunks))]
    )
    if not isinstance(reply, ModelReply):
        return escalate("The model's reply could not be parsed.")
    if reply.escalate:
        return escalate(reply.reason or "The model escalated without giving a reason.")

    citations = collect_citations(reply.cited_chunks, chunks)
    if not citations:
        return escalate("The model's answer had missing or invalid citations.")
    return AnswerResult(answer=reply.answer, citations=citations, escalate=False, reason="")
