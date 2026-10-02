"""
Knowledge Base Management Package.
Loads, parses, cleans, and chunks academic municipal documents without ML.
"""

from backend.app.services.knowledge.knowledge_loader import load_and_chunk_knowledge_base, KnowledgeChunk

__all__ = ["load_and_chunk_knowledge_base", "KnowledgeChunk"]
