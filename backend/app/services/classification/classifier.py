"""
Deterministic Rule-Based Complaint Classifier.
Categorizes citizen grievances using predefined rules and weighted dictionary matching.
ZERO MACHINE LEARNING. Outputs explainable Rule Match Scores and decision reasons.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from backend.app.services.nlp.preprocessing import NLPPreprocessedResult, preprocess_complaint
from backend.app.services.classification.category_rules import CATEGORY_RULES
from backend.app.services.classification.scoring import (
    score_category_rules,
    normalize_rule_score,
    MIN_CLASSIFICATION_THRESHOLD,
)
from backend.app.utils.constants import ComplaintCategory, ComplaintStatus


@dataclass
class ClassificationResult:
    category: str
    rule_match_score: float
    raw_score: float
    matched_keywords: List[str] = field(default_factory=list)
    matched_phrases: List[str] = field(default_factory=list)
    reason: str = ""
    status: str = ComplaintStatus.CLASSIFIED.value
    category_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "rule_match_score": self.rule_match_score,
            "raw_score": self.raw_score,
            "matched_keywords": self.matched_keywords,
            "matched_phrases": self.matched_phrases,
            "reason": self.reason,
            "status": self.status,
            "category_scores": self.category_scores,
        }


def classify_complaint(input_data: Any) -> ClassificationResult:
    """
    Main deterministic classification entry point.
    Accepts raw string or NLPPreprocessedResult.
    Evaluates rule criteria across all 9 municipal categories.
    """
    if isinstance(input_data, str):
        nlp_result = preprocess_complaint(input_data)
    else:
        nlp_result = input_data

    if not nlp_result.tokens:
        return ClassificationResult(
            category=ComplaintCategory.OTHER.value,
            rule_match_score=0.0,
            raw_score=0.0,
            matched_keywords=[],
            matched_phrases=[],
            reason="Complaint text is empty or non-informative.",
            status=ComplaintStatus.NEEDS_REVIEW.value,
            category_scores={},
        )

    category_scores: Dict[str, float] = {}
    category_matches: Dict[str, dict] = {}

    for cat_name, rules in CATEGORY_RULES.items():
        raw_score, keywords, phrases, breakdown = score_category_rules(cat_name, rules, nlp_result)
        category_scores[cat_name] = raw_score
        category_matches[cat_name] = {
            "keywords": keywords,
            "phrases": phrases,
            "breakdown": breakdown,
        }

    # Rank categories by raw score descending
    sorted_categories = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
    top_category, top_raw_score = sorted_categories[0]

    # Evaluate against minimum acceptance threshold
    if top_raw_score < MIN_CLASSIFICATION_THRESHOLD:
        return ClassificationResult(
            category=ComplaintCategory.OTHER.value,
            rule_match_score=0.0,
            raw_score=top_raw_score,
            matched_keywords=[],
            matched_phrases=[],
            reason="Insufficient rule matches for predefined municipal categories. Forwarded for administrative review.",
            status=ComplaintStatus.NEEDS_REVIEW.value,
            category_scores=category_scores,
        )

    best_match_info = category_matches[top_category]
    matched_kws = best_match_info["keywords"]
    matched_phrases = best_match_info["phrases"]
    norm_score = normalize_rule_score(top_raw_score)

    # Construct transparent explanation
    reason_parts = []
    if matched_phrases:
        reason_parts.append(f"matched {len(matched_phrases)} key phrase(s) ({', '.join(repr(p) for p in matched_phrases[:3])})")
    if matched_kws:
        reason_parts.append(f"matched {len(matched_kws)} vocabulary keyword(s) ({', '.join(repr(k) for k in matched_kws[:4])})")

    explanation = f"{top_category} complaint rules triggered: {' and '.join(reason_parts)}."

    return ClassificationResult(
        category=top_category,
        rule_match_score=norm_score,
        raw_score=top_raw_score,
        matched_keywords=matched_kws,
        matched_phrases=matched_phrases,
        reason=explanation,
        status=ComplaintStatus.CLASSIFIED.value,
        category_scores=category_scores,
    )
