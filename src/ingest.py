"""Index product PDFs into a local Chroma vector store.

Each run scans the docs folder: new PDFs are added, changed PDFs are
re-indexed, and unchanged PDFs are skipped (matched by SHA-256 hash).
"""

import argparse
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_DIR = Path("db")
COLLECTION_NAME = "support_docs"
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
SPLIT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
# Long manuals produce thousands of chunks; adding them in batches keeps each
# embedding request small and shows progress.
ADD_BATCH_SIZE = 100

logger = logging.getLogger(__name__)


@dataclass
class IngestReport:
    """Which PDFs were (re)indexed and which were skipped as unchanged."""

    indexed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def open_vector_store() -> Chroma:
    """Open (or create) the persisted Chroma collection with Gemini embeddings."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=str(DB_DIR),
    )


def compute_file_hash(pdf_path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    with pdf_path.open("rb") as pdf_file:
        return hashlib.file_digest(pdf_file, "sha256").hexdigest()


def load_pdf_pages(pdf_path: Path) -> list[Document]:
    """Load a PDF as one Document per non-empty page, with {source, page} metadata."""
    pages = PyMuPDFLoader(str(pdf_path)).load()
    return [
        Document(
            page_content=page.page_content,
            # PyMuPDF counts from 0; citations should match the PDF viewer's page number.
            metadata={"source": pdf_path.name, "page": page.metadata["page"] + 1},
        )
        for page in pages
        if page.page_content.strip()
    ]


def split_pages(pages: list[Document]) -> list[Document]:
    """Split pages into overlapping chunks; each chunk keeps its page's metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SPLIT_SEPARATORS,
    )
    return splitter.split_documents(pages)


def is_already_indexed(stored: dict, file_hash: str) -> bool:
    """True if the store holds every chunk of this exact file version.

    Checking the chunk count catches a run that crashed halfway through
    adding a file, which would otherwise be skipped forever.
    """
    if not stored["ids"]:
        return False
    first_metadata = stored["metadatas"][0]
    return (
        first_metadata.get("file_hash") == file_hash
        and first_metadata.get("chunk_count") == len(stored["ids"])
    )


def index_pdf(vector_store: Chroma, pdf_path: Path) -> bool:
    """Index one PDF, replacing any older version of it.

    Returns True if the file was indexed, False if skipped as unchanged.
    """
    file_hash = compute_file_hash(pdf_path)
    stored = vector_store.get(where={"source": pdf_path.name}, include=["metadatas"])
    if is_already_indexed(stored, file_hash):
        return False

    if stored["ids"]:
        vector_store.delete(ids=stored["ids"])

    chunks = split_pages(load_pdf_pages(pdf_path))
    if not chunks:
        logger.warning("No extractable text in %s (scanned PDF?)", pdf_path.name)
        return True

    for chunk in chunks:
        chunk.metadata.update({"file_hash": file_hash, "chunk_count": len(chunks)})

    for start in range(0, len(chunks), ADD_BATCH_SIZE):
        vector_store.add_documents(chunks[start : start + ADD_BATCH_SIZE])
        logger.info(
            "%s: embedded %d/%d chunks",
            pdf_path.name,
            min(start + ADD_BATCH_SIZE, len(chunks)),
            len(chunks),
        )
    return True


def ingest_docs(docs_dir: Path) -> IngestReport:
    """Sync every PDF in docs_dir into the vector store at DB_DIR.

    Raises:
        FileNotFoundError: docs_dir does not exist.
        ValueError: docs_dir contains no PDFs.
    """
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    pdf_paths = sorted(docs_dir.glob("*.pdf"))
    if not pdf_paths:
        raise ValueError(f"No PDF files found in {docs_dir}")

    vector_store = open_vector_store()

    report = IngestReport()
    for pdf_path in pdf_paths:
        if index_pdf(vector_store, pdf_path):
            report.indexed.append(pdf_path.name)
        else:
            report.skipped.append(pdf_path.name)
            logger.info("%s: unchanged, skipped", pdf_path.name)
    return report


def main() -> None:
    """CLI entry point: python src/ingest.py --docs docs/"""
    parser = argparse.ArgumentParser(description="Index PDFs into the vector store.")
    parser.add_argument("--docs", type=Path, required=True, help="Folder of PDF files")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()

    try:
        report = ingest_docs(args.docs)
    except Exception as error:
        logger.error("%s: %s", type(error).__name__, error)
        raise SystemExit(1) from error

    logger.info(
        "Done: %d indexed, %d unchanged", len(report.indexed), len(report.skipped)
    )


if __name__ == "__main__":
    main()
