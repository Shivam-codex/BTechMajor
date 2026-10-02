"""
Deterministic weighted scoring engine for complaint classification.
Computes transparent rule match scores with explainable point breakdowns.
NO MACHINE LEARNING — 100% dictionary & rule-driven arithmetic.
"""

from typing import Dict, List, Set, Tuple
from backend.app.services.nlp.preprocessing import NLPPreprocessedResult

# Deterministic point weights
WEIGHT_EXACT_PHRASE = 5.0
WEIGHT_PRIMARY_KEYWORD = 3.0
WEIGHT_SYNONYM = 2.0
WEIGHT_CONTEXT = 1.0
PENALTY_NEGATIVE = -4.0

MIN_CLASSIFICATION_THRESHOLD = 3.0  # Must match at least 1 primary keyword or phrase


def score_category_rules(
    category: str,
    rules: dict,
    nlp_result: NLPPreprocessedResult,
) -> Tuple[float, List[str], List[str], Dict[str, float]]:
    """
    Evaluates rule matches for a given category against preprocessed complaint text.
    Returns:
        (total_score, matched_keywords, matched_phrases, score_breakdown)
    """
    matched_phrases: List[str] = []
    matched_keywords: List[str] = []
    breakdown: Dict[str, float] = {
        "phrase_points": 0.0,
        "primary_points": 0.0,
        "synonym_points": 0.0,
        "context_points": 0.0,
        "penalty_points": 0.0,
    }

    lower_text = nlp_result.normalized_text.lower()
    token_set = nlp_result.token_set
    lemma_set = nlp_result.lemmatized_set
    all_tokens = token_set | lemma_set

    # 1. Exact phrase matching (Weight: 5.0)
    for phrase in rules.get("exact_phrases", []):
        phrase_clean = phrase.lower().strip()
        if phrase_clean in lower_text:
            matched_phrases.append(phrase)
            breakdown["phrase_points"] += WEIGHT_EXACT_PHRASE

    # 2. Primary keyword matching (Weight: 3.0)
    for kw in rules.get("primary_keywords", []):
        kw_clean = kw.lower().strip()
        # Direct word match or lemma match
        if kw_clean in all_tokens or kw_clean in lower_text:
            matched_keywords.append(kw)
            breakdown["primary_points"] += WEIGHT_PRIMARY_KEYWORD

    # 3. Synonym matching (Weight: 2.0)
    for syn in rules.get("synonyms", []):
        syn_clean = syn.lower().strip()
        if syn_clean in all_tokens or syn_clean in lower_text:
            matched_keywords.append(syn)
            breakdown["synonym_points"] += WEIGHT_SYNONYM

    # 4. Context keyword matching (Weight: 1.0)
    for ctx in rules.get("context_keywords", []):
        ctx_clean = ctx.lower().strip()
        if ctx_clean in all_tokens or ctx_clean in lower_text:
            breakdown["context_points"] += WEIGHT_CONTEXT

    # 5. Negative keyword penalty (Penalty: -4.0)
    for neg in rules.get("negative_keywords", []):
        neg_clean = neg.lower().strip()
        if neg_clean in lower_text:
            breakdown["penalty_points"] += PENALTY_NEGATIVE

    # Deduplicate matched keywords while preserving order
    unique_matched_keywords = list(dict.fromkeys(matched_keywords))
    unique_matched_phrases = list(dict.fromkeys(matched_phrases))

    raw_total = sum(breakdown.values())
    final_score = max(0.0, raw_total)

    return final_score, unique_matched_keywords, unique_matched_phrases, breakdown


def normalize_rule_score(raw_score: float) -> float:
    """
    Transforms raw rule points into a normalized 'Rule Match Score' bounded in [0.0, 1.0].
    Deterministic hyperbolic saturation curve:
      score = min(0.99, (raw_score / (raw_score + 4.0)) * 1.35)
    Examples:
      raw = 0.0  -> 0.0
      raw = 3.0  -> 0.58
      raw = 5.0  -> 0.75
      raw = 8.0  -> 0.90
      raw >= 11  -> 0.98+
    """
    if raw_score <= 0.0:
        return 0.0
    normalized = (raw_score / (raw_score + 4.0)) * 1.35
    return round(min(0.99, max(0.0, normalized)), 4)
