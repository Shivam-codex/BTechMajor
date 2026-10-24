"""
Conversational Municipal Assistant Intent Recognition and Query Expansion Engine.
Emulates modern e-commerce/civic customer support chatbots (Flipkart, Amazon, Swiggy).
Identifies citizen intentions (lodge grievance, track complaint, emergency, greeting, SLA, escalation),
detects municipal categories, expands lexical retrieval queries, and builds interactive action cards.
"""

import re
from typing import Dict, Any, List, Optional
from backend.app.utils.constants import ComplaintCategory, DepartmentName

# Keyword mapping for municipal domain query expansion
SYNONYM_EXPANSION = {
    "electricity": "electricity electrical electric power supply transformer wire voltage blackout outage fuse spark 1912",
    "electric": "electricity electrical electric power supply transformer wire voltage blackout outage 1912",
    "power": "electricity electrical electric power supply transformer wire voltage blackout outage 1912",
    "current": "electricity electrical electric power supply transformer wire voltage 1912",
    "transformer": "electricity electrical transformer sparking blast smoke explosion oil leak 1912",
    "voltage": "electricity electrical voltage surge fluctuation neutral low voltage 1912",
    "wire": "electricity electrical wire hanging dangling overhead conductor live wire shock hazard 1912",
    "water": "water supply pipeline burst leak drinking water contamination contaminated dirty tap pressure shortage tanker",
    "pipeline": "water pipeline burst leak distribution main supply repair 1800-233-0001",
    "leakage": "water leakage pipeline burst overflow road flooding",
    "pothole": "road pothole crater asphalt tar damage surface pavement footpath ditch excavation",
    "road": "road pothole crater asphalt tar damage surface pavement footpath ditch excavation",
    "tar": "road pothole tar asphalt repair road infrastructure",
    "garbage": "garbage waste trash refuse dustbin dumping litter debris sweeping collection dumper bin overflow",
    "waste": "garbage waste sanitation collection solid waste segregating dumping bin",
    "trash": "garbage waste trash sanitation collection solid waste dumping",
    "cleanliness": "garbage sanitation cleanliness sweeping hygiene municipal",
    "street light": "street light lamp pole darkness flickering dark night lighting illumination electrical",
    "streetlight": "street light lamp pole darkness flickering dark night lighting illumination",
    "lamp": "street light lamp pole fixture bulb darkness",
    "drainage": "drainage sewerage sewer gutter manhole open drain overflow wastewater clog blockage stormwater",
    "drain": "drainage sewerage sewer gutter manhole open drain overflow wastewater",
    "sewer": "drainage sewerage sewer gutter manhole open drain overflow wastewater",
    "sewage": "drainage sewerage sewer gutter manhole open drain overflow wastewater",
    "gutter": "drainage sewerage sewer gutter manhole open drain overflow wastewater",
    "manhole": "drainage sewerage sewer gutter manhole open drain cover broken fallen hazardous",
    "toilet": "public toilet restroom washroom urinal community toilet hygiene cleanliness sanitation flush",
    "washroom": "public toilet restroom washroom urinal community toilet hygiene",
    "urinal": "public toilet restroom washroom urinal community toilet hygiene",
    "traffic": "traffic signal jam congestion light intersection junction parking illegal speed breaker divider",
    "signal": "traffic signal light red light blinker malfunction intersection",
    "parking": "traffic illegal parking encroachment road obstruction towing",
    # Marathi Keywords
    "वीज": "electricity electrical power supply वीज महावितरण खंडित",
    "विद्युत": "electricity electrical power supply विद्युत",
    "पाणी": "water supply pipeline drinking पाणी पुरवठा गळती",
    "पाईप": "water pipeline burst पाईप गळती",
    "कचरा": "garbage waste sanitation कचरा पेटी घाण",
    "स्वच्छता": "garbage sanitation cleanliness स्वच्छता",
    "रस्ता": "road pothole asphalt रस्ता डांबर खड्डा",
    "खड्डा": "road pothole खड्डा रस्ता",
    "दिवा": "street light lamp pole दिवा पथदिवा",
    "पथदिवा": "street light lamp pole पथदिवा बंद",
    "गटार": "drainage sewerage gutter गटार सांडपाणी तुंबणे",
    "ड्रेनेज": "drainage sewerage ड्रेनेज",
    "शौचालय": "public toilet washroom शौचालय स्वच्छता",
    "वाहतूक": "traffic signal jam वाहतूक कोंडी सिग्नल",
}

GREETING_PATTERNS = [
    r"^(hi|hello|hey|hola|greetings|good\s*(morning|afternoon|evening)|namaste|namaskar|नमस्कार|प्रणाम)\b",
    r"^(who\s+are\s+you|what\s+can\s+you\s+do|help\s+me|help)\b",
]

TRACK_PATTERNS = [
    r"\b(track|status|check|progress|where\s+is|what\s+happened\s+to)\b.*\b(complaint|grievance|ticket|issue|request)\b",
    r"\b(cmp-\d{4}-[a-z0-9]+)\b",
    r"\bstatus\s+of\b",
]

LODGE_PATTERNS = [
    r"\b(want\s+to|how\s+to|need\s+to|wish\s+to|can\s+i)\s+(raise|file|lodge|register|submit|report|complain|create)\b",
    r"\b(raise|file|lodge|register|submit|report)\s+(a\s+)?(complaint|grievance|issue|problem|case)\b",
    r"\b(i\s+have\s+an?\s+issue|facing\s+(an?\s+)?issue|problem\s+with)\b",
]

EMERGENCY_KEYWORDS = [
    "spark", "sparking", "shock", "fire", "live wire", "burst", "explosion",
    "gas leak", "cave in", "drowning", "open manhole", "urgent", "emergency", "danger", "आग", "शॉक"
]


def detect_user_intent(query: str) -> Dict[str, Any]:
    """
    Classifies user inquiry into conversational intents:
    - GREETING
    - LODGE_GRIEVANCE
    - TRACK_STATUS
    - EMERGENCY
    - PROCEDURAL_QUERY
    - OUT_OF_DOMAIN
    """
    q_lower = (query or "").lower().strip()

    # 1. Check for Out of Domain (e.g. poetry, recipes, movies)
    out_of_domain_words = ["poem", "poetry", "song", "recipe", "movie", "weather in tokyo", "joke", "story", "cricket score"]
    if any(re.search(rf"\b{re.escape(w)}\b", q_lower) for w in out_of_domain_words):
        return {
            "intent": "OUT_OF_DOMAIN",
            "category": None,
            "department": None,
            "tracking_id": None,
            "is_emergency": False,
            "suggested_actions": [],
            "quick_replies": [],
        }

    # 2. Check for Complaint Tracking ID (e.g. CMP-2026-XXXXX)
    cmp_match = re.search(r"cmp-\d{4}-[a-z0-9]+", q_lower)
    if cmp_match:
        tracking_id = cmp_match.group(0).upper()
        return {
            "intent": "TRACK_STATUS",
            "category": None,
            "department": None,
            "tracking_id": tracking_id,
            "is_emergency": False,
            "suggested_actions": [
                {
                    "label": f"🔍 View Details for {tracking_id}",
                    "action_type": "link",
                    "url": f"/complaints/{tracking_id}",
                    "icon": "search",
                },
                {
                    "label": "📋 View All My Grievances",
                    "action_type": "link",
                    "url": "/complaints/my",
                    "icon": "list",
                },
            ],
            "quick_replies": [
                f"What is the status of {tracking_id}?",
                "How do I escalate this grievance?",
                "Who is the officer in charge?",
            ],
        }

    # 3. Check for Greetings / Smalltalk
    for pat in GREETING_PATTERNS:
        if re.search(pat, q_lower):
            return {
                "intent": "GREETING",
                "category": None,
                "department": None,
                "tracking_id": None,
                "is_emergency": False,
                "suggested_actions": [
                    {
                        "label": "📝 Lodge a New Grievance",
                        "action_type": "link",
                        "url": "/complaints",
                        "icon": "file-plus",
                    },
                    {
                        "label": "🔍 Track Existing Complaint",
                        "action_type": "link",
                        "url": "/complaints/my",
                        "icon": "search",
                    },
                    {
                        "label": "⚡ Report Electricity Issue",
                        "action_type": "link",
                        "url": "/complaints?category=Electricity&text=Power+or+electricity+issue",
                        "icon": "zap",
                    },
                    {
                        "label": "💧 Report Water Leakage",
                        "action_type": "link",
                        "url": "/complaints?category=Water+Supply&text=Water+leakage+or+supply+issue",
                        "icon": "droplet",
                    },
                ],
                "quick_replies": [
                    "How do I report a pothole?",
                    "What is the turnaround time for a water burst?",
                    "How to report an electrical wire hazard?",
                ],
            }

    # 4. Check for Track Status Intent (without explicit ID)
    for pat in TRACK_PATTERNS:
        if re.search(pat, q_lower):
            return {
                "intent": "TRACK_STATUS",
                "category": None,
                "department": None,
                "tracking_id": None,
                "is_emergency": False,
                "suggested_actions": [
                    {
                        "label": "📋 Open My Complaints Tracker",
                        "action_type": "link",
                        "url": "/complaints/my",
                        "icon": "list",
                    },
                    {
                        "label": "📝 Submit New Grievance",
                        "action_type": "link",
                        "url": "/complaints",
                        "icon": "file-plus",
                    },
                ],
                "quick_replies": [
                    "How do I find my Tracking ID?",
                    "What does 'In Progress' status mean?",
                    "How many days until resolution?",
                ],
            }

    # 5. Detect Municipal Category
    detected_cat: Optional[str] = None
    detected_dept: Optional[str] = None

    if any(k in q_lower for k in ["electri", "power", "transformer", "voltage", "current", "wire", "वीज", "विद्युत"]):
        detected_cat = ComplaintCategory.ELECTRICITY.value
        detected_dept = DepartmentName.ELECTRICAL.value
    elif any(k in q_lower for k in ["water", "pipeline", "tap", "drinking water", "पाणी", "गळती"]):
        detected_cat = ComplaintCategory.WATER_SUPPLY.value
        detected_dept = DepartmentName.WATER_SUPPLY.value
    elif any(k in q_lower for k in ["pothole", "road", "asphalt", "crater", "footpath", "रस्ता", "खड्डा"]) or re.search(r"\btar\b", q_lower):
        detected_cat = ComplaintCategory.ROAD_POTHOLE.value
        detected_dept = DepartmentName.ROADS_INFRASTRUCTURE.value
    elif any(k in q_lower for k in ["garbage", "waste", "trash", "dustbin", "cleanliness", "dumping", "sweeping", "कचरा", "स्वच्छता"]):
        detected_cat = ComplaintCategory.GARBAGE_WASTE.value
        detected_dept = DepartmentName.SANITATION.value
    elif any(k in q_lower for k in ["street light", "streetlight", "lamp", "pole", "darkness", "दिवे", "पथदिवा"]):
        detected_cat = ComplaintCategory.STREET_LIGHT.value
        detected_dept = DepartmentName.ELECTRICAL.value
    elif any(k in q_lower for k in ["drainage", "sewer", "gutter", "manhole", "overflow", "गटार", "ड्रेनेज"]):
        detected_cat = ComplaintCategory.DRAINAGE_SEWERAGE.value
        detected_dept = DepartmentName.DRAINAGE.value
    elif any(k in q_lower for k in ["toilet", "washroom", "urinal", "restroom", "शौचालय"]):
        detected_cat = ComplaintCategory.PUBLIC_TOILET.value
        detected_dept = DepartmentName.PUBLIC_HEALTH.value
    elif any(k in q_lower for k in ["traffic", "signal", "jam", "parking", "वाहतूक", "सिग्नल"]):
        detected_cat = ComplaintCategory.TRAFFIC.value
        detected_dept = DepartmentName.TRAFFIC.value

    # 5. Check Emergency
    is_emergency = any(k in q_lower for k in EMERGENCY_KEYWORDS)

    # 6. Check Lodge Intent
    is_lodge = any(re.search(pat, q_lower) for pat in LODGE_PATTERNS)

    if is_lodge or detected_cat:
        intent = "LODGE_GRIEVANCE" if is_lodge else "PROCEDURAL_QUERY"

        cat_param = detected_cat.replace(" ", "+") if detected_cat else "General"
        actions = [
            {
                "label": f"⚡ Submit {detected_cat or 'Civic'} Grievance Now",
                "action_type": "link",
                "url": f"/complaints?category={cat_param}&text={cat_param}+issue+in+my+locality",
                "icon": "send",
            },
            {
                "label": "📋 Track Filed Complaints",
                "action_type": "link",
                "url": "/complaints/my",
                "icon": "list",
            },
        ]

        if detected_cat == ComplaintCategory.ELECTRICITY.value:
            actions.append({
                "label": "📞 Call 24/7 Power Squad (1912)",
                "action_type": "tel",
                "url": "tel:1912",
                "icon": "phone-call",
            })
        else:
            actions.append({
                "label": "📞 Municipal Helpline (1800-233-0001)",
                "action_type": "tel",
                "url": "tel:18002330001",
                "icon": "phone-call",
            })

        replies = [
            f"What is the resolution timeline for {detected_cat or 'this issue'}?",
            f"Who is the officer in charge of {detected_dept or 'this department'}?",
            "Can I upload photos with my complaint?",
        ]

        return {
            "intent": intent,
            "category": detected_cat,
            "department": detected_dept,
            "tracking_id": None,
            "is_emergency": is_emergency,
            "suggested_actions": actions,
            "quick_replies": replies,
        }

    # 7. Check for general out-of-domain queries (e.g. poetry, recipes, movies)
    out_of_domain_words = ["poem", "poetry", "song", "recipe", "movie", "weather in tokyo", "joke", "story", "cricket score"]
    if any(w in q_lower for w in out_of_domain_words):
        return {
            "intent": "OUT_OF_DOMAIN",
            "category": None,
            "department": None,
            "tracking_id": None,
            "is_emergency": False,
            "suggested_actions": [
                {
                    "label": "📝 View Municipal Grievance Services",
                    "action_type": "link",
                    "url": "/complaints",
                    "icon": "file-text",
                },
                {
                    "label": "🏛️ Browse Municipal Knowledge Base",
                    "action_type": "link",
                    "url": "/knowledge-base",
                    "icon": "book-open",
                },
            ],
            "quick_replies": [
                "How do I report a pothole on my street?",
                "How do I file an electricity complaint?",
                "What is the water pipeline repair SLA?",
            ],
        }

    # Default procedural query
    return {
        "intent": "PROCEDURAL_QUERY",
        "category": detected_cat,
        "department": detected_dept,
        "tracking_id": None,
        "is_emergency": is_emergency,
        "suggested_actions": [
            {
                "label": "📝 File a Grievance",
                "action_type": "link",
                "url": "/complaints",
                "icon": "file-plus",
            },
            {
                "label": "📋 Track My Grievances",
                "action_type": "link",
                "url": "/complaints/my",
                "icon": "list",
            },
            {
                "label": "📞 Municipal Helpline (1800-233-0001)",
                "action_type": "tel",
                "url": "tel:18002330001",
                "icon": "phone",
            },
        ],
        "quick_replies": [
            "How do I report a pothole?",
            "How to file an electricity complaint?",
            "What is the water repair SLA?",
        ],
    }


def expand_retrieval_query(query: str) -> str:
    """
    Enriches user inquiry with domain synonyms and keyword expansions
    to maximize TF-IDF lexical recall without modifying the original question text.
    """
    clean_q = (query or "").lower().strip()
    expansions = []

    for word, syn in SYNONYM_EXPANSION.items():
        if word in clean_q:
            expansions.append(syn)

    if expansions:
        # Append expansions to broaden TF-IDF feature overlap
        return f"{query} {' '.join(expansions)}"
    return query
