"""
Non-ML Retrieval-Augmented Municipal Assistant API.
Answers citizen questions using deterministic TF-IDF knowledge base retrieval.
"""

from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.assistant_schema import AssistantQueryRequest, AssistantQueryResponse
from backend.app.services.assistant.assistant_service import query_municipal_assistant
from backend.app.core.security import sanitize_text_input

router = APIRouter(prefix="/assistant", tags=["Municipal Assistant"])


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    summary="Query the Non-ML Retrieval-Augmented Municipal Assistant",
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
