"""
Rule-Based Priority Detection Engine.
Deterministically computes severity levels (Critical, High, Medium, Low)
using explicit hazard indicators, public health impact, and obstruction markers.
ZERO MACHINE LEARNING.
"""

from typing import List, Tuple
from dataclasses import dataclass, field
from backend.app.services.nlp.preprocessing import NLPPreprocessedResult, preprocess_complaint
from backend.app.utils.constants import ComplaintPriority

# Priority scoring markers
CRITICAL_TRIGGERS: List[str] = [
    # English
    "emergency", "accident", "accidents", "exposed electrical wire", "exposed wire",
    "hanging wire", "loose wire", "severe flooding", "dangerous", "life threatening",
    "transformer blast", "electrocution risk", "gas leak", "building collapse",
    "fatal", "fire breakout", "cave in", "sparking wire", "open manhole near school",
    "electric shock", "hospital emergency", "pipe burst", "dead animal", "open manhole",
    "broken manhole", "sparking", "electrocution", "road cave-in", "road cave in",
    # Marathi
    "अपघात", "विजेची उघडी तार", "उघडी तार", "धोकादायक", "पूर", "भिंत कोसळली",
    "जीवघेणा", "ठिणग्या", "शॉर्ट सर्किट", "आग लागली", "रस्ता खचला", "आपत्कालीन",
    "मॅनहोल उघडे", "करंट लागला", "पाईप फुटला", "मृत प्राणी",
    # Transliteration
    "accident", "dhokadayak", "apghat", "wire ughadi", "fire", "pipe burst",
]

HIGH_TRIGGERS: List[str] = [
    # English
    "completely blocked", "no water for several days", "no water since", "days without water",
    "massive garbage accumulation", "dangerous road", "sewage entering houses", "hospital road",
    "school gate", "contaminated water causing illness", "main road blocked", "epidemic",
    "deep crater", "heavy traffic jam", "foul smell entering house", "contaminated",
    "contamination", "pipeline leakage", "major leak", "gridlock", "traffic jam",
    "overflowing", "overflow", "dark street", "total darkness", "load shedding",
    "power cut", "choked", "blocked drain", "foul smell", "water crisis",
    # Marathi
    "रस्ता पूर्ण बंद", "अनेक दिवस पाणी नाही", "पाणी नाही अनेक दिवस", "दुर्गंधी",
    "मोठा खड्डा", "घरात पाणी शिरले", "सांडपाणी घरात", "कचऱ्याचे मोठे ढीग",
    "रुग्णालय रस्ता", "आजारी", "रोगराई", "वाहने आदळली", "वाहतूक ठप्प",
    "गळती", "वाहतूक कोंडी", "अंधार", "भारनियमन", "तुंबले", "सांडपाणी", "अस्वच्छ",
    # Transliteration
    "rasta band", "paani nahi", "gatar tumble", "gharala paani", "traffic jam",
]

LOW_TRIGGERS: List[str] = [
    # English
    "inquiry", "information", "suggestion", "minor issue", "cosmetic",
    "procedure query", "general question", "status check", "request for info",
    "request", "permission", "guidelines", "timing", "schedule", "tree pruning",
    "pruning", "rebate", "property tax", "tax", "certificate", "birth certificate",
    # Marathi
    "माहिती हवी", "चौकशी", "सूचना", "साधी विचारणा", "नियम काय आहेत",
    "माहिती", "विनंती", "वेळापत्रक", "दाखला", "सवलत", "फांद्या छाटणी",
]


@dataclass
class PriorityResult:
    priority: str
    priority_score: float
    detected_keywords: List[str] = field(default_factory=list)
    priority_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "priority": self.priority,
            "priority_score": self.priority_score,
            "detected_keywords": self.detected_keywords,
            "priority_reason": self.priority_reason,
        }


def detect_priority(input_data: any) -> PriorityResult:
    """
    Deterministically computes grievance urgency based on keyword & hazard matching.
    Priority hierarchy: Critical > High > Low (explicit) > Medium (default baseline).
    """
    if isinstance(input_data, str):
        nlp_result = preprocess_complaint(input_data)
    else:
        nlp_result = input_data

    lower_text = nlp_result.normalized_text.lower()
    token_set = nlp_result.token_set | nlp_result.lemmatized_set

    # 1. Check Critical triggers
    matched_critical = []
    for trigger in CRITICAL_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_text or trigger_clean in token_set:
            matched_critical.append(trigger)

    if matched_critical:
        unique_crit = list(dict.fromkeys(matched_critical))
        return PriorityResult(
            priority=ComplaintPriority.CRITICAL.value,
            priority_score=1.0,
            detected_keywords=unique_crit,
            priority_reason=f"Immediate hazard detected ({', '.join(repr(k) for k in unique_crit[:3])}). Requires prompt emergency intervention.",
        )

    # 2. Check High triggers
    matched_high = []
    for trigger in HIGH_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_text or trigger_clean in token_set:
            matched_high.append(trigger)

    if matched_high:
        unique_high = list(dict.fromkeys(matched_high))
        return PriorityResult(
            priority=ComplaintPriority.HIGH.value,
            priority_score=0.75,
            detected_keywords=unique_high,
            priority_reason=f"Severe municipal disruption indicated ({', '.join(repr(k) for k in unique_high[:3])}).",
        )

    # 3. Check Low triggers (inquiries/minor suggestions)
    matched_low = []
    for trigger in LOW_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_text or trigger_clean in token_set:
            matched_low.append(trigger)

    if matched_low and len(nlp_result.tokens) < 25:
        unique_low = list(dict.fromkeys(matched_low))
        return PriorityResult(
            priority=ComplaintPriority.LOW.value,
            priority_score=0.25,
            detected_keywords=unique_low,
            priority_reason=f"Informational / minor suggestion indicator ({', '.join(repr(k) for k in unique_low[:2])}).",
        )

    # 4. Default standard municipal grievance baseline
    return PriorityResult(
        priority=ComplaintPriority.MEDIUM.value,
        priority_score=0.50,
        detected_keywords=[],
        priority_reason="Standard municipal grievance without immediate hazard or total blockage indicators.",
    )
