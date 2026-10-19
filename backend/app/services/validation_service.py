"""
Question paper validation and quality assurance service for BlindPaper.
Evaluates syllabus relevance, duplicate questions, marks consistency, and unit coverage.
"""

import math
import re
from collections import Counter
from typing import Any, Dict, List, Set, Tuple

from app.schemas.question import QuestionItem
from app.schemas.validation import (
    DuplicatePair,
    MarksValidationResult,
    QuestionRelevance,
    UnitCoverageResult,
    ValidationRequest,
    ValidationResponse,
)

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


class ValidationService:
    """
    Core validation engine for examination question papers.
    Evaluates syllabus relevance, duplicates, marks distribution, and unit coverage.
    """

    DUPLICATE_SIMILARITY_THRESHOLD = 0.70
    RELEVANCE_HIGH_THRESHOLD = 0.40
    RELEVANCE_UNCERTAIN_THRESHOLD = 0.15

    def validate_paper(self, request: ValidationRequest) -> ValidationResponse:
        """
        Execute full validation pipeline against the provided paper.
        Does NOT mutate or discard any questions.
        """
        issues: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        # 1. Marks and Count Validation
        marks_result = self._validate_marks_and_counts(request, issues)

        # 2. Syllabus Relevance Validation
        relevance_results = self._validate_syllabus_relevance(request, warnings)

        # 3. Duplicate Detection
        duplicate_pairs = self._detect_duplicates(request.questions, warnings)

        # 4. Unit Coverage Validation
        unit_coverage = self._validate_unit_coverage(request, warnings, recommendations)

        # 5. Determine Overall Status & Summary
        overall_status = self._compute_overall_status(issues, warnings)

        summary = self._build_summary(
            status=overall_status,
            total_questions=len(request.questions),
            issues_count=len(issues),
            warnings_count=len(warnings),
            coverage_pct=unit_coverage.coverage_percentage,
        )

        # Add general faculty advisory if needed
        if warnings and not recommendations:
            recommendations.append("Review flagged items to ensure alignment with department examination guidelines.")

        return ValidationResponse(
            overall_status=overall_status,
            summary=summary,
            total_questions=len(request.questions),
            relevance_results=relevance_results,
            duplicate_pairs=duplicate_pairs,
            marks_validation=marks_result,
            unit_coverage=unit_coverage,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _validate_marks_and_counts(
        self, request: ValidationRequest, issues: List[str]
    ) -> MarksValidationResult:
        """Verify total marks, question count, and positivity of marks."""
        actual_count = len(request.questions)
        actual_marks = sum(q.marks for q in request.questions)

        count_matches = actual_count == request.question_count
        marks_match = actual_marks == request.total_marks

        # Check for zero or negative marks
        invalid_mark_questions = [q.question_id for q in request.questions if q.marks <= 0]
        if invalid_mark_questions:
            issues.append(
                f"Questions with IDs {invalid_mark_questions} have non-positive marks. Every question must have marks >= 1."
            )

        # Check for empty question texts
        empty_text_questions = [q.question_id for q in request.questions if not q.question_text.strip()]
        if empty_text_questions:
            issues.append(
                f"Questions with IDs {empty_text_questions} contain empty question text."
            )

        if not count_matches:
            issues.append(
                f"Question count mismatch: expected {request.question_count}, but paper contains {actual_count} questions."
            )

        if not marks_match:
            issues.append(
                f"Total marks mismatch: expected {request.total_marks} marks, but total sums to {actual_marks} marks."
            )

        is_valid = count_matches and marks_match and not invalid_mark_questions and not empty_text_questions

        if is_valid:
            details = f"Marks and question count match specifications ({actual_count} questions, {actual_marks} total marks)."
        else:
            details = (
                f"Validation failed: expected {request.question_count} questions / {request.total_marks} marks, "
                f"found {actual_count} questions / {actual_marks} marks."
            )

        return MarksValidationResult(
            is_valid=is_valid,
            expected_marks=request.total_marks,
            actual_marks=actual_marks,
            expected_count=request.question_count,
            actual_count=actual_count,
            details=details,
        )

    def _validate_syllabus_relevance(
        self, request: ValidationRequest, warnings: List[str]
    ) -> List[QuestionRelevance]:
        """Assess the lexical and contextual relevance of each question to syllabus text."""
        syllabus_tokens = set(extract_informative_tokens(request.syllabus_text))
        selected_units_tokens = set(extract_informative_tokens(" ".join(request.selected_units)))
        all_syllabus_tokens = syllabus_tokens | selected_units_tokens

        results: List[QuestionRelevance] = []

        for q in request.questions:
            q_tokens = extract_informative_tokens(q.question_text)
            unit_tokens = set(extract_informative_tokens(q.unit_or_topic))

            if not q_tokens:
                results.append(
                    QuestionRelevance(
                        question_id=q.question_id,
                        question_text=q.question_text,
                        relevance_score=0.0,
                        status="low",
                        matched_terms=[],
                        explanation="Question text contains no significant domain keywords.",
                    )
                )
                warnings.append(f"Question #{q.question_id} has very low evidence of syllabus relevance.")
                continue

            # Terms in question that actually exist in the syllabus
            matched = [t for t in q_tokens if t in all_syllabus_tokens]
            unique_q_tokens = set(q_tokens)
            unique_matched = set(matched)

            # If zero terms match the syllabus, it is definitely low relevance
            if len(unique_matched) == 0:
                relevance_score = 0.0
                status = "low"
                explanation = (
                    "Low relevance (0.00): no significant syllabus terms found. "
                    "Question may be outside prescribed syllabus."
                )
                warnings.append(
                    f"Question #{q.question_id} appears to be outside the prescribed syllabus (score: 0.00)."
                )
            else:
                overlap_ratio = len(unique_matched) / len(unique_q_tokens)

                # Only give unit boost if declared unit terms actually exist in the syllabus
                unit_matched_in_syllabus = [t for t in q_tokens if t in unit_tokens and t in all_syllabus_tokens]
                boost = 0.10 if unit_matched_in_syllabus else 0.0

                relevance_score = min(1.0, round(overlap_ratio + boost, 3))

                if relevance_score >= self.RELEVANCE_HIGH_THRESHOLD or len(unique_matched) >= 3:
                    status = "high"
                    explanation = f"High relevance: matched syllabus terms: {', '.join(sorted(unique_matched)[:5])}."
                elif relevance_score >= self.RELEVANCE_UNCERTAIN_THRESHOLD or len(unique_matched) >= 1:
                    status = "review_required"
                    explanation = (
                        f"Moderate relevance ({relevance_score:.2f}): matched terms {', '.join(sorted(unique_matched))}. "
                        "Faculty review recommended to confirm subject context."
                    )
                    warnings.append(
                        f"Question #{q.question_id} has uncertain syllabus relevance (score: {relevance_score:.2f})."
                    )
                else:
                    status = "low"
                    explanation = (
                        f"Low relevance ({relevance_score:.2f}): insufficient syllabus terms found. "
                        "Question may be outside prescribed syllabus."
                    )
                    warnings.append(
                        f"Question #{q.question_id} appears to be outside the prescribed syllabus (score: {relevance_score:.2f})."
                    )

            results.append(
                QuestionRelevance(
                    question_id=q.question_id,
                    question_text=q.question_text,
                    relevance_score=relevance_score,
                    status=status,
                    matched_terms=sorted(list(unique_matched)),
                    explanation=explanation,
                )
            )

        return results

    def _detect_duplicates(
        self, questions: List[QuestionItem], warnings: List[str]
    ) -> List[DuplicatePair]:
        """Detect exact and near-duplicate pairs among questions."""
        duplicates: List[DuplicatePair] = []
        n = len(questions)

        for i in range(n):
            for j in range(i + 1, n):
                q1 = questions[i]
                q2 = questions[j]

                norm1 = normalize_text(q1.question_text)
                norm2 = normalize_text(q2.question_text)

                if norm1 == norm2:
                    duplicates.append(
                        DuplicatePair(
                            question_id_1=q1.question_id,
                            question_id_2=q2.question_id,
                            question_text_1=q1.question_text,
                            question_text_2=q2.question_text,
                            similarity_score=1.0,
                            match_type="exact",
                            reason="Questions are identical after basic text normalization.",
                        )
                    )
                    warnings.append(
                        f"Exact duplicate detected between Question #{q1.question_id} and Question #{q2.question_id}."
                    )
                else:
                    similarity = compute_cosine_similarity(q1.question_text, q2.question_text)
                    if similarity >= self.DUPLICATE_SIMILARITY_THRESHOLD:
                        duplicates.append(
                            DuplicatePair(
                                question_id_1=q1.question_id,
                                question_id_2=q2.question_id,
                                question_text_1=q1.question_text,
                                question_text_2=q2.question_text,
                                similarity_score=round(similarity, 3),
                                match_type="near_duplicate",
                                reason=f"High lexical similarity ({similarity:.2f}) indicates potential duplication.",
                            )
                        )
                        warnings.append(
                            f"Near-duplicate detected between Question #{q1.question_id} and Question #{q2.question_id} (similarity: {similarity:.2f})."
                        )

        return duplicates

    def _validate_unit_coverage(
        self, request: ValidationRequest, warnings: List[str], recommendations: List[str]
    ) -> UnitCoverageResult:
        """Determine which selected units have question coverage and identify gaps."""
        covered: Set[str] = set()

        for unit in request.selected_units:
            # Extract non-structural domain tokens for the unit
            unit_tokens = set(
                t
                for t in extract_informative_tokens(unit)
                if t not in STRUCTURAL_STOPWORDS and not t.isdigit()
            )

            for q in request.questions:
                q_unit_tokens = set(
                    t
                    for t in extract_informative_tokens(q.unit_or_topic)
                    if t not in STRUCTURAL_STOPWORDS and not t.isdigit()
                )
                q_text_tokens = set(extract_informative_tokens(q.question_text))

                # Check if unit domain tokens overlap significantly with declared unit or question text
                if unit_tokens and unit_tokens.issubset(q_unit_tokens):
                    covered.add(unit)
                    break

                matched_domain = unit_tokens & (q_unit_tokens | q_text_tokens)
                if unit_tokens and len(matched_domain) >= max(1, (len(unit_tokens) + 1) // 2):
                    covered.add(unit)
                    break

        uncovered = [u for u in request.selected_units if u not in covered]
        total_units = len(request.selected_units)
        covered_count = len(covered)
        coverage_pct = round((covered_count / total_units) * 100.0, 1) if total_units > 0 else 0.0

        if uncovered:
            warnings.append(
                f"Selected units with no questions: {', '.join(uncovered)}."
            )
            recommendations.append(
                f"Add questions covering unit(s): {', '.join(uncovered)} to ensure balanced syllabus coverage."
            )

        return UnitCoverageResult(
            total_selected_units=total_units,
            covered_units=sorted(list(covered)),
            uncovered_units=sorted(uncovered),
            coverage_percentage=coverage_pct,
        )

    def _compute_overall_status(
        self, issues: List[str], warnings: List[str]
    ) -> str:
        """
        Compute 'pass', 'review_required', or 'fail'.
        - 'fail' on definite structural/marks/count errors.
        - 'review_required' on duplicates, low/uncertain relevance, or missing units.
        - 'pass' if all checks pass cleanly.
        """
        if issues:
            return "fail"
        if warnings:
            return "review_required"
        return "pass"

    def _build_summary(
        self, status: str, total_questions: int, issues_count: int, warnings_count: int, coverage_pct: float
    ) -> str:
        """Construct a concise, faculty-friendly summary message."""
        if status == "pass":
            return (
                f"Validation passed successfully. All {total_questions} questions comply with syllabus requirements, "
                f"marks distribution, and unit coverage ({coverage_pct}%)."
            )
        elif status == "fail":
            return (
                f"Validation failed with {issues_count} critical structural issue(s). "
                "Marks or question counts violate examination specifications."
            )
        else:
            return (
                f"Validation completed with {warnings_count} advisory warning(s). "
                "Faculty review is required for suspected duplicates, unit coverage, or syllabus relevance."
            )


# Singleton validation service instance
validation_service = ValidationService()
