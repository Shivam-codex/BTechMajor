"""
Unit tests for deterministic priority detection engine.
Verifies Critical, High, Medium, and Low severity routing.
"""

from backend.app.services.classification.priority_detector import detect_priority
from backend.app.utils.constants import ComplaintPriority


def test_priority_critical_exposed_wire():
    text = "There is an exposed electrical wire sparking on the street creating an electrocution risk!"
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.CRITICAL.value
    assert res.priority_score == 1.0
    assert any("wire" in k or "risk" in k or "spark" in k for k in res.detected_keywords)


def test_priority_critical_marathi():
    text = "रस्त्यावर विजेची उघडी तार पडली असून मोठा अपघात होण्याची भीती आहे."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.CRITICAL.value


def test_priority_high_prolonged_disruption():
    text = "There has been no water for several days in our society and residents are suffering."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.HIGH.value
    assert res.priority_score == 0.75


def test_priority_high_blocked_road():
    text = "Road is completely blocked due to fallen tree branch near school gate."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.HIGH.value


def test_priority_medium_standard_complaint():
    text = "Street light bulb is flickering occasionally near street corner."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.MEDIUM.value
    assert res.priority_score == 0.50


def test_priority_low_inquiry():
    text = "General inquiry regarding procedure for requesting a new dustbin."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.LOW.value
    assert res.priority_score == 0.25


def test_priority_policy_small_pothole_is_low():
    text = "There is a small pothole on the corner with no immediate hazard."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.LOW.value


def test_priority_policy_minor_water_leak_is_low():
    text = "Minor water leak from garden pipe dripping slowly onto curb."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.LOW.value


def test_priority_policy_substantial_water_leak_is_medium():
    text = "There is a substantial water leak from the municipal connection on the street corner."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.MEDIUM.value


def test_priority_policy_blocked_main_road_is_high():
    text = "Main road completely blocked creating a serious traffic hazard during peak hours."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.HIGH.value


def test_priority_policy_confirmed_sparking_wire_is_critical():
    text = "Confirmed dangerous electrical short circuit with exposed sparking wires hanging over footpath."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.CRITICAL.value


def test_priority_negation_suppresses_emergency_trigger():
    text = "There is no accident and no emergency here, just a small crack on the pedestrian footpath."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.LOW.value
    assert any("negated" in u for u in res.uncertainty_indicators)


def test_priority_hypothetical_suppresses_critical():
    text = "Please repair this pavement crack soon to prevent accidents in the future."
    res = detect_priority(text)
    assert res.priority in [ComplaintPriority.LOW.value, ComplaintPriority.MEDIUM.value]
    assert res.priority != ComplaintPriority.CRITICAL.value
    assert any("hypothetical" in u for u in res.uncertainty_indicators)


def test_priority_historical_incident_does_not_escalate():
    text = "Last year there was a fire here, but right now some leaves need routine clearing."
    res = detect_priority(text)
    assert res.priority in [ComplaintPriority.LOW.value, ComplaintPriority.MEDIUM.value]
    assert res.priority != ComplaintPriority.CRITICAL.value


def test_priority_vague_complaint_requires_review():
    text = "Something bad happened near junction accident."
    res = detect_priority(text)
    assert res.priority == ComplaintPriority.REVIEW_REQUIRED.value
    assert "vague_emergency_or_insufficient_evidence" in res.uncertainty_indicators


def test_priority_contradictory_evidence_requires_review():
    text = "Catastrophic road collapse with multiple vehicles destroyed and massive danger."
    vis_evidence = {
        "apparent_damage": "none",
        "hazard_markers": [],
        "visual_priority": "Low",
        "vision_source": "ollama_gemma3:4b",
    }
    res = detect_priority(text, visual_evidence=vis_evidence)
    assert res.priority == ComplaintPriority.REVIEW_REQUIRED.value
    assert "contradictory_multimodal_evidence" in res.escalation_reasons
