"""
Unit tests for the Conversational Municipal Assistant and Response Generator.
Verifies grounded response synthesis, source attribution, safe fallback on irrelevant queries,
and Google GenAI integration with graceful fallback behavior.
"""

from unittest.mock import MagicMock, patch
from backend.app.services.assistant.assistant_service import (
    query_municipal_assistant,
    search_knowledge_base,
)
from backend.app.services.assistant.response_generator import (
    generate_llm_response,
    format_deterministic_response,
)
from backend.app.services.retrieval.ranking import RetrievalResult


def test_assistant_answers_road_pothole():
    ans = query_municipal_assistant("How can I complain about a pothole on my street?")
    assert ans.has_answer
    assert ans.confidence > 0.12
    assert "Sample Municipal Knowledge Base" in ans.answer
    assert len(ans.sources) > 0
    # Check source transparency
    assert any("pothole" in s["title"].lower() or "road" in s["title"].lower() or "faq" in s["title"].lower() for s in ans.sources)


def test_assistant_answers_water_burst_emergency():
    ans = query_municipal_assistant("What is the turnaround time for a major water pipeline burst?")
    assert ans.has_answer
    assert any(k in ans.answer for k in ["Water", "Pipeline", "Hours", "SLA", "1800-233-0001"])
    assert any("water" in s["title"].lower() or "sla" in s["title"].lower() for s in ans.sources)
    assert len(ans.retrieved_chunks) > 0


def test_assistant_fallback_on_unrelated_query():
    ans = query_municipal_assistant("Can you write a poem about stars in the night sky?")
    # Out of domain query should safely trigger fallback without hallucinations
    assert not ans.has_answer or ans.confidence < 0.15
    if not ans.has_answer:
        assert "could not find sufficient information" in ans.answer.lower()
        assert len(ans.sources) == 0


def test_assistant_empty_query():
    ans = query_municipal_assistant("")
    assert not ans.has_answer
    assert "Please enter a question" in ans.answer


def test_search_knowledge_base():
    results = search_knowledge_base("garbage collection schedule", top_k=3)
    assert len(results) > 0
    assert any("garbage" in r.text.lower() or "waste" in r.text.lower() for r in results)

    # Empty question
    empty_res = search_knowledge_base("")
    assert empty_res == []


def test_generate_llm_response_mocked_gemini():
    """Verifies that generate_llm_response properly calls Google GenAI SDK and formats response."""
    sample_chunk = RetrievalResult(
        chunk_id="KB-001_chk_01",
        document_id="KB-001",
        title="Pothole Repair Standard Operating Procedure",
        category="Roads",
        department="Roads & Infrastructure",
        source="Municipal Charter",
        score=0.45,
        text="Potholes reported via portal are inspected within 24 hours and repaired within 48 hours.",
    )

    mock_response = MagicMock()
    mock_response.text = (
        "According to the official **Sample Municipal Knowledge Base**:\n\n"
        "1. **Inspection**: Roads & Infrastructure Department inspects potholes within 24 hours.\n"
        "2. **Repair**: Resolution is completed within 48 hours under standard SLA."
    )

    with patch("backend.app.services.assistant.response_generator.genai.Client") as mock_client_cls, \
         patch("backend.app.services.assistant.response_generator.settings.GEMINI_API_KEY", "test-api-key"), \
         patch("backend.app.services.assistant.response_generator.generate_ollama_response", return_value=None):
        
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_instance

        answer = generate_llm_response("How fast are potholes fixed?", [sample_chunk])

        assert "Sample Municipal Knowledge Base" in answer
        assert "Roads & Infrastructure Department" in answer
        assert "24 hours" in answer
        mock_instance.models.generate_content.assert_called_once()


def test_generate_llm_response_graceful_fallback_on_api_error():
    """Verifies that if Google GenAI API raises an exception, the system gracefully returns local template."""
    sample_chunk = RetrievalResult(
        chunk_id="KB-002_chk_01",
        document_id="KB-002",
        title="Water Supply Protocol",
        category="Water",
        department="Water Supply Department",
        source="Municipal Charter",
        score=0.5,
        text="Major pipeline bursts are addressed within 4 to 6 hours.",
    )

    with patch("backend.app.services.assistant.response_generator.genai.Client") as mock_client_cls, \
         patch("backend.app.services.assistant.response_generator.settings.GEMINI_API_KEY", "test-api-key"), \
         patch("backend.app.services.assistant.response_generator.generate_ollama_response", return_value=None):
        
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = RuntimeError("API Quota Exceeded")
        mock_client_cls.return_value = mock_instance

        # Should NOT raise RuntimeError; must fall back gracefully
        answer = generate_llm_response("What is the water burst timeline?", [sample_chunk])

        assert "Sample Municipal Knowledge Base" in answer
        assert "Water Supply Protocol" in answer
        assert "4 to 6 hours" in answer


def test_generate_llm_response_local_ollama_gemma3():
    """Verifies that generate_llm_response uses local Ollama Gemma 3 when GEMINI_API_KEY is empty."""
    sample_chunk = RetrievalResult(
        chunk_id="KB-003_chk_01",
        document_id="KB-003",
        title="Street Lighting Standards",
        category="Electricity",
        department="Electrical & Energy Department",
        source="Municipal Charter",
        score=0.48,
        text="Street lights are maintained daily and broken bulbs are replaced within 24 hours.",
    )

    mock_ollama_resp = MagicMock()
    mock_ollama_resp.status_code = 200
    mock_ollama_resp.json.return_value = {
        "response": "Broken street lights are repaired within 24 hours by the Electrical Department."
    }

    with patch("backend.app.services.assistant.response_generator.settings.GEMINI_API_KEY", ""), \
         patch("httpx.Client.post", return_value=mock_ollama_resp) as mock_post:
        
        answer = generate_llm_response("When will my street light be repaired?", [sample_chunk])
        assert "Broken street lights are repaired" in answer
        assert "Sample Municipal Knowledge Base" in answer
        assert mock_post.called

