"""
Knowledge Loader.
Loads all municipal documents from the knowledge repository directory,
cleans text, extracts metadata, and chunks into KnowledgeChunk objects.
"""

from pathlib import Path
from typing import List
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.knowledge.text_cleaner import clean_knowledge_text
from backend.app.services.knowledge.metadata_manager import extract_document_metadata
from backend.app.services.knowledge.chunker import chunk_document, KnowledgeChunk


def load_and_chunk_knowledge_base(kb_dir: Path = None) -> List[KnowledgeChunk]:
    """
    Traverses the knowledge base directory, processes all documents,
    and returns a flattened list of KnowledgeChunk instances.
    """
    if kb_dir is None:
        kb_dir = settings.KNOWLEDGE_BASE_DIR

    if not kb_dir.exists():
        logger.warning(f"Knowledge base directory does not exist: {kb_dir}")
        return []

    all_chunks: List[KnowledgeChunk] = []
    # Search for all supported document extensions
    doc_paths = sorted(list(kb_dir.glob("*.txt")) + list(kb_dir.glob("*.md")))

    for path in doc_paths:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()

            if not raw_content.strip():
                continue

            metadata, body_text = extract_document_metadata(raw_content, fallback_title=path.name)
            cleaned_body = clean_knowledge_text(body_text)
            chunks = chunk_document(cleaned_body, metadata)
            all_chunks.extend(chunks)

        except Exception as e:
            logger.error(f"Failed to process knowledge document {path.name}: {e}")

    logger.info(f"Loaded {len(doc_paths)} documents and produced {len(all_chunks)} knowledge chunks.")
    return all_chunks
