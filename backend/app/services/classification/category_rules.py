"""
Configurable rule dictionary for deterministic complaint classification.
Contains curated multi-lingual lexical patterns for English, Marathi (Devanagari),
and code-mixed / transliterated expressions across all 9 municipal categories.
"""

from typing import Dict, List, Any
from backend.app.utils.constants import ComplaintCategory

CATEGORY_RULES: Dict[str, Dict[str, Any]] = {
    ComplaintCategory.WATER_SUPPLY.value: {
        "primary_keywords": [
            # English
            "water", "supply", "leakage", "leak", "pipe", "pipeline", "tap",
            "pressure", "drinking", "contamination", "turbid", "borewell", "tanker",
            # Marathi
            "पाणी", "पानी", "पुरवठा", "नळ", "गळती", "पाईप", "पाईपलाईन", "जल",
            "पिण्याचे", "दाब", "बोरवेल", "टँकर", "जलकुंभ", "तोटी",
            # Transliteration
            "paani", "pani", "nal", "galati", "panyacha", "purvatha",
        ],
        "exact_phrases": [
            "no water", "water not coming", "low water pressure", "water leakage",
            "drinking water", "dirty water", "pipe burst", "pipe leaking", "pipeline damage",
            "contaminated water", "irregular water supply", "water contamination", "no drinking water",
            "पाणी येत नाही", "कमी दाबाने पाणी", "पिण्याचे पाणी दूषित", "पाईप फुटला",
            "पाणी पुरवठा बंद", "गळती सुरू आहे", "पिण्याचे पाणी नाही", "गढूळ पाणी",
            "नळाला पाणी नाही", "पाईपलाईन गळती", "paani yet nahi", "water problem",
        ],
        "synonyms": [
            "reservoir", "valve", "aqueduct", "booster", "wharf", "motor",
            "व्हॉल्व्ह", "जलवाहिनी", "पंप", "मोटार", "टाकी",
        ],
        "context_keywords": [
            "yellow", "smell", "morning", "timing", "hours", "days", "muddy",
            "सकाळ", "दुर्गंध", "पिवळे", "अनियमित", "वेळ",
        ],
        "negative_keywords": [
            "drainage water", "gutter water", "sewage", "toilet", "सांडपाणी", "गटाराचे पाणी",
        ],
    },

    ComplaintCategory.GARBAGE_WASTE.value: {
        "primary_keywords": [
            # English
            "garbage", "waste", "trash", "rubbish", "refuse", "debris", "bin",
            "dustbin", "dumping", "collection", "pickup", "litter", "littering",
            # Marathi
            "कचरा", "कचराकुंडी", "घाण", "टाकाऊ", "ढीग", "संकलन", "स्वच्छता",
            "घंटागाडी", "झाडू", "सफाई",
            # Transliteration
            "kachra", "ghangadi", "safai", "dustbin",
        ],
        "exact_phrases": [
            "garbage collection", "overflowing dustbin", "waste dumping", "garbage pile",
            "garbage vehicle not coming", "uncleaned garbage", "garbage accumulation",
            "open dumping", "stinking garbage", "no garbage pickup",
            "कचरा उचलला नाही", "कचऱ्याचे ढीग", "कचरा गाडी आली नाही", "कचराकुंडी भरली",
            "रस्त्यावर कचरा", "कचरा साचला आहे", "कचरा संकलन बंद", "दुर्गंधी पसरली",
            "kachra uchalla nahi", "kachra gadi",
        ],
        "synonyms": [
            "muck", "scrap", "disposal", "sweeper", "scraps", "rotting",
            "घंटा गाडी", "सफाई कामगार", "कचरापेटी",
        ],
        "context_keywords": [
            "smell", "foul", "stink", "flies", "dogs", "animals", "hygiene",
            "दुर्गंधी", "माशा", "रोगराई", "कुत्रे", "उंदीर",
        ],
        "negative_keywords": [
            "toilet waste", "drainage choke",
        ],
    },

    ComplaintCategory.ROAD_POTHOLE.value: {
        "primary_keywords": [
            # English
            "road", "pothole", "potholes", "asphalt", "tar", "pavement", "footpath",
            "divider", "crater", "speed breaker", "bump", "uneven", "gravel", "sidewalk",
            # Marathi
            "रस्ता", "रस्ते", "खड्डा", "खड्डे", "डांबरीकरण", "पदपथ", "फुटपाथ",
            "दुभाजक", "गतिरोधक", "खडी", "रस्त्याची",
            # Transliteration
            "rasta", "raste", "khadda", "khadde", "footpath",
        ],
        "exact_phrases": [
            "damaged road", "broken road", "deep pothole", "potholes on road", "road repair",
            "speed breaker needed", "uneven road", "crater on road", "tar road broken",
            "pothole repair", "footpath broken", "bad road condition",
            "खड्डा पडला", "रस्ता खराब", "रस्त्याची दुर्दशा", "खड्ड्यांची दुरुस्ती",
            "रस्त्यावर खड्डे", "डांबरीकरण करावे", "गतिरोधक बसवा", "मोठा खड्डा",
            "rasta kharab", "khadde padale", "road damage",
        ],
        "synonyms": [
            "lane", "alley", "street surface", "resurfacing", "patchwork",
            "गल्ली", "पॅचवर्क", "मुरुम",
        ],
        "context_keywords": [
            "accident", "bike slip", "vehicle damage", "two wheeler", "slip", "skid",
            "अपघात", "गाड्यांचे नुकसान", "निसरडा", "वाहतूक", "पडला",
        ],
        "negative_keywords": [
            "street light", "wire hanging",
        ],
    },

    ComplaintCategory.STREET_LIGHT.value: {
        "primary_keywords": [
            # English
            "street light", "streetlight", "street lamp", "pole", "bulb", "dark",
            "darkness", "lamp", "lamppost", "illumination",
            # Marathi
            "पथदिवा", "पथदिवे", "दिवा", "दिवे", "खांब", "पोल", "अंधार", "बल्ब", "लाईट",
            # Transliteration
            "pathdiwa", "diwa", "street light", "pole",
        ],
        "exact_phrases": [
            "street light not working", "street lights off", "dark street", "light pole broken",
            "flickering light", "no street light", "street light out", "street lamp broken",
            "dark road at night", "lights not functioning",
            "पथदिवे बंद आहेत", "पथदिवा लागत नाही", "रस्त्यावर अंधार", "पोलचा दिवा बंद",
            "विजेचा खांब वाकला", "पथदिवे सुरू करा", "दिवा बंद आहे",
            "street light band", "light lagat nahi",
        ],
        "synonyms": [
            "sodium lamp", "led street light", "lantern", "tube light", "luminaire",
            "एलईडी दिवा", "ट्यूबलाईट", "प्रकाश",
        ],
        "context_keywords": [
            "evening", "night", "crime", "safety", "theft", "women safety",
            "रात्री", "संध्याकाळी", "असुरक्षित", "चोरी", "भिती",
        ],
        "negative_keywords": [
            "traffic signal", "house electricity", "meter reading", "bill",
        ],
    },

    ComplaintCategory.DRAINAGE_SEWERAGE.value: {
        "primary_keywords": [
            # English
            "drainage", "drain", "drains", "sewer", "sewerage", "gutter", "gutters",
            "manhole", "sewage", "overflow", "backflow", "chamber", "nullah", "culvert",
            # Marathi
            "सांडपाणी", "गटार", "गटारे", "मॅनहोल", "नाला", "नाली", "चेंबर",
            "मलनिःसारण", "तुंबले", "गटारी",
            # Transliteration
            "gatar", "nullah", "drainage", "manhole", "chamber",
        ],
        "exact_phrases": [
            "drainage overflow", "blocked drain", "gutter overflowing", "sewage water",
            "open manhole", "broken manhole cover", "choked drainage", "sewer line blocked",
            "foul water overflowing", "nullah blocked", "drain clogged",
            "गटार तुंबले", "सांडपाणी रस्त्यावर", "मॅनहोल उघडे", "गटाराचे पाणी घरात",
            "नाला तुंबला", "दुर्गंधीयुक्त पाणी", "सांडपाणी वाहिनी चोक", "मॅनहोल तुटले",
            "gatar tumble", "drainage block",
        ],
        "synonyms": [
            "cesspool", "conduit", "sullage", "stormwater", "stench",
            "सांडपाणी वाहिनी", "नालिका",
        ],
        "context_keywords": [
            "mosquito", "breeding", "monsoon", "rain", "filth", "disease",
            "डास", "पावसाळा", "रोगराई", "दुर्गंधी",
        ],
        "negative_keywords": [
            "drinking water supply", "tap water", "water meter",
        ],
    },

    ComplaintCategory.PUBLIC_TOILET.value: {
        "primary_keywords": [
            # English
            "toilet", "urinal", "restroom", "lavatory", "washroom", "latrine",
            # Marathi
            "शौचालय", "शौचालये", "मुतारी", "प्रसाधनगृह", "शौच", "संडास",
            # Transliteration
            "shauchalay", "toilet", "urinal", "mutari",
        ],
        "exact_phrases": [
            "public toilet dirty", "toilet door broken", "no water in toilet",
            "toilet cleaning needed", "urinal blocked", "unusable toilet",
            "public toilet stinking", "dirty restroom", "toilet maintenance",
            "सार्वजनिक शौचालय अस्वच्छ", "शौचालयात पाणी नाही", "शौचालयाचा दरवाजा तुटला",
            "मुतारीची दुर्गंधी", "सुलभ शौचालय बंद", "शौचालय स्वच्छ करा",
            "toilet clean nahi", "shauchalay gandagi",
        ],
        "synonyms": [
            "commode", "cubicle", "sulabh", "sanitation block",
            "सुलभ शौचालय", "प्रसाधन गृह",
        ],
        "context_keywords": [
            "stench", "unhygienic", "flush", "tap broken", "lock",
            "अस्वच्छ", "दुर्गंधी", "कडी", "पाणी टंचाई",
        ],
        "negative_keywords": [
            "home toilet", "private building",
        ],
    },

    ComplaintCategory.ELECTRICITY.value: {
        "primary_keywords": [
            # English
            "electricity", "power", "outage", "transformer", "wire", "voltage",
            "sparking", "short circuit", "meter", "current", "shock", "cable",
            # Marathi
            "वीज", "विद्युत", "भारनियमन", "ट्रान्सफॉर्मर", "तार", "स्पार्किंग",
            "मीटर", "करंट", "शॉक", "केबल", "विजेचा",
            # Transliteration
            "vij", "current", "transformer", "powercut", "light geli",
        ],
        "exact_phrases": [
            "power cut", "frequent power cut", "no electricity", "wire sparking",
            "hanging wire", "loose electric wire", "transformer blast", "voltage fluctuation",
            "load shedding", "electric shock danger", "cable burning",
            "वीज पुरवठा खंडित", "लाईट गेली", "विजेचे भारनियमन", "तारेतून ठिणग्या",
            "उघडी वीज तार", "ट्रान्सफॉर्मर जळाला", "कमी जास्त व्होल्टेज",
            "power cut issue", "light geli", "loose wire",
        ],
        "synonyms": [
            "blackout", "feeder", "phase", "mseb", "fuse",
            "शॉर्ट सर्किट", "विद्युत दाब", "फ्युज", "महावितरण",
        ],
        "context_keywords": [
            "fire", "danger", "fluctuation", "appliances", "spark",
            "आग", "धोका", "उपकरणे", "स्फोट",
        ],
        "negative_keywords": [
            "street light only",
        ],
    },

    ComplaintCategory.TRAFFIC.value: {
        "primary_keywords": [
            # English
            "traffic", "signal", "congestion", "parking", "vehicle", "rickshaw",
            "crossing", "divider", "gridlock", "jam",
            # Marathi
            "वाहतूक", "ट्रॅफिक", "सिग्नल", "कोंडी", "वाहन", "पार्किंग", "रिक्षा",
            "गर्दी", "अतिक्रमण",
            # Transliteration
            "traffic", "signal", "jam", "parking", "kondi",
        ],
        "exact_phrases": [
            "traffic jam", "traffic signal not working", "illegal parking", "heavy congestion",
            "wrong side driving", "traffic police needed", "severe gridlock", "signal broken",
            "वाहतूक कोंडी", "सिग्नल बंद", "अवैध पार्किंग", "रस्त्यावर वाहनांची कोंडी",
            "गाड्यांची प्रचंड रांग", "सिग्नल लागत नाही", "वाहतूक ठप्प",
            "traffic jam jhala", "signal band aahe",
        ],
        "synonyms": [
            "bottleneck", "snarl", "encroachment", "zebra crossing",
            "पदपथ अतिक्रमण", "वाहनांची रांग",
        ],
        "context_keywords": [
            "peak hours", "rush", "office time", "school time", "horn",
            "गर्दीच्या वेळी", "सकाळी", "सायंकाळी", "वाजवणे",
        ],
        "negative_keywords": [
            "pothole only",
        ],
    },
}
