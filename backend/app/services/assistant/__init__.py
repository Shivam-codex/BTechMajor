"""
Non-ML Retrieval-Augmented Municipal Assistant.
Provides deterministic responses directly grounded in the local municipal knowledge base.
ZERO MACHINE LEARNING / ZERO GENERATIVE AI.
"""

from backend.app.services.assistant.assistant_service import query_municipal_assistant, AssistantAnswer

__all__ = ["query_municipal_assistant", "AssistantAnswer"]
