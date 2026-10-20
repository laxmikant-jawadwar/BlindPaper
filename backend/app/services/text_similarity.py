"""
Lightweight text similarity helpers used to judge syllabus relevance and duplicate questions:
tokenising, stop-word removal, stemming and word-frequency cosine similarity.
"""

import math
import re
from collections import Counter
from typing import Any, Dict, List, Set, Tuple

# Standard English stopwords to eliminate non-informative terms during relevance checks
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "explain",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    "discuss", "describe", "define", "briefly", "detail", "write", "note", "following", "given",
}

# Structural syllabus labeling words to exclude from domain matching
STRUCTURAL_STOPWORDS: Set[str] = {
    "unit", "units", "chapter", "chapters", "module", "modules",
    "section", "sections", "topic", "topics", "part", "parts",
}


def normalize_text(text: str) -> str:
    """Normalize text by converting to lowercase and stripping punctuation/extra whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def stem_token(token: str) -> str:
    """Basic lightweight suffix normalization for English plural/inflection variations."""
    if len(token) > 4:
        if token.endswith("ing"):
            return token[:-3]
        if token.endswith("ies"):
            return token[:-3] + "y"
        if token.endswith("es"):
            return token[:-2]
        if token.endswith("s") and not token.endswith("ss"):
            return token[:-1]
        if token.endswith("ed"):
            return token[:-2]
    return token


def extract_informative_tokens(text: str) -> List[str]:
    """Tokenize, stem, and filter out single characters, numbers, and common stopwords."""
    normalized = normalize_text(text)
    tokens = normalized.split()
    return [
        stem_token(t)
        for t in tokens
        if len(t) > 1 and t not in STOPWORDS and not t.isdigit()
    ]


def compute_cosine_similarity(text1: str, text2: str) -> float:
    """
    Compute word-frequency cosine similarity between two texts using stemmed tokens.
    Returns a score between 0.0 and 1.0.
    """
    tokens1 = extract_informative_tokens(text1)
    tokens2 = extract_informative_tokens(text2)

    if not tokens1 or not tokens2:
        return 0.0

    vec1 = Counter(tokens1)
    vec2 = Counter(tokens2)

    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)

    sum1 = sum(val ** 2 for val in vec1.values())
    sum2 = sum(val ** 2 for val in vec2.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0

    return min(1.0, max(0.0, float(numerator) / denominator))
