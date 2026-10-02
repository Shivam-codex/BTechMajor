"""
Unit tests for deterministic rule-based complaint classifier.
Verifies all 9 municipal categories, bilingual accuracy (English & Marathi),
scoring thresholds, and transparent explainability reasons.
"""

from backend.app.services.classification.classifier import classify_complaint
from backend.app.services.classification.department_router import assign_department
from backend.app.utils.constants import ComplaintCategory, DepartmentName, ComplaintStatus


def test_classify_water_supply():
    text = "The drinking water supply pipeline has a massive leak and water pressure is very low."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.WATER_SUPPLY.value
    assert res.rule_match_score > 0.6
    assert any(k in ["water", "leak", "pipeline", "pressure"] for k in res.matched_keywords)
    assert res.status == ComplaintStatus.CLASSIFIED.value


def test_classify_marathi_water_supply():
    text = "आमच्या भागात गेल्या ४ दिवसांपासून नळाला पिण्याचे पाणी येत नाही, त्वरित पाणी पुरवठा सुरू करा."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.WATER_SUPPLY.value
    assert res.rule_match_score > 0.6
    assert "पाणी येत नाही" in res.matched_phrases or "पाणी" in res.matched_keywords


def test_classify_garbage_waste():
    text = "Garbage collection truck has not arrived for a week. Dustbins are overflowing with waste and bad smell."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.GARBAGE_WASTE.value
    assert res.rule_match_score > 0.6
    assert any(k in ["garbage", "waste", "dustbin"] for k in res.matched_keywords)


def test_classify_marathi_garbage():
    text = "रस्त्यावर कचरा साचला आहे आणि कचराकुंडी पूर्ण भरली आहे. दुर्गंधी पसरली आहे."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.GARBAGE_WASTE.value


def test_classify_road_pothole():
    text = "There is a deep pothole on the main road after rain. Damaged road is causing vehicle accidents."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.ROAD_POTHOLE.value
    assert any(k in ["pothole", "road"] for k in res.matched_keywords)


def test_classify_marathi_road_pothole():
    text = "रस्त्यावर मोठे खड्डे पडले असून डांबरीकरण खराब झाले आहे."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.ROAD_POTHOLE.value


def test_classify_street_light():
    text = "Street light is not working near crossroad 4. It is pitch dark at night creating safety issues."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.STREET_LIGHT.value
    assert "street light" in res.matched_keywords or "dark" in res.matched_keywords


def test_classify_drainage_sewerage():
    text = "The sewage gutter is overflowing into the street. Choked drainage line needs immediate unblocking."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.DRAINAGE_SEWERAGE.value
    assert any(k in ["drainage", "gutter", "sewer", "sewage"] for k in res.matched_keywords)


def test_classify_public_toilet():
    text = "The public toilet near bus station is completely dirty and urinals are broken with no water."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.PUBLIC_TOILET.value
    assert any(k in ["toilet", "urinal"] for k in res.matched_keywords)


def test_classify_electricity():
    text = "High voltage fluctuation caused transformer blast and power cut throughout the night."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.ELECTRICITY.value
    assert any(k in ["transformer", "electricity", "power", "voltage"] for k in res.matched_keywords)


def test_classify_traffic():
    text = "Severe traffic jam at Shivaji square due to broken traffic signal and illegal vehicle parking."
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.TRAFFIC.value
    assert any(k in ["traffic", "signal", "congestion", "parking"] for k in res.matched_keywords)


def test_classify_unrelated_text_falls_to_other():
    text = "Can you recommend a good recipe for making chocolate cake at home?"
    res = classify_complaint(text)
    assert res.category == ComplaintCategory.OTHER.value
    assert res.status == ComplaintStatus.NEEDS_REVIEW.value
    assert res.rule_match_score == 0.0


def test_department_routing():
    dept, _ = assign_department(ComplaintCategory.WATER_SUPPLY.value)
    assert dept == DepartmentName.WATER_SUPPLY.value

    dept, _ = assign_department(ComplaintCategory.ROAD_POTHOLE.value)
    assert dept == DepartmentName.ROADS_INFRASTRUCTURE.value

    dept, _ = assign_department(ComplaintCategory.OTHER.value)
    assert dept == DepartmentName.GENERAL_GRIEVANCE.value
