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
