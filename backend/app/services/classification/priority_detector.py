"""
Rule-Based Priority & Severity Detection Engine.
Deterministically computes municipal grievance severity:
- CRITICAL: Immediate life-threatening emergency requiring urgent escalation.
- HIGH: Serious incident or substantial municipal damage requiring urgent intervention.
- MEDIUM: Significant but non-emergency civic problem requiring timely attention.
- LOW: Minor, routine, or cosmetic issue.
- REVIEW REQUIRED: Insufficient, contradictory, or unreliable evidence for confident assessment.

Context-aware: Handles negation, hypothetical statements, historical incidents,
qualifiers (minor vs severe), and correlates visual/audio/textual evidence.
ZERO BLACK-BOX NEURAL HALLUCINATIONS.
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from backend.app.services.nlp.preprocessing import NLPPreprocessedResult, preprocess_complaint
from backend.app.utils.constants import ComplaintPriority


# -------------------------------------------------------------------------
# Hazard & Urgency Trigger Dictionaries
# -------------------------------------------------------------------------

CRITICAL_EMERGENCY_TRIGGERS: List[str] = [
    # Immediate life threats & hazardous failures
    "exposed electrical wire", "exposed wire", "sparking wire", "hanging wire",
    "live wire", "loose wire", "wire sparking", "electric shock", "electrocution",
    "electrocution risk", "transformer blast", "transformer fire", "gas leak",
    "building collapse", "wall collapse", "bridge collapse", "road cave-in",
    "road cave in", "sinkhole", "fatal accident", "severe accident", "open manhole near school",
    "fire breakout", "active fire", "severe chemical leak", "life threatening",
    # Marathi (Immediate life hazards)
    "विजेची उघडी तार", "उघडी तार", "शॉर्ट सर्किट", "ठिणग्या", "करंट लागला",
    "ट्रान्सफॉर्मरचा स्फोट", "गॅस गळती", "भिंत कोसळली", "इमारत कोसळली",
    "रस्ता खचला", "मोठा खड्डा खचला", "जीवघेणा अपघात", "जीवघेणी परिस्थिती",
    "आग लागली", "धोकादायक उघडी तार", "आपत्कालीन परिस्थिती",
    # Transliteration
    "wire ughadi", "sparking", "current lagla", "transformer blast", "gas leak"
]

HIGH_SEVERITY_TRIGGERS: List[str] = [
    # Serious infrastructure disruptions
    "completely blocked", "main road blocked", "arterial road blocked",
    "major water pipe burst", "pipeline burst", "major water pipeline burst",
    "burst main pipeline", "burst pipeline", "burst pipe", "water pipe burst",
    "flooding houses", "sewage entering houses", "sewage overflow in homes",
    "water entering house", "deep open manhole", "broken manhole on road",
    "massive garbage accumulation", "garbage blocking road", "epidemic risk",
    "contaminated drinking water", "water contamination causing illness",
    "days without water", "no water for several days", "no water since",
    "gridlock", "total road blockage", "deep crater on highway",
    # Marathi (Serious disruption)
    "रस्ता पूर्ण बंद", "मुख्य रस्ता बंद", "मोठा पाईप फुटला", "पाईपलाईन फुटली",
    "घरात सांडपाणी शिरले", "घरात पाणी शिरले", "अनेक दिवस पाणी नाही",
    "पाणी नाही अनेक दिवस", "दूषित पाणी पुरवठा", "रोगराई पसरली",
    "कचऱ्याचे मोठे ढीग रस्ता बंद", "मॅनहोल उघडे", "उघडे मॅनहोल", "रस्ता तुंबला",
    # Transliteration
    "rasta band", "pipe burst", "paani nahi anek divas", "gharala paani", "gatar tumble"
]

MEDIUM_SEVERITY_TRIGGERS: List[str] = [
    # Significant non-emergency municipal issues
    "pothole", "potholes", "crater", "road damage", "damaged road",
    "pipeline leakage", "water leak", "water pipe leak", "water supply disrupted",
    "street light not working", "street lights off", "dark street", "light pole damaged",
    "garbage bin overflowing", "dustbin overflow", "garbage dump", "waste accumulation",
    "choked drain", "blocked gutter", "drainage overflow", "sewage overflow",
    "public toilet dirty", "toilet tap broken", "traffic jam", "foul smell",
    # Marathi (Standard municipal issues)
    "खड्डा", "खड्डे", "पाणी गळती", "पाईप गळती", "पथदिवा बंद", "दिवाबत्ती बंद",
    "कचराकुंडी भरली", "कचऱ्याचा ढीग", "गटार तुंबले", "सांडपाणी रस्त्यावर",
    "सार्वजनिक शौचालय अस्वच्छ", "दुर्गंधी", "वाहतूक कोंडी",
]

LOW_SEVERITY_TRIGGERS: List[str] = [
    # Minor, routine, cosmetic, or procedural inquiries
    "minor pothole", "small pothole", "small crack", "cosmetic damage",
    "faint road marking", "faint zebra crossing", "minor leak", "slight leakage",
    "water dripping", "slow drainage", "dustbin lid broken",
    "tree pruning", "branch pruning", "grass cutting", "garden maintenance",
    "inquiry", "procedure query", "information", "guidelines", "status check",
    "timing", "schedule", "birth certificate", "property tax", "tax receipt",
    "suggestion", "feedback", "routine inspection",
    # Marathi (Minor / Informational)
    "साधा खड्डा", "लहान खड्डा", "बारीक तडे", "किरकोळ गळती", "झाडांच्या फांद्या छाटणी",
    "चौकशी", "माहिती हवी", "सूचना", "विचारणा", "वेळापत्रक", "दाखला", "सवलत", "विनंती"
]


# -------------------------------------------------------------------------
# Linguistic Filter Regex Patterns (Negation, Modals, Temporal, Modifiers)
# -------------------------------------------------------------------------

# Negation prefixes within 1-3 words before or after a target keyword
NEGATION_EN_PATTERN = re.compile(
    r"\b(no|not|never|without|hardly|neither|nor|zero|nil)\b(?:\s+\w+){0,3}\s+"
    r"\b(accident|accidents|danger|dangerous|emergency|hazard|injuries|injury|fire|blast|collapse|burst|blocked)\b",
    re.IGNORECASE
)
REVERSED_NEGATION_EN_PATTERN = re.compile(
    r"\b(accident|accidents|danger|dangerous|emergency|hazard|injuries|injury|fire|blast|collapse|burst|blocked)\b\s+"
    r"\b(was avoided|is not|are not|were not|is absent|did not happen)\b",
    re.IGNORECASE
)

# Marathi negation
NEGATION_MR_PATTERN = re.compile(
    r"(अपघात|धोका|आपत्कालीन|इजा|आग|स्फोट)\s*(नाही|नव्हती|नव्हता|नसून|नका|झालेला नाही|झालेली नाही)",
    re.UNICODE
)

# Hypothetical, conditional, or preventive phrasing
HYPOTHETICAL_PATTERN = re.compile(
    r"\b(might|could|may|would|can cause|could cause|might cause|prevent|preventing|avoid|avoiding|"
    r"risk of|chance of|possibility of|before someone|so that no)\b(?:\s+\w+){0,3}\s+"
    r"\b(accident|accidents|injury|fatal|damage|hazard|collapse)\b",
    re.IGNORECASE
)
HYPOTHETICAL_MR_PATTERN = re.compile(
    r"(अपघात|धोका|इजा)\s*(होऊ शकतो|होऊ नये|टाळण्यासाठी|शक्यता आहे|संभवतो|होण्याची शक्यता)",
    re.UNICODE
)

# Historical / resolved incidents
HISTORICAL_PATTERN = re.compile(
    r"\b(last year|last month|years ago|months ago|in 20\d\d|yesterday it was|previously occurred|"
    r"already cleared|already resolved|fixed earlier)\b",
    re.IGNORECASE
)
HISTORICAL_MR_PATTERN = re.compile(
    r"(गेल्या वर्षी|गेल्या महिन्यात|पूर्वी झाला होता|आधी झालेला|नुकताच दुरुस्त झाला)",
    re.UNICODE
)

# Downscaling / minor qualifiers
MINOR_QUALIFIERS_PATTERN = re.compile(
    r"\b(minor|small|slight|tiny|little|trivial|cosmetic|negligible|hairline|just a|only a|harmless)\b",
    re.IGNORECASE
)
MINOR_QUALIFIERS_MR_PATTERN = re.compile(
    r"(किरकोळ|लहान|साधा|थोडा|फार नाही|काही विशेष नाही|साधारण)",
    re.UNICODE
)

# Escalation qualifiers (severe, acute, catastrophic)
SEVERE_QUALIFIERS_PATTERN = re.compile(
    r"\b(major|severe|massive|extreme|fatal|disastrous|catastrophic|deep|huge|completely|urgently)\b",
    re.IGNORECASE
)
SEVERE_QUALIFIERS_MR_PATTERN = re.compile(
    r"(गंभीर|मोठा|जीवघेणा|प्रचंड|भयंकर|तातडीने|पूर्णपणे)",
    re.UNICODE
)


# -------------------------------------------------------------------------
# Dataclasses & Result Models
# -------------------------------------------------------------------------

@dataclass
class PriorityResult:
    priority: str
    priority_score: float
    detected_keywords: List[str] = field(default_factory=list)
    priority_reason: str = ""
    confidence: float = 0.85
    uncertainty_indicators: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    escalation_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority": self.priority,
            "priority_score": self.priority_score,
            "detected_keywords": self.detected_keywords,
            "priority_reason": self.priority_reason,
            "confidence": self.confidence,
            "uncertainty_indicators": self.uncertainty_indicators,
            "evidence_sources": self.evidence_sources,
            "escalation_reasons": self.escalation_reasons,
        }


# -------------------------------------------------------------------------
# Context Extractor Helpers
# -------------------------------------------------------------------------

def _has_negation(text: str, trigger: str) -> bool:
    """Checks whether a hazardous trigger word is negated in context."""
    if NEGATION_EN_PATTERN.search(text) or REVERSED_NEGATION_EN_PATTERN.search(text):
        return True
    if NEGATION_MR_PATTERN.search(text):
        return True
    # Word-specific boundary negation
    trig_clean = re.escape(trigger.lower())
    specific_pattern = rf"\b(no|not|without|never|नाही|नव्हते)\s+(?:\w+\s+)?{trig_clean}\b"
    if re.search(specific_pattern, text, re.IGNORECASE):
        return True
    return False


def _has_hypothetical(text: str) -> bool:
    """Checks whether emergency words are framed hypothetically or preventively."""
    return bool(HYPOTHETICAL_PATTERN.search(text) or HYPOTHETICAL_MR_PATTERN.search(text))


def _has_historical(text: str) -> bool:
    """Checks whether an incident reference is purely historical."""
    return bool(HISTORICAL_PATTERN.search(text) or HISTORICAL_MR_PATTERN.search(text))


def _has_minor_qualifier(text: str) -> bool:
    """Checks if the description specifically qualifies the issue as small/minor/cosmetic."""
    return bool(MINOR_QUALIFIERS_PATTERN.search(text) or MINOR_QUALIFIERS_MR_PATTERN.search(text))


def _has_severe_qualifier(text: str) -> bool:
    """Checks if the description uses explicit severe/massive escalation terms."""
    return bool(SEVERE_QUALIFIERS_PATTERN.search(text) or SEVERE_QUALIFIERS_MR_PATTERN.search(text))


# -------------------------------------------------------------------------
# Core Severity Assessment Engine
# -------------------------------------------------------------------------

def detect_priority(
    input_data: Any,
    visual_priority: Optional[str] = None,
    visual_evidence: Optional[Dict[str, Any]] = None,
    audio_evidence: Optional[Dict[str, Any]] = None,
    citizen_text: Optional[str] = None,
) -> PriorityResult:
    """
    Computes an explainable municipal severity assessment:
    - CRITICAL: Credible immediate life-threat or hazardous emergency.
    - HIGH: Substantial municipal disruption or serious infrastructure hazard.
    - MEDIUM: Standard civic problem requiring timely municipal intervention.
    - LOW: Minor, routine, cosmetic, or procedural matter.
    - REVIEW REQUIRED: Insufficient, conflicting, or highly ambiguous evidence.
    """
    if isinstance(input_data, str):
        nlp_result = preprocess_complaint(input_data)
        raw_text = input_data
    elif hasattr(input_data, "normalized_text"):
        nlp_result = input_data
        raw_text = input_data.normalized_text
    else:
        raw_text = str(input_data or "")
        nlp_result = preprocess_complaint(raw_text)

    lower_text = nlp_result.normalized_text.lower()
    token_set = nlp_result.token_set | nlp_result.lemmatized_set

    # Also inspect explicit citizen text if provided separately
    if citizen_text and citizen_text.strip():
        lower_citizen = citizen_text.strip().lower()
    else:
        lower_citizen = lower_text

    uncertainty_indicators: List[str] = []
    evidence_sources: List[str] = ["text"]
    escalation_reasons: List[str] = []

    # 1. Inspect visual evidence parameters
    vis_meta = visual_evidence or {}
    vis_damage = vis_meta.get("apparent_damage", "").lower()
    vis_hazards = vis_meta.get("hazard_markers", []) or vis_meta.get("visible_hazards", [])
    vis_uncertainty = vis_meta.get("uncertainty_indicators", [])
    if vis_uncertainty:
        uncertainty_indicators.extend(vis_uncertainty)
    if visual_evidence:
        evidence_sources.append("visual")

    # 2. Inspect audio evidence parameters
    aud_meta = audio_evidence or {}
    if audio_evidence:
        evidence_sources.append("audio")
    aud_hazards = aud_meta.get("hazard_keywords", [])

    # Check for visual vs text contradiction
    # e.g., image shows completely clean / no damage, but user reports extreme catastrophe
    has_visual_contradiction = False
    if vis_damage in ["none", "clean"] and _has_severe_qualifier(lower_citizen):
        has_visual_contradiction = True
        uncertainty_indicators.append("visual_evidence_shows_no_damage_contrasting_with_reported_claim")

    # Check for empty / insufficient information
    meaningful_words = [t for t in nlp_result.tokens if len(t) > 2 and not t.isdigit()]
    is_extremely_vague = len(meaningful_words) < 3 and not vis_hazards and not aud_hazards

    if is_extremely_vague:
        uncertainty_indicators.append("insufficient_descriptive_details")
        return PriorityResult(
            priority=ComplaintPriority.REVIEW_REQUIRED.value,
            priority_score=0.40,
            detected_keywords=meaningful_words,
            priority_reason="Insufficient details provided to verify incident severity. Flagged for manual review.",
            confidence=0.35,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    if has_visual_contradiction:
        return PriorityResult(
            priority=ComplaintPriority.REVIEW_REQUIRED.value,
            priority_score=0.45,
            detected_keywords=["conflicting_visual_observation"],
            priority_reason=(
                "Contradiction detected: Citizen report mentions severe disruption, but attached photograph "
                "shows no evident physical damage or hazard. Assigned Review Required for field verification."
            ),
            confidence=0.40,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=["contradictory_multimodal_evidence"],
        )

    # -------------------------------------------------------------------------
    # Context-Aware Trigger Analysis
    # -------------------------------------------------------------------------
    is_negated = False
    is_hypothetical = _has_hypothetical(lower_citizen)
    is_historical = _has_historical(lower_citizen)
    is_minor = _has_minor_qualifier(lower_citizen)
    is_severe = _has_severe_qualifier(lower_citizen)

    if NEGATION_EN_PATTERN.search(lower_citizen) or NEGATION_MR_PATTERN.search(lower_citizen):
        uncertainty_indicators.append("negated_emergency_statement")
    if is_hypothetical:
        uncertainty_indicators.append("hypothetical_preventive_statement")
    if is_historical:
        uncertainty_indicators.append("historical_incident_statement")

    # Match Critical triggers
    matched_critical = []
    for trigger in CRITICAL_EMERGENCY_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_citizen or trigger_clean in token_set:
            if _has_negation(lower_citizen, trigger_clean):
                is_negated = True
                uncertainty_indicators.append(f"negated_critical_trigger:{trigger_clean}")
                continue
            if is_hypothetical:
                uncertainty_indicators.append(f"hypothetical_preventive_mention:{trigger_clean}")
                continue
            if is_historical:
                uncertainty_indicators.append(f"historical_incident_mention:{trigger_clean}")
                continue
            matched_critical.append(trigger)

    # Match High triggers
    matched_high = []
    for trigger in HIGH_SEVERITY_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_citizen or trigger_clean in token_set:
            if _has_negation(lower_citizen, trigger_clean):
                is_negated = True
                uncertainty_indicators.append(f"negated_high_trigger:{trigger_clean}")
                continue
            if is_minor:
                uncertainty_indicators.append(f"minor_qualified_high_trigger:{trigger_clean}")
                continue
            matched_high.append(trigger)

    # Match Medium triggers
    matched_medium = []
    for trigger in MEDIUM_SEVERITY_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_citizen or trigger_clean in token_set:
            matched_medium.append(trigger)

    # Match Low triggers
    matched_low = []
    for trigger in LOW_SEVERITY_TRIGGERS:
        trigger_clean = trigger.lower()
        if trigger_clean in lower_citizen or trigger_clean in token_set:
            matched_low.append(trigger)

    # Deduplicate matches
    matched_critical = list(dict.fromkeys(matched_critical))
    matched_high = list(dict.fromkeys(matched_high))
    matched_medium = list(dict.fromkeys(matched_medium))
    matched_low = list(dict.fromkeys(matched_low))

    # Evaluate explicit visual priority argument if provided
    v_p = (visual_priority or vis_meta.get("visual_priority") or "").strip().capitalize()

    # -------------------------------------------------------------------------
    # DECISION RULE 1: CRITICAL SEVERITY
    # Unambiguous, active, non-negated life-threatening emergency
    # -------------------------------------------------------------------------
    if matched_critical:
        # Check if corroborated by visual or explicitly detailed
        escalation_reasons.append("credible_life_threat_detected")
        reason = (
            f"Immediate life hazard detected from verified evidence ({', '.join(repr(k) for k in matched_critical[:3])}). "
            f"Requires emergency municipal intervention."
        )
        if v_p == "Critical":
            escalation_reasons.append("visual_inspection_corroborated_critical_hazard")
            reason += " Corroborated by on-site photographic inspection."

        return PriorityResult(
            priority=ComplaintPriority.CRITICAL.value,
            priority_score=1.0,
            detected_keywords=matched_critical,
            priority_reason=reason,
            confidence=0.95,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=escalation_reasons,
        )

    # If visual inspection independently observed an acute live electrical/fire hazard
    if v_p == "Critical" and any("spark" in str(h).lower() or "fire" in str(h).lower() or "wire" in str(h).lower() for h in vis_hazards):
        escalation_reasons.append("visual_high_intensity_hazard_detected")
        return PriorityResult(
            priority=ComplaintPriority.CRITICAL.value,
            priority_score=1.0,
            detected_keywords=["visual_spark_or_flame_hazard"],
            priority_reason="Active electrical / fire hazard identified on-site through physical visual inspection.",
            confidence=0.90,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=escalation_reasons,
        )

    # -------------------------------------------------------------------------
    # DECISION RULE 2: HIGH SEVERITY
    # Severe municipal disruption, road blockage, major burst, dangerous obstacle
    # -------------------------------------------------------------------------
    if matched_high and not (is_minor and not is_severe):
        escalation_reasons.append("substantial_municipal_disruption")
        reason = (
            f"Substantial municipal disruption or safety hazard identified ({', '.join(repr(k) for k in matched_high[:3])}). "
            f"Requires urgent departmental deployment."
        )
        if v_p in ["High", "Critical"]:
            reason += " Supported by visible damage in attached photograph."

        return PriorityResult(
            priority=ComplaintPriority.HIGH.value,
            priority_score=0.75,
            detected_keywords=matched_high,
            priority_reason=reason,
            confidence=0.88,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=escalation_reasons,
        )

    # Severe qualifier applied to a standard medium problem (e.g. "major water leak", "severe traffic jam")
    if is_severe and matched_medium and not (is_minor and not is_severe):
        escalation_reasons.append("severity_intensifier_applied_to_civic_issue")
        return PriorityResult(
            priority=ComplaintPriority.HIGH.value,
            priority_score=0.75,
            detected_keywords=matched_medium + ["severe_intensity_qualifier"],
            priority_reason=(
                f"Elevated to High urgency: Citizen reports severe intensity regarding {matched_medium[0]} "
                f"with high potential public disruption."
            ),
            confidence=0.82,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=escalation_reasons,
        )

    # -------------------------------------------------------------------------
    # DECISION RULE 3: LOW SEVERITY
    # Explicitly minor, cosmetic, inquiry, or small pothole/leak
    # -------------------------------------------------------------------------
    # Substantial water leak or pothole qualified as small/minor
    if is_minor and not is_severe:
        keyword_context = matched_low or matched_medium or ["minor_issue"]
        return PriorityResult(
            priority=ComplaintPriority.LOW.value,
            priority_score=0.25,
            detected_keywords=keyword_context,
            priority_reason=(
                f"Classified as Low severity: Evidence explicitly indicates a minor, localized, or cosmetic issue "
                f"({', '.join(repr(k) for k in keyword_context[:2])}) without immediate hazard."
            ),
            confidence=0.90,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    if matched_low and not matched_medium:
        return PriorityResult(
            priority=ComplaintPriority.LOW.value,
            priority_score=0.25,
            detected_keywords=matched_low,
            priority_reason=(
                f"Routine municipal matter or inquiry ({', '.join(repr(k) for k in matched_low[:2])}). "
                f"Scheduled for standard administrative attention."
            ),
            confidence=0.92,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    # Small pothole with no immediate hazard
    if any("small" in lower_citizen or "minor" in lower_citizen for _ in [1]) and "pothole" in lower_citizen:
        return PriorityResult(
            priority=ComplaintPriority.LOW.value,
            priority_score=0.25,
            detected_keywords=["small pothole"],
            priority_reason="Small pothole identified without active hazard to vehicular or pedestrian traffic.",
            confidence=0.88,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    # -------------------------------------------------------------------------
    # VAGUE EMERGENCY DETECTION: Emergency keyword without actionable detail
    # -------------------------------------------------------------------------
    vague_emergency_words = ["accident", "emergency", "danger", "hazard", "apghat", "durghatna", "अपघात"]
    has_vague_emergency = any(w in lower_citizen for w in vague_emergency_words)
    if (
        has_vague_emergency
        and not is_hypothetical
        and not is_historical
        and not is_negated
        and not matched_critical
        and not matched_high
        and not matched_medium
        and not matched_low
    ):
        uncertainty_indicators.append("vague_emergency_or_insufficient_evidence")
        return PriorityResult(
            priority=ComplaintPriority.REVIEW_REQUIRED.value,
            priority_score=0.45,
            detected_keywords=[w for w in vague_emergency_words if w in lower_citizen],
            priority_reason="Vague mention of accident or emergency without sufficient operational details. Flagged for review.",
            confidence=0.40,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    # -------------------------------------------------------------------------
    # DECISION RULE 4: MEDIUM SEVERITY (Standard Baseline)
    # Significant non-emergency civic grievance (pothole, water leak, dustbin)
    # -------------------------------------------------------------------------
    if matched_medium:
        return PriorityResult(
            priority=ComplaintPriority.MEDIUM.value,
            priority_score=0.50,
            detected_keywords=matched_medium,
            priority_reason=(
                f"Standard non-emergency municipal grievance regarding {matched_medium[0]}. "
                f"Assigned for timely departmental inspection."
            ),
            confidence=0.85,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    # If hypothetical emergency keyword was used in preventive context
    if is_hypothetical:
        return PriorityResult(
            priority=ComplaintPriority.MEDIUM.value,
            priority_score=0.50,
            detected_keywords=["preventive_maintenance_request"],
            priority_reason="Preventive civic maintenance request to avoid potential hazards. Evaluated at standard Medium priority.",
            confidence=0.80,
            uncertainty_indicators=uncertainty_indicators,
            evidence_sources=evidence_sources,
            escalation_reasons=[],
        )

    # Default baseline for typical citizen submission
    return PriorityResult(
        priority=ComplaintPriority.MEDIUM.value,
        priority_score=0.50,
        detected_keywords=[],
        priority_reason="Standard municipal grievance without immediate life hazard or major disruption indicators.",
        confidence=0.75,
        uncertainty_indicators=uncertainty_indicators,
        evidence_sources=evidence_sources,
        escalation_reasons=[],
    )
