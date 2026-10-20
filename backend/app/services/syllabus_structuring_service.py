"""
Service for parsing and structuring extracted syllabus text into units, topics,
and suggested Bloom's Taxonomy cognitive levels.
"""

import logging
import re
from typing import Any, Dict, List, Tuple

from app.schemas.syllabus import (
    BLOOMS_LEVELS,
    StructuredSyllabus,
    TopicStructure,
    UnitStructure,
)

logger = logging.getLogger(__name__)

# Bloom's Taxonomy keyword associations (lowercase)
BLOOMS_KEYWORDS: Dict[str, List[str]] = {
    "Remember": [
        "define", "definition", "list", "recall", "state", "name", "identify",
        "mention", "what is", "memorize", "label", "recognize", "reproduce",
    ],
    "Understand": [
        "explain", "describe", "discuss", "classify", "summarize", "illustrate",
        "interpret", "overview", "distinguish", "comprehend", "outline", "concept",
        "introduction", "fundamentals", "basics", "review",
    ],
    "Apply": [
        "implement", "implementation", "calculate", "solve", "demonstrate", "use",
        "apply", "application", "execute", "construct", "practice", "compute",
        "operate", "code", "programming", "algorithm", "operations", "handling",
    ],
    "Analyze": [
        "analyze", "analysis", "compare", "contrast", "differentiate", "distinguish",
        "examine", "investigate", "breakdown", "categorize", "troubleshoot",
        "inspect", "complexity", "efficiency", "performance",
    ],
    "Evaluate": [
        "evaluate", "evaluation", "assess", "assessment", "judge", "justify",
        "critique", "verify", "recommend", "prioritize", "validate", "rate",
        "defense", "optimality", "tradeoffs",
    ],
    "Create": [
        "design", "create", "formulate", "compose", "devise", "architect",
        "synthesize", "generate", "plan", "build", "integrate", "develop",
        "framework", "system design",
    ],
}

# Regex to detect Unit/Module/Chapter boundaries
UNIT_HEADING_PATTERNS = [
    re.compile(
        r"^(?:unit|module|chapter|section)\s*(?:[ivxlcdm]+|\d+)[:\.\-\s]+(.*)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:unit|module|chapter|section)\s*(?:[ivxlcdm]+|\d+)\s*$",
        re.IGNORECASE,
    ),
]

BOILERPLATE_PATTERNS = [
    re.compile(r"^(?:hours|credits|marks|course code|lecture|tutorial|practical|prerequisites)[:\s]", re.IGNORECASE),
    re.compile(r"^(?:textbooks?|references?|outcomes?|course objectives?)[:\s]", re.IGNORECASE),
]


class SyllabusStructuringService:
    """Parses raw syllabus text into structured units, topics, and Bloom's levels."""

    def infer_blooms_levels(self, text: str) -> Tuple[List[str], str]:
        """
        Infer Bloom's Taxonomy cognitive levels based on keyword analysis.
        Returns:
            Tuple of (list_of_levels, confidence_status)
            where confidence is 'inferred' or 'needs_review'.
        """
        text_lower = text.lower()
        matched_levels: List[str] = []

        for level, keywords in BLOOMS_KEYWORDS.items():
            for kw in keywords:
                # Word boundary match for precision
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, text_lower):
                    if level not in matched_levels:
                        matched_levels.append(level)
                    break

        if matched_levels:
            return matched_levels, "inferred"

        # If no strong keywords match, default to Understand with needs_review flag
        return ["Understand"], "needs_review"

    def extract_subject_name(self, text: str, fallback_filename: str) -> str:
        """Attempt to extract course or subject title from document header."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:8]:
            match = re.search(r"(?:course|subject|title|paper)\s*(?:name|title)?[:\s\-]+(.+)", line, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                if len(candidate) > 2 and len(candidate) < 100:
                    return candidate

        # If first line looks like a course name (reasonable length, not a header/code)
        if lines and 3 < len(lines[0]) < 80 and not lines[0].lower().startswith("page"):
            return lines[0]

        # Fallback to cleaned filename
        clean_name = re.sub(r"\.pdf$", "", fallback_filename, flags=re.IGNORECASE)
        clean_name = clean_name.replace("_", " ").replace("-", " ")
        return clean_name.title()

    def parse_topics_from_text(self, text: str) -> List[TopicStructure]:
        """
        Extract topics and subtopics from a block of unit text.
        """
        topics: List[TopicStructure] = []
        raw_items: List[str] = []

        # Split on bullet points, semicolons, or newlines
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            # Skip boilerplate (credits, textbook headers, etc.)
            if any(p.search(line) for p in BOILERPLATE_PATTERNS):
                continue

            # Remove leading bullet characters or numbers (e.g., "1. ", "• ", "- ")
            cleaned_line = re.sub(r"^(?:[\d\.\-\*\•\–\—\)\(]+|\b[a-z]\))\s*", "", line).strip()
            if not cleaned_line:
                continue

            # If line has semicolon-separated topics, split them
            if ";" in cleaned_line:
                parts = [p.strip() for p in cleaned_line.split(";") if p.strip()]
                raw_items.extend(parts)
            else:
                raw_items.append(cleaned_line)

        for item in raw_items:
            # Check for colon separating topic and subtopics
            subtopics: List[str] = []
            if ":" in item:
                parts = item.split(":", 1)
                topic_title = parts[0].strip()
                subtopics_str = parts[1].strip()
                subtopics = [
                    s.strip()
                    for s in re.split(r"[,;]", subtopics_str)
                    if s.strip()
                ]
            else:
                topic_title = item

            # Further check if topic_title has parenthetical details
            if "(" in topic_title and topic_title.endswith(")"):
                match = re.match(r"^(.*?)\s*\((.*?)\)$", topic_title)
                if match:
                    topic_title = match.group(1).strip()
                    parenthetical = match.group(2).strip()
                    subtopics.extend([s.strip() for s in re.split(r"[,;]", parenthetical) if s.strip()])

            if not topic_title or len(topic_title) < 2:
                continue

            full_context = f"{topic_title} {' '.join(subtopics)}"
            blooms_levels, confidence = self.infer_blooms_levels(full_context)

            topics.append(
                TopicStructure(
                    topic_name=topic_title,
                    subtopics=subtopics,
                    blooms_levels=blooms_levels,
                    blooms_confidence=confidence,
                )
            )

        return topics

    def structure_syllabus_text(
        self,
        extracted_text: str,
        subject_name: str | None = None,
        filename: str = "syllabus.pdf",
        page_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Structure syllabus text into units, topics, and Bloom's classifications.
        """
        detected_subject = subject_name or self.extract_subject_name(extracted_text, filename)

        # 1. Identify unit boundaries in lines
        lines = extracted_text.split("\n")
        unit_blocks: List[Tuple[str, List[str]]] = []
        current_unit_name: str = ""
        current_unit_lines: List[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            is_unit_header = False
            matched_header = ""

            for pattern in UNIT_HEADING_PATTERNS:
                m = pattern.match(line_str)
                if m:
                    is_unit_header = True
                    matched_header = line_str
                    break

            if is_unit_header:
                if current_unit_name and current_unit_lines:
                    unit_blocks.append((current_unit_name, list(current_unit_lines)))
                    current_unit_lines.clear()
                current_unit_name = matched_header
            else:
                if current_unit_name:
                    current_unit_lines.append(line_str)
                else:
                    # Content before the first explicit unit
                    current_unit_lines.append(line_str)

        if current_unit_name and current_unit_lines:
            unit_blocks.append((current_unit_name, current_unit_lines))
        elif not unit_blocks and current_unit_lines:
            # No explicit Unit headers were found, group whole content into Unit 1
            unit_blocks.append(("Unit 1: Course Topics", current_unit_lines))

        # 2. Build structured units
        structured_units: List[UnitStructure] = []
        for idx, (unit_label, ulines) in enumerate(unit_blocks, start=1):
            unit_content = "\n".join(ulines)
            topics = self.parse_topics_from_text(unit_content)

            # If no topics parsed from lines, fallback to creating at least one topic from unit label or summary
            if not topics:
                topics = [
                    TopicStructure(
                        topic_name=f"Overview of {unit_label}",
                        subtopics=[],
                        blooms_levels=["Understand"],
                        blooms_confidence="needs_review",
                    )
                ]

            clean_unit_name = unit_label.strip()
            # If label is just "Unit 1", add helpful title if available
            if re.match(r"^Unit\s+\d+$", clean_unit_name, re.IGNORECASE) and topics:
                clean_unit_name = f"{clean_unit_name}: {topics[0].topic_name}"

            structured_units.append(
                UnitStructure(
                    unit_name=clean_unit_name,
                    topics=topics,
                )
            )

        structured_syllabus = StructuredSyllabus(units=structured_units)

        return {
            "subject_name": detected_subject,
            "filename": filename,
            "page_count": page_count,
            "extracted_text": extracted_text,
            "structured_syllabus": structured_syllabus,
            "message": f"Successfully structured {len(structured_units)} units with Bloom's Taxonomy recommendations.",
        }


syllabus_structuring_service = SyllabusStructuringService()
