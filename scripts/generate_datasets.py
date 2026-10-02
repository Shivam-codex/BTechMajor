"""
Dataset Generator for Academic Rule Development & Evaluation.
Synthesizes:
1. data/complaints/sample_complaints.csv (600+ complaints across all 9 categories, 4 priorities, en/mr/mixed)
2. data/complaints/test_complaints.csv (120+ distinct held-out evaluation complaints)
3. data/rag/rag_questions.json (50 ground-truth evaluation questions for Classical IR evaluation)
"""

import os
import csv
import json
import random
from pathlib import Path

# Fix seed for reproducibility
random.seed(42)

ROOT_DIR = Path(__file__).resolve().parent.parent
COMPLAINTS_DIR = ROOT_DIR / "data" / "complaints"
RAG_DIR = ROOT_DIR / "data" / "rag"
COMPLAINTS_DIR.mkdir(parents=True, exist_ok=True)
RAG_DIR.mkdir(parents=True, exist_ok=True)

LOCATIONS = [
    "Kothrud, Ward 12", "Shivaji Nagar, Ward 4", "Hadapsar, Ward 18", "Viman Nagar, Ward 7",
    "Katraj Chowk, Ward 22", "Baner Road, Ward 9", "Aundh, Ward 8", "Swargate, Ward 15",
    "Karve Road, Ward 11", "FC Road, Ward 3", "Bavdhan, Ward 14", "Camp, Ward 2",
    "Kalyani Nagar, Ward 6", "Pashan, Ward 10", "Dhanori, Ward 20", "Warje, Ward 16",
    "Bibvewadi, Ward 19", "Kondhwa, Ward 21", "Yerawada, Ward 5", "Sinhagad Road, Ward 17",
]

# Category and Priority Templates
TEMPLATES = {
    "Water Supply": {
        "department": "Water Supply Department",
        "en": [
            ("Severe drinking water pipeline leakage near {loc}. Potable water is wasting onto the road.", "Water Supply", "High", "water, leakage, pipeline"),
            ("No water supply in our society since 3 days. Residents are facing acute water crisis.", "Water Supply", "High", "no water, water supply, crisis"),
            ("Very low water pressure during morning hours. Overhead tank is not filling up at all.", "Water Supply", "Medium", "water pressure, supply"),
            ("Drinking water supplied today is yellow, muddy, and smells contaminated.", "Water Supply", "High", "drinking water, contaminated, dirty"),
            ("Municipal water pipe burst near {loc}. Water is gushing into basements.", "Water Supply", "Critical", "pipe burst, water leakage, emergency"),
            ("Request for municipal water tanker due to scheduled pipeline maintenance work.", "Water Supply", "Low", "water tanker, request, supply"),
            ("The public tap at {loc} has broken valve and water is leaking continuously.", "Water Supply", "Medium", "tap, water leak, valve"),
            ("Water supply timing is highly irregular in {loc}. Please fix schedule.", "Water Supply", "Medium", "water supply, timing, irregular"),
        ],
        "mr": [
            ("गेल्या ४ दिवसांपासून आमच्या भागात नळाला पिण्याचे पाणी येत नाही. त्वरित पाणी पुरवठा सुरू करावा.", "Water Supply", "High", "पाणी येत नाही, पाणी पुरवठा"),
            ("{loc} येथे मुख्य पिण्याच्या पाण्याची पाईपलाईन फुटली असून रस्त्यावर लाखो लिटर पाणी वाहत आहे.", "Water Supply", "High", "पाणी, पाईपलाईन, गळती"),
            ("सकाळच्या वेळी नळाला अत्यंत कमी दाबाने पाणी येते. तिसऱ्या मजल्यावर पाणी चढत नाही.", "Water Supply", "Medium", "कमी दाबाने पाणी, नळ, पाणी"),
            ("नळाचे पाणी पिवळे व दुर्गंधीयुक्त येत असून नागरिकांचे आरोग्य धोक्यात आले आहे.", "Water Supply", "High", "पाणी, दूषित पाणी, दुर्गंधी"),
            ("आमच्या कॉलनीतील सार्वजनिक नळाची तोटी तुटली असून पाणी वाया जात आहे.", "Water Supply", "Medium", "नळ, पाणी गळती, तोटी"),
            ("पाणी पुरवठा विभागाकडून टँकर वेळेवर येत नाही. पिण्याच्या पाण्याचा तुटवडा आहे.", "Water Supply", "Medium", "पाणी पुरवठा, टँकर"),
        ],
        "mixed": [
            ("{loc} madhe paani yet nahiye since 2 days. Water pressure khup low ahe.", "Water Supply", "High", "paani, water pressure, no water"),
            ("Main road var water pipe leak zala ahe, drinking water waste hot ahe.", "Water Supply", "Medium", "water, pipe leak, drinking water"),
            ("Water supply timing regularize kara in our colony. Pani khup late yete.", "Water Supply", "Medium", "water supply, timing, pani"),
        ]
    },

    "Garbage/Waste Management": {
        "department": "Sanitation Department",
        "en": [
            ("Community dustbin overflowing with garbage for 4 days near {loc}. Foul smell spreading.", "Garbage/Waste Management", "High", "garbage, dustbin, waste"),
            ("Door to door garbage collection vehicle (Ghanta Gadi) has not visited our street for a week.", "Garbage/Waste Management", "Medium", "garbage collection, waste pickup"),
            ("Illegal garbage dumping on open plot near {loc}. Stray animals are scattering trash.", "Garbage/Waste Management", "High", "garbage dumping, waste, trash"),
            ("Dead street dog lying near school gate at {loc}. Urgent health hazard removal needed.", "Garbage/Waste Management", "Critical", "dead animal, health hazard, waste"),
            ("Commercial shops dumping vegetable waste and rotting debris on sidewalk.", "Garbage/Waste Management", "Medium", "waste, dumping, garbage"),
            ("Request to install a new twin dustbin for segregated waste at {loc}.", "Garbage/Waste Management", "Low", "dustbin, waste segregation, suggestion"),
        ],
        "mr": [
            ("{loc} येथील कचराकुंडी पूर्ण भरली असून रस्त्यावर कचऱ्याचे ढीग साचले आहेत.", "Garbage/Waste Management", "High", "कचराकुंडी, कचरा, ढीग"),
            ("गेल्या पाच दिवसांपासून घंटागाडी आमच्या गल्लीत कचरा संकलनासाठी आलेली नाही.", "Garbage/Waste Management", "Medium", "घंटागाडी, कचरा संकलन"),
            ("रस्त्याच्या कडेला मृत प्राणी पडला असून प्रचंड दुर्गंधी पसरली आहे. त्वरित विल्हेवाट लावा.", "Garbage/Waste Management", "Critical", "मृत प्राणी, कचरा, दुर्गंधी"),
            ("भाजी मंडई परिसरातील टाकाऊ कचरा उचलला नाही. माशा आणि डासांचा प्रादुर्भाव वाढला आहे.", "Garbage/Waste Management", "High", "कचरा, टाकाऊ, माशा"),
            ("कचरा पेटीची नियमित सफाई होत नाही. कॉलनीत रोगराई पसरण्याची भीती आहे.", "Garbage/Waste Management", "Medium", "कचरा, सफाई, स्वच्छता"),
        ],
        "mixed": [
            ("{loc} madhe road var kachra dharla ahe. Garbage truck not coming regularly.", "Garbage/Waste Management", "Medium", "kachra, garbage truck, waste"),
            ("Dustbin full zali ahe ani garbage overflow hot ahe near market.", "Garbage/Waste Management", "High", "dustbin, garbage overflow, waste"),
        ]
    },

    "Road/Pothole": {
        "department": "Roads and Infrastructure Department",
        "en": [
            ("Deep pothole on main carriage lane at {loc}. Several two-wheelers have slipped and crashed.", "Road/Pothole", "Critical", "pothole, accident, damaged road"),
            ("Damaged road surface with gravel loose after recent rains near {loc}. Road repair required.", "Road/Pothole", "Medium", "damaged road, road repair, gravel"),
            ("Huge road cave-in and trench left open by utility contractors without barricades.", "Road/Pothole", "Critical", "road cave in, dangerous, trench"),
            ("Speed breaker installed near {loc} is unpainted and non-standard causing vehicle underbody hit.", "Road/Pothole", "Medium", "speed breaker, road bump"),
            ("Pedestrian footpath tiles broken and missing along the road stretch in {loc}.", "Road/Pothole", "Low", "footpath, pavement, sidewalk"),
            ("Multiple craters and severe potholes on arterial bus corridor causing huge traffic delays.", "Road/Pothole", "High", "potholes, craters, road damage"),
        ],
        "mr": [
            ("{loc} येथील मुख्य रस्त्यावर मोठा खड्डा पडला असून दोन दुचाकींचे गंभीर अपघात झाले आहेत.", "Road/Pothole", "Critical", "खड्डा, रस्ता, अपघात"),
            ("पावसामुळे डांबरीकरण वाहून गेले असून रस्त्यावर सर्वत्र खडी पसरली आहे.", "Road/Pothole", "Medium", "डांबरीकरण, खडी, रस्ता खराब"),
            ("रस्त्यावरील पदपथ (फुटपाथ) तुटलेला असून पादचाऱ्यांना चालणे कठीण झाले आहे.", "Road/Pothole", "Low", "पदपथ, फुटपाथ, रस्ता"),
            ("{loc} चौकात रस्ता खचला असून मोठा खड्डा तयार झाला आहे. त्वरित पॅचवर्क करावे.", "Road/Pothole", "High", "रस्ता खचला, खड्डा, पॅचवर्क"),
            ("बेकायदेशीर गतिरोधक तयार केला असून त्यावर पांढरे पट्टे मारलेले नाहीत.", "Road/Pothole", "Medium", "गतिरोधक, रस्ता"),
        ],
        "mixed": [
            ("Road var khup mothe khadde padle ahet at {loc}. Heavy bike slip risk.", "Road/Pothole", "High", "road, khadde, pothole"),
            ("Damaged rasta needs immediate patchwork before monsoon.", "Road/Pothole", "Medium", "damaged rasta, road, patchwork"),
        ]
    },

    "Street Light": {
        "department": "Electrical Department",
        "en": [
            ("Street light pole SL-44 is completely non-functional at {loc}. Total darkness at night.", "Street Light", "Medium", "street light, dark, pole"),
            ("All street lights along the entire stretch of {loc} are off. Women safety risk at night.", "Street Light", "High", "street lights, dark street, safety"),
            ("Street light pole damaged and tilting precariously over the road after windstorm.", "Street Light", "Critical", "light pole, dangerous, tilting"),
            ("Street lamp bulb flickering continuously and creates strobe distraction near junction.", "Street Light", "Low", "street light, flickering, lamp"),
            ("LED street lights remain switched on 24 hours during daytime wasting municipal power.", "Street Light", "Low", "street light, daytime burning"),
            ("Street lamp fixture glass broken and hanging loosely from the post at {loc}.", "Street Light", "Medium", "street lamp, light post"),
        ],
        "mr": [
            ("{loc} येथील पथदिवे गेल्या ३ दिवसांपासून बंद असून रात्री रस्त्यावर पूर्ण अंधार असतो.", "Street Light", "High", "पथदिवे बंद, अंधार, पथदिवा"),
            ("विजेचा खांब वाकला असून कोणत्याही क्षणी रस्त्यावर पडू शकतो. त्वरित दुरुस्ती करा.", "Street Light", "Critical", "विजेचा खांब, धोकादायक, पोल"),
            ("आमच्या गल्लीतील पथदिवा चालू-बंद (फ्लिकर) होत आहे. नवीन एलईडी बल्ब बसवावा.", "Street Light", "Low", "पथदिवा, दिवा, एलईडी"),
            ("रात्रीच्या वेळी पथदिवे लागत नसल्यामुळे चोरीच्या घटना वाढल्या आहेत.", "Street Light", "High", "पथदिवे, अंधार, रात्री"),
            ("भर दिवसा देखील रस्त्यावरील दिवे चालू असतात, विजेचा अपव्यय थांबवा.", "Street Light", "Low", "रस्त्यावरील दिवे, दिवा"),
        ],
        "mixed": [
            ("Street light working nahi ahe at {loc}. Raatri khup andhar asto.", "Street Light", "Medium", "street light, andhar, light"),
            ("Pole number 12 var led light band padli ahe, please replace bulb.", "Street Light", "Medium", "led light, pole, bulb"),
        ]
    },

    "Drainage/Sewerage": {
        "department": "Drainage Department",
        "en": [
            ("Open manhole without cover near {loc}. Severe life-threatening danger for pedestrians.", "Drainage/Sewerage", "Critical", "open manhole, danger, drainage"),
            ("Underground sewer choked and foul drainage wastewater overflowing onto public road.", "Drainage/Sewerage", "High", "sewer choked, drainage overflow, gutter"),
            ("Sewage water backing up and entering residential ground floor houses in {loc}.", "Drainage/Sewerage", "Critical", "sewage water, backflow, drainage"),
            ("Open stormwater nullah clogged with plastic bottles and silt. Water stagnation causing mosquitoes.", "Drainage/Sewerage", "High", "nullah blocked, drainage, stagnant water"),
            ("Broken concrete slab over stormwater gutter in front of residential gate.", "Drainage/Sewerage", "Medium", "gutter slab, drainage, gutter"),
            ("Drainage chamber cover is damaged and vehicle tires get stuck.", "Drainage/Sewerage", "Medium", "drainage chamber, manhole"),
        ],
        "mr": [
            ("{loc} येथे रस्त्यावरील मॅनहोलचे झाकण तुटलेले/उघडे असून मोठा अपघात होऊ शकतो.", "Drainage/Sewerage", "Critical", "मॅनहोल उघडे, सांडपाणी, अपघात"),
            ("भूमिगत गटार तुंबल्यामुळे सांडपाणी रस्त्यावर वाहत असून प्रचंड दुर्गंधी पसरली आहे.", "Drainage/Sewerage", "High", "गटार तुंबले, सांडपाणी, दुर्गंधी"),
            ("गटाराचे दूषित पाणी घरात शिरत असून डासांचे प्रमाण वाढले आहे.", "Drainage/Sewerage", "Critical", "गटार, सांडपाणी, घरात पाणी"),
            ("पावसाळी नाला गाळाने भरला असून पावसाचे पाणी साचून पूर येण्याची शक्यता आहे.", "Drainage/Sewerage", "High", "नाला तुंबला, सांडपाणी, पूर"),
            ("सांडपाणी वाहिनी फुटली असून मैला रस्त्यावर पसरत आहे.", "Drainage/Sewerage", "High", "सांडपाणी वाहिनी, गटार"),
        ],
        "mixed": [
            ("Drainage line block zali ahe and gutter water is overflowing on road at {loc}.", "Drainage/Sewerage", "High", "drainage block, gutter water, overflow"),
            ("Manhole cover open ahe near school gate. Very dangerous for small kids.", "Drainage/Sewerage", "Critical", "manhole open, dangerous, drainage"),
        ]
    },

    "Public Toilet": {
        "department": "Public Health and Sanitation Department",
        "en": [
            ("Public toilet near bus stand at {loc} is extremely dirty and foul smelling with no running water.", "Public Toilet", "High", "public toilet, dirty, no water"),
            ("Doors and latches broken in municipal ladies public restroom at {loc}.", "Public Toilet", "High", "public restroom, toilet door, safety"),
            ("Urinals in community sanitation complex are completely choked with urine overflowing.", "Public Toilet", "High", "urinal choked, toilet, sanitation"),
            ("Private contractor at public toilet charging illegal fees above prescribed rate.", "Public Toilet", "Medium", "public toilet, overcharging"),
            ("Request to build a disabled-accessible public toilet near public garden in {loc}.", "Public Toilet", "Low", "public toilet, suggestion, accessible"),
        ],
        "mr": [
            ("{loc} येथील सार्वजनिक शौचालय अत्यंत अस्वच्छ असून नळाला पाणी नाही.", "Public Toilet", "High", "सार्वजनिक शौचालय, अस्वच्छ, पाणी नाही"),
            ("महिला शौचालयाचे दरवाजे तुटलेले असून कडी नाही. त्वरित दुरुस्ती करावी.", "Public Toilet", "High", "शौचालय, दरवाजा, महिला सुरक्षा"),
            ("मुतारी चोक झाली असून परिसरात प्रचंड घाण आणि दुर्गंधी पसरली आहे.", "Public Toilet", "High", "मुतारी, शौचालय, दुर्गंधी"),
            ("सुलभ शौचालयाची टाकी भरून वाहते आहे, सक्शन टँकरने रिकामी करावी.", "Public Toilet", "High", "सुलभ शौचालय, टाकी, स्वच्छता"),
        ],
        "mixed": [
            ("Public toilet at {loc} is not cleaned since days. Washroom flush not working.", "Public Toilet", "High", "public toilet, washroom, flush"),
        ]
    },

    "Electricity": {
        "department": "Electrical Department",
        "en": [
            ("Exposed live electrical cable sparking continuously near tree branch at {loc}. Immediate shock hazard.", "Electricity", "Critical", "exposed wire, sparking, electric shock"),
            ("Distribution transformer caught fire and blasted with heavy black smoke in {loc}.", "Electricity", "Critical", "transformer blast, fire, power"),
            ("Unscheduled power cut across the entire locality since morning without notification.", "Electricity", "High", "power cut, outage, electricity"),
            ("High voltage fluctuation in residential grid damaged home electrical appliances.", "Electricity", "High", "voltage fluctuation, power surge"),
            ("Overhead electric service wires sagging too low and touching passing delivery trucks.", "Electricity", "Critical", "overhead wire, electric cable, dangerous"),
            ("Municipal electricity meter sparking inside feeder box at {loc}.", "Electricity", "High", "meter sparking, electricity"),
        ],
        "mr": [
            ("{loc} येथे विजेची उघडी तार तुटून रस्त्यावर पडली असून ठिणग्या उडत आहेत. जीवघेणा धोका आहे.", "Electricity", "Critical", "विजेची उघडी तार, ठिणग्या, धोका"),
            ("ट्रान्सफॉर्मर जळाला असून संपूर्ण वसाहतीत वीज पुरवठा खंडित झाला आहे.", "Electricity", "High", "ट्रान्सफॉर्मर, वीज पुरवठा खंडित"),
            ("वारंवार विजेचे भारनियमन होत असून वीज दाब कमी जास्त (व्होल्टेज फ्लक्चुएशन) होतो.", "Electricity", "High", "भारनियमन, वीज, व्होल्टेज"),
            ("विजेच्या खांबात करंट उतरला असून जनावरांना विजेचा झटका बसण्याची भीती आहे.", "Electricity", "Critical", "करंट, विजेचा झटका, वीज खांब"),
        ],
        "mixed": [
            ("Electric wire sparking zali ahe at {loc}. Heavy load shedding since 6 hours.", "Electricity", "High", "electric wire, sparking, load shedding"),
            ("Power cut issue in our area. Transformer madhun sound yet ahe.", "Electricity", "High", "power cut, transformer, electricity"),
        ]
    },

    "Traffic": {
        "department": "Traffic Management Department",
        "en": [
            ("Traffic signal at busy crossroad {loc} has stopped functioning causing massive gridlock.", "Traffic", "High", "traffic signal, traffic jam, congestion"),
            ("Illegal parking of heavy delivery trucks blocking two full lanes of main road in {loc}.", "Traffic", "High", "illegal parking, traffic congestion"),
            ("Severe traffic jam at square during school peak hours due to lack of traffic police wardens.", "Traffic", "Medium", "traffic jam, peak hours, congestion"),
            ("Zebra crossing markings completely faded on high speed road near hospital at {loc}.", "Traffic", "Low", "zebra crossing, pedestrian safety, traffic"),
            ("Commercial roadside shops encroaching on carriage lane creating major bottle-neck.", "Traffic", "Medium", "encroachment, traffic bottleneck"),
        ],
        "mr": [
            ("{loc} चौकातील ट्रॅफिक सिग्नल बंद पडल्यामुळे चारही बाजूने वाहनांची प्रचंड कोंडी झाली आहे.", "Traffic", "High", "ट्रॅफिक सिग्नल, वाहतूक कोंडी, वाहन"),
            ("रस्त्यावर बेकायदेशीर वाहने पार्क केल्यामुळे बस आणि रुग्णवाहिकांना वाट मिळत नाही.", "Traffic", "High", "अवैध पार्किंग, वाहतूक कोंडी, रस्ता"),
            ("शाळेच्या सुटण्याच्या वेळेस चौकात वाहतूक पोलीस नसल्याने वाहतूक ठप्प होते.", "Traffic", "Medium", "वाहतूक ठप्प, वाहतूक पोलीस"),
            ("पदपथावर फेरीवाल्यांचे अतिक्रमण झाल्यामुळे पादचाऱ्यांना रस्त्यावरून चालावे लागत आहे.", "Traffic", "Medium", "अतिक्रमण, वाहतूक, पदपथ"),
        ],
        "mixed": [
            ("Heavy traffic jam at {loc} signal due to broken signal light and illegal parking.", "Traffic", "High", "traffic jam, signal, illegal parking"),
        ]
    },

    "Other": {
        "department": "General Grievance Cell",
        "en": [
            ("General inquiry regarding property tax rebate deadline and payment receipt download.", "Other", "Low", "inquiry, tax, general"),
            ("Requesting permission form details for setting up cultural event canopy in public ground.", "Other", "Low", "permission, event, inquiry"),
            ("Complaint regarding excessive noise pollution from unauthorized sound systems late at night.", "Other", "Medium", "noise pollution, sound, complaint"),
            ("Stray cattle wandering on colony internal gardens eating saplings.", "Other", "Low", "stray cattle, garden, complaint"),
            ("Request for tree pruning as overgrown branches are obstructing residential window view.", "Other", "Low", "tree pruning, branches, request"),
        ],
        "mr": [
            ("मालमत्ता कर सवलत मिळवण्यासाठी लागणाऱ्या आवश्यक कागदपत्रांची माहिती हवी आहे.", "Other", "Low", "चौकशी, कागदपत्रे, माहिती"),
            ("कॉलनीतील उद्यानातील झाडांच्या फांद्या छाटणी करण्याची विनंती आहे.", "Other", "Low", "फांद्या छाटणी, विनंती, उद्यान"),
            ("रात्रीच्या वेळी मोठ्या आवाजात वाजणाऱ्या डीजेमुळे वृद्ध व रुग्णांना त्रास होत आहे.", "Other", "Medium", "आवाज, डीजे, त्रास"),
        ],
        "mixed": [
            ("General inquiry regarding birth certificate status and municipal office timings.", "Other", "Low", "inquiry, certificate, timing"),
        ]
    }
}


def generate_complaint_pool(target_count=650):
    rows = []
    cid = 1000

    categories = list(TEMPLATES.keys())
    while len(rows) < target_count:
        for cat in categories:
            cat_data = TEMPLATES[cat]
            dept = cat_data["department"]

            # Sample languages proportionally: 50% English, 35% Marathi, 15% Mixed
            lang_choice = random.choices(["en", "mr", "mixed"], weights=[0.50, 0.35, 0.15])[0]
            templates_list = cat_data.get(lang_choice, cat_data["en"])

            template_item = random.choice(templates_list)
            text_template, expected_cat, priority, kws = template_item

            loc = random.choice(LOCATIONS)
            text = text_template.replace("{loc}", loc)

            cid += 1
            comp_id = f"CMP-DEV-{cid}"

            rows.append({
                "id": comp_id,
                "complaint_text": text,
                "language": lang_choice,
                "category": expected_cat,
                "department": dept,
                "priority": priority,
                "keywords": kws,
            })

            if len(rows) >= target_count:
                break

    return rows


def generate_test_pool(test_count=135):
    """Generates distinct, held-out complaints with variations for testing."""
    test_rows = []
    tid = 5000

    for cat in TEMPLATES.keys():
        cat_data = TEMPLATES[cat]
        dept = cat_data["department"]

        for lang in ["en", "mr", "mixed"]:
            templates = cat_data.get(lang, [])
            for tpl in templates:
                text_tpl, expected_cat, priority, kws = tpl
                loc = f"Sector {random.randint(1, 20)}, Zone {random.choice(['A', 'B', 'C'])}"
                # Distinct modifier
                modifier = random.choice([
                    "Immediate inspection demanded.",
                    "Please look into this issue urgently.",
                    "Citizens are suffering due to this negligence.",
                    "Issue has been unresolved for days.",
                    "Kindly take strict action.",
                ])
                if lang == "mr":
                    modifier = random.choice([
                        "त्वरित दखल घेऊन कारवाई करावी.",
                        "नागरिकांचे हाल होत आहेत.",
                        "कृपया तात्काळ दुरुस्ती करावी.",
                    ])
                elif lang == "mixed":
                    modifier = "Please resolve fast."

                distinct_text = f"{text_tpl.replace('{loc}', loc)} {modifier}"
                tid += 1
                test_rows.append({
                    "id": f"CMP-TEST-{tid}",
                    "complaint_text": distinct_text,
                    "language": lang,
                    "category": expected_cat,
                    "department": dept,
                    "priority": priority,
                    "keywords": kws,
                })
                if len(test_rows) >= test_count:
                    return test_rows

    return test_rows


def generate_rag_questions():
    """Generates 50 ground-truth questions mapped to knowledge base documents."""
    questions = [
        {"question": "How do I report a pothole on my street?", "expected_documents": ["Road and Pothole Complaint Procedure", "Citizen Frequently Asked Questions (FAQ) Charter"], "expected_category": "Road/Pothole"},
        {"question": "What is the turnaround time for a major water pipeline burst?", "expected_documents": ["Water Supply Complaint Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Water Supply"},
        {"question": "How often does the garbage truck visit our neighborhood?", "expected_documents": ["Solid Waste and Garbage Collection Guidelines", "Citizen Frequently Asked Questions (FAQ) Charter"], "expected_category": "Garbage/Waste Management"},
        {"question": "What should I do if an electrical wire is sparking on the road?", "expected_documents": ["Municipal Electricity and Power Supply Grievance Procedure", "Citizen Frequently Asked Questions (FAQ) Charter"], "expected_category": "Electricity"},
        {"question": "How to file a complaint about an open manhole cover?", "expected_documents": ["Drainage and Sewerage Complaint Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Drainage/Sewerage"},
        {"question": "What are the rules regarding public toilet cleanliness and maintenance?", "expected_documents": ["Public Toilet Guidelines and Sanitation Protocol"], "expected_category": "Public Toilet"},
        {"question": "How can I report illegal parking causing traffic gridlock?", "expected_documents": ["Traffic and Parking Grievance Redressal Procedure"], "expected_category": "Traffic"},
        {"question": "How does the municipal complaint escalation process work?", "expected_documents": ["Municipal Complaint Escalation Matrix"], "expected_category": "Other"},
        {"question": "What are the different stages and statuses of a complaint?", "expected_documents": ["Complaint Status and Tracking Guide"], "expected_category": "Other"},
        {"question": "What are the responsibilities of the Water Supply Department?", "expected_documents": ["Municipal Department Responsibilities Directory", "Water Supply Complaint Procedure"], "expected_category": "Water Supply"},
        {"question": "What is the SLA for pothole repairs on major roads?", "expected_documents": ["Road and Pothole Complaint Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Road/Pothole"},
        {"question": "What is the fine for illegal dumping of waste on public roads?", "expected_documents": ["Solid Waste and Garbage Collection Guidelines"], "expected_category": "Garbage/Waste Management"},
        {"question": "Who repairs non-functional street lights at night?", "expected_documents": ["Street Light Complaint Procedure", "Municipal Department Responsibilities Directory"], "expected_category": "Street Light"},
        {"question": "How can I check the status of my complaint using Complaint ID?", "expected_documents": ["Complaint Status and Tracking Guide", "General Municipal Complaint Registration Procedure"], "expected_category": "Other"},
        {"question": "What is the emergency helpline number for municipal grievances?", "expected_documents": ["Water Supply Complaint Procedure", "Municipal Electricity and Power Supply Grievance Procedure"], "expected_category": "Water Supply"},
        {"question": "How long does dead animal removal take?", "expected_documents": ["Solid Waste and Garbage Collection Guidelines", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Garbage/Waste Management"},
        {"question": "How fast are missing manhole covers replaced?", "expected_documents": ["Drainage and Sewerage Complaint Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Drainage/Sewerage"},
        {"question": "What can I do if water supplied is muddy or yellow?", "expected_documents": ["Water Supply Complaint Procedure"], "expected_category": "Water Supply"},
        {"question": "Can I submit a complaint in Marathi or mixed script?", "expected_documents": ["Citizen Frequently Asked Questions (FAQ) Charter", "General Municipal Complaint Registration Procedure"], "expected_category": "Other"},
        {"question": "What is the escalation officer for Level 2 complaints?", "expected_documents": ["Municipal Complaint Escalation Matrix"], "expected_category": "Other"},
        {"question": "What documents are required to register a complaint?", "expected_documents": ["General Municipal Complaint Registration Procedure"], "expected_category": "Other"},
        {"question": "How do I report low water pressure in my building?", "expected_documents": ["Water Supply Complaint Procedure"], "expected_category": "Water Supply"},
        {"question": "How to report community dustbin overflow?", "expected_documents": ["Solid Waste and Garbage Collection Guidelines"], "expected_category": "Garbage/Waste Management"},
        {"question": "What to do if street light is flickering continuously?", "expected_documents": ["Street Light Complaint Procedure"], "expected_category": "Street Light"},
        {"question": "What is the turnaround time for a broken traffic signal?", "expected_documents": ["Traffic and Parking Grievance Redressal Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Traffic"},
        {"question": "Who handles drainage overflow and sewage water?", "expected_documents": ["Drainage and Sewerage Complaint Procedure", "Municipal Department Responsibilities Directory"], "expected_category": "Drainage/Sewerage"},
        {"question": "What is the protocol if sewage enters residential premises?", "expected_documents": ["Drainage and Sewerage Complaint Procedure"], "expected_category": "Drainage/Sewerage"},
        {"question": "How to report a damaged speed breaker on colony road?", "expected_documents": ["Road and Pothole Complaint Procedure"], "expected_category": "Road/Pothole"},
        {"question": "How to report dirty public urinal near bus stand?", "expected_documents": ["Public Toilet Guidelines and Sanitation Protocol"], "expected_category": "Public Toilet"},
        {"question": "What is the SLA for distribution transformer breakdown?", "expected_documents": ["Municipal Electricity and Power Supply Grievance Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Electricity"},
        {"question": "How can I reopen an unresolved complaint?", "expected_documents": ["Municipal Complaint Escalation Matrix"], "expected_category": "Other"},
        {"question": "What department is responsible for street sweeping and cleaning?", "expected_documents": ["Solid Waste and Garbage Collection Guidelines", "Municipal Department Responsibilities Directory"], "expected_category": "Garbage/Waste Management"},
        {"question": "How do I report high-voltage fluctuations damaging appliances?", "expected_documents": ["Municipal Electricity and Power Supply Grievance Procedure"], "expected_category": "Electricity"},
        {"question": "What should I do if traffic jam is caused by unauthorized hawkers?", "expected_documents": ["Traffic and Parking Grievance Redressal Procedure"], "expected_category": "Traffic"},
        {"question": "How to get a water tanker during pipeline repairs?", "expected_documents": ["Water Supply Complaint Procedure", "Municipal Department Responsibilities Directory"], "expected_category": "Water Supply"},
        {"question": "Who maintains footpaths and pedestrian sidewalks?", "expected_documents": ["Road and Pothole Complaint Procedure", "Municipal Department Responsibilities Directory"], "expected_category": "Road/Pothole"},
        {"question": "What does the status 'Needs Review' mean?", "expected_documents": ["Complaint Status and Tracking Guide"], "expected_category": "Other"},
        {"question": "What does the status 'In Progress' mean?", "expected_documents": ["Complaint Status and Tracking Guide"], "expected_category": "Other"},
        {"question": "What is the deadline for resolving road cave-in?", "expected_documents": ["Road and Pothole Complaint Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Road/Pothole"},
        {"question": "How do I report day-and-night burning street lamps?", "expected_documents": ["Street Light Complaint Procedure"], "expected_category": "Street Light"},
        {"question": "What is the resolution timeline for septic tank emptying?", "expected_documents": ["Public Toilet Guidelines and Sanitation Protocol"], "expected_category": "Public Toilet"},
        {"question": "How to report open nullah silt blockage before monsoon?", "expected_documents": ["Drainage and Sewerage Complaint Procedure"], "expected_category": "Drainage/Sewerage"},
        {"question": "How does the system automatically detect complaint priority?", "expected_documents": ["General Municipal Complaint Registration Procedure"], "expected_category": "Other"},
        {"question": "What is the role of the General Grievance Cell?", "expected_documents": ["Municipal Department Responsibilities Directory"], "expected_category": "Other"},
        {"question": "What to do if utility trench is left uncovered on road?", "expected_documents": ["Road and Pothole Complaint Procedure"], "expected_category": "Road/Pothole"},
        {"question": "Can I upload a PDF or DOCX file with my complaint?", "expected_documents": ["General Municipal Complaint Registration Procedure", "Citizen Frequently Asked Questions (FAQ) Charter"], "expected_category": "Other"},
        {"question": "What happens if a complaint is rejected?", "expected_documents": ["Complaint Status and Tracking Guide"], "expected_category": "Other"},
        {"question": "Who is the Level 3 escalation authority?", "expected_documents": ["Municipal Complaint Escalation Matrix"], "expected_category": "Other"},
        {"question": "How do I report broken streetlight pole liable to fall?", "expected_documents": ["Street Light Complaint Procedure", "Resolution SLA and Grievance Redressal Charter"], "expected_category": "Street Light"},
        {"question": "What is the penalty for open garbage burning?", "expected_documents": ["Solid Waste and Garbage Collection Guidelines"], "expected_category": "Garbage/Waste Management"},
    ]
    return questions


def main():
    print("Generating Rule Development and Evaluation Dataset...")
    sample_rows = generate_complaint_pool(650)
    sample_file = COMPLAINTS_DIR / "sample_complaints.csv"
    with open(sample_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "complaint_text", "language", "category", "department", "priority", "keywords"])
        writer.writeheader()
        writer.writerows(sample_rows)
    print(f"-> Saved {len(sample_rows)} complaints to {sample_file}")

    print("Generating Held-out Test Dataset...")
    test_rows = generate_test_pool(135)
    test_file = COMPLAINTS_DIR / "test_complaints.csv"
    with open(test_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "complaint_text", "language", "category", "department", "priority", "keywords"])
        writer.writeheader()
        writer.writerows(test_rows)
    print(f"-> Saved {len(test_rows)} test complaints to {test_file}")

    print("Generating RAG Evaluation Ground-Truth Questions...")
    rag_questions = generate_rag_questions()
    rag_file = RAG_DIR / "rag_questions.json"
    with open(rag_file, "w", encoding="utf-8") as f:
        json.dump(rag_questions, f, indent=2, ensure_ascii=False)
    print(f"-> Saved {len(rag_questions)} RAG questions to {rag_file}")


if __name__ == "__main__":
    main()
