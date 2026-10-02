"""
Non-ML Retrieval-Augmented Municipal Assistant API.
Answers citizen questions using deterministic TF-IDF knowledge base retrieval.
"""

from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.assistant_schema import AssistantQueryRequest, AssistantQueryResponse
from backend.app.services.assistant.assistant_service import query_municipal_assistant
from backend.app.core.security import sanitize_text_input

router = APIRouter(prefix="/assistant", tags=["Municipal Assistant"])


@router.get(
    "/status",
    summary="Get status of Non-ML Municipal Assistant",
)
def get_assistant_status():
    """Returns runtime status and indexing health of the Non-ML assistant."""
    from backend.app.services.retrieval.tfidf_retriever import tfidf_retriever
    chunks_count = len(tfidf_retriever.chunks) if tfidf_retriever.is_ready() else 0
    return {
        "status": "online",
        "retrieval_engine": "TF-IDF + Cosine Similarity (Non-ML)",
        "indexed_chunks": chunks_count,
    }


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    summary="Query the Non-ML Retrieval-Augmented Municipal Assistant",
)
@router.post(
    "/chat",
    response_model=AssistantQueryResponse,
    summary="Chat alias for Non-ML Retrieval-Augmented Municipal Assistant",
)
def query_assistant(payload: AssistantQueryRequest):
    """
    Submits citizen question to the deterministic NLP retrieval pipeline.
    Retrieves grounded municipal guidelines and returns factual response with source documents.
    """
    clean_question = sanitize_text_input(payload.question)
    if len(clean_question) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inquiry text is too short.",
        )

    try:
        answer = query_municipal_assistant(clean_question)
        return answer.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant query failed: {str(e)}",
        )
