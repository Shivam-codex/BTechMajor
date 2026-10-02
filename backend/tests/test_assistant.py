"""
Unit tests for the Non-ML Municipal Assistant and Deterministic Response Generator.
Verifies grounded response synthesis, source attribution, and safe fallback on irrelevant queries.
"""

from backend.app.services.assistant.assistant_service import query_municipal_assistant


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
