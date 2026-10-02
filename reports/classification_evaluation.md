# Academic Research Report: Deterministic Rule-Based Complaint Classification Evaluation

**Project Title:** AI-Based Smart City Complaint Management System  
**Evaluation Type:** Non-ML Deterministic Lexical & Rule Match Evaluation  
**Test Set Size:** 110 held-out municipal grievances  
**Languages Evaluated:** English, Marathi (Devanagari), and Code-mixed Marathi-English  

## 1. Executive Summary & Key Results

- **Overall Categorization Accuracy:** **91.82%**
- **Macro Average Precision:** **93.63%**
- **Macro Average Recall:** **90.65%**
- **Macro Average F1-Score:** **91.41%**
- **Priority Detection Accuracy:** **57.27%**

## 2. Category-Wise Performance Breakdown

| Category | Precision | Recall | F1-Score | Test Support |
|:---|:---:|:---:|:---:|:---:|
| Water Supply | 85.0% | 100.0% | 91.9% | 17 |
| Garbage/Waste Management | 92.3% | 92.3% | 92.3% | 13 |
| Road/Pothole | 76.5% | 100.0% | 86.7% | 13 |
| Street Light | 100.0% | 100.0% | 100.0% | 13 |
| Drainage/Sewerage | 100.0% | 84.6% | 91.7% | 13 |
| Public Toilet | 100.0% | 80.0% | 88.9% | 10 |
| Electricity | 100.0% | 100.0% | 100.0% | 12 |
| Traffic | 100.0% | 70.0% | 82.4% | 10 |
| Other | 88.9% | 88.9% | 88.9% | 9 |
| **Macro Average** | **93.6%** | **90.6%** | **91.4%** | **110** |

## 3. Confusion Matrix

Rows represent Ground Truth, Columns represent Deterministic Rule Predictions:

| Actual \ Predicted | Water Supply | Garbage/Waste Management | Road/Pothole | Street Light | Drainage/Sewerage | Public Toilet | Electricity | Traffic | Other |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Water Supply** | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Garbage/Waste Management** | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| **Road/Pothole** | 0 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Street Light** | 0 | 0 | 0 | 13 | 0 | 0 | 0 | 0 | 0 |
| **Drainage/Sewerage** | 1 | 0 | 1 | 0 | 11 | 0 | 0 | 0 | 0 |
| **Public Toilet** | 1 | 1 | 0 | 0 | 0 | 8 | 0 | 0 | 0 |
| **Electricity** | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 |
| **Traffic** | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 7 | 0 |
| **Other** | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |

## 4. Error Analysis and Edge Cases

Identified 9 misclassified grievances on the held-out set:

### Case 1: ID `CMP-TEST-5021`
- **Grievance Text:** *"Dead street dog lying near school gate at Sector 14, Zone C. Urgent health hazard removal needed. Kindly take strict action."*
- **Ground Truth:** `Garbage/Waste Management`
- **Rule Prediction:** `Other` (Rule Match Score: 0.0)
- **Rule Reason:** Insufficient rule matches for predefined municipal categories. Forwarded for administrative review.

### Case 2: ID `CMP-TEST-5063`
- **Grievance Text:** *"Sector 14, Zone C येथे रस्त्यावरील मॅनहोलचे झाकण तुटलेले/उघडे असून मोठा अपघात होऊ शकतो. त्वरित दखल घेऊन कारवाई करावी."*
- **Ground Truth:** `Drainage/Sewerage`
- **Rule Prediction:** `Road/Pothole` (Rule Match Score: 0.675)
- **Rule Reason:** Road/Pothole complaint rules triggered: matched 1 vocabulary keyword(s) ('रस्ता').

### Case 3: ID `CMP-TEST-5066`
- **Grievance Text:** *"पावसाळी नाला गाळाने भरला असून पावसाचे पाणी साचून पूर येण्याची शक्यता आहे. त्वरित दखल घेऊन कारवाई करावी."*
- **Ground Truth:** `Drainage/Sewerage`
- **Rule Prediction:** `Water Supply` (Rule Match Score: 0.5786)
- **Rule Reason:** Water Supply complaint rules triggered: matched 1 vocabulary keyword(s) ('पाणी').

### Case 4: ID `CMP-TEST-5075`
- **Grievance Text:** *"Sector 8, Zone A येथील सार्वजनिक शौचालय अत्यंत अस्वच्छ असून नळाला पाणी नाही. नागरिकांचे हाल होत आहेत."*
- **Ground Truth:** `Public Toilet`
- **Rule Prediction:** `Water Supply` (Rule Match Score: 0.99)
- **Rule Reason:** Water Supply complaint rules triggered: matched 1 key phrase(s) ('नळाला पाणी नाही') and matched 2 vocabulary keyword(s) ('पाणी', 'नळ').

### Case 5: ID `CMP-TEST-5077`
- **Grievance Text:** *"मुतारी चोक झाली असून परिसरात प्रचंड घाण आणि दुर्गंधी पसरली आहे. नागरिकांचे हाल होत आहेत."*
- **Ground Truth:** `Public Toilet`
- **Rule Prediction:** `Garbage/Waste Management` (Rule Match Score: 0.9346)
- **Rule Reason:** Garbage/Waste Management complaint rules triggered: matched 1 key phrase(s) ('दुर्गंधी पसरली') and matched 1 vocabulary keyword(s) ('घाण').

## 5. Methodology & Non-ML Justification

1. **Deterministic Processing:** Tokenization, Unicode canonical normalization, and lemmatization without black-box neural networks.
2. **Weighted Dictionaries:** Exact phrase matching (5.0 pts), primary keywords (3.0 pts), synonyms (2.0 pts), context (1.0 pt), negative suppressions (-4.0 pts).
3. **Zero Probabilistic Hallucination:** Every classification outputs an exact, auditable chain of triggered phrases and vocabulary tokens.
