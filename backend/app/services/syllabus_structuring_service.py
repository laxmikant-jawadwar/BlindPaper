"""
Service for structuring extracted syllabus text into the parts BlindPaper keeps:
course name and code, course description, course outcomes (with Bloom's levels) and
the course contents (unit number, unit name, topics).

Targets the common university syllabus template: a title block, outcome tables, then a
"Course Contents:" section made of "Unit N: Title      X Hours" lines, each followed by a
wrapped, comma-separated topic list. Everything is rule-based; no LLM is involved.
Prerequisites, objectives, CO-PO grid, assessment scheme, textbooks and hours are ignored.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from app.schemas.syllabus import CourseOutcome, CourseUnit

logger = logging.getLogger(__name__)

BLOOMS_NAMES = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}
# Descriptors vary between syllabi ("Understand" / "Understanding"); match on the stem
BLOOMS_STEMS = (("remember", 1), ("understand", 2), ("appl", 3), ("analy", 4), ("evaluat", 5), ("creat", 6))
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

# "Unit 4 Title", "Unit 4: Title", "Module II - Title" ...
UNIT_HEADING_PATTERN = re.compile(
    r"^(?P<label>unit|module|chapter|section)\s*[-–]?\s*(?P<number>\d+|[ivxlcdm]+)\b\s*[:.\-–]?\s*(?P<rest>.*)$",
    re.IGNORECASE,
)

# "... 8 Hours" at the end of a unit heading line (dropped, hours are not kept)
HOURS_PATTERN = re.compile(
    r"[\s:.\-–,(]*\b\d+\s*(?:hours?|hrs?|lectures?|periods?)\b[\s.)]*$",
    re.IGNORECASE,
)

CONTENTS_START_PATTERN = re.compile(
    r"^(?:detailed\s+|course\s+)?(?:contents|syllabus)\s*:?\s*$", re.IGNORECASE
)

# Headings that close the "Course Contents" section
CONTENTS_END_PATTERN = re.compile(
    r"^(?:text\s*books?|references?|reference\s+books?|suggested\s+(?:readings?|books)"
    r"|home\s+assignments?|assignments?|e-?resources|web\s+resources|online\s+resources"
    r"|list\s+of\s+(?:experiments|practicals))\s*:?\s*$",
    re.IGNORECASE,
)

# Any other section heading; ends the course description
SECTION_HEADING_PATTERN = re.compile(
    r"^(?:course\s+[a-z][a-z\- ]{2,30}\s*:|co-?po\s+mapping\s*:"
    r"|(?:teacher\s+)?assessments?(?:\s+scheme)?\s*:|text\s*books?\s*:|references?\s*:)",
    re.IGNORECASE,
)

PAGE_FOOTER_PATTERNS = [
    re.compile(r"^\d+\s*\|\s*p\s*a\s*g\s*e$", re.IGNORECASE),  # "4 | P a g e"
    re.compile(r"^page\s+\d+(?:\s+of\s+\d+)?$", re.IGNORECASE),  # "Page 3 of 6"
]

BOILERPLATE_PATTERNS = [
    re.compile(r"^(?:hours|credits|marks|course code|prerequisites?)\s*:", re.IGNORECASE),
    re.compile(r"^(?:textbooks?|references?|outcomes?|course objectives?)\s*:", re.IGNORECASE),
]

SUBJECT_LABEL_PATTERN = re.compile(
    r"^(?:course\s*name|course\s*title|title\s+of\s+the\s+course|name\s+of\s+the\s+course"
    r"|subject(?:\s*name)?|paper\s*title|course)\s*[:\-]\s*(?P<value>\S.*)$",
    re.IGNORECASE,
)

COURSE_CODE_PATTERN = re.compile(
    r"^(?:course|subject|paper)\s*code\s*[:\-]\s*(?P<code>[A-Za-z0-9][A-Za-z0-9_\-/.]*)",
    re.IGNORECASE,
)

COURSE_DESCRIPTION_PATTERN = re.compile(r"^course\s+description\s*[:\-]\s*(?P<text>.*)$", re.IGNORECASE)

CO_CODE_PATTERN = re.compile(r"CO\d+", re.IGNORECASE)
ROMAN_CELL_PATTERN = re.compile(r"[IVX]+")
BLOOM_WORD_PATTERN = re.compile(r"(?:remember|understand|appl|analy[sz]|evaluat|creat)\w*", re.IGNORECASE)
GRID_CELL_PATTERN = re.compile(r"[\d\-]+")  # cells of a CO-PO grid row

BULLET_PATTERN = re.compile(r"^(?:\d+[.)]|\(?[a-zA-Z][.)]|[-•*–—▪●○])\s+")

# PDF lines at least this long that don't end a sentence are treated as wrapped
WRAPPED_LINE_MIN_LENGTH = 60
TITLE_BLOCK_LINE_LIMIT = 40


def roman_to_int(text: str) -> Optional[int]:
    """'IV' -> 4. Returns None for anything that is not a roman numeral."""
    letters = text.upper()
    if not letters or any(ch not in ROMAN_VALUES for ch in letters):
        return None
    total = 0
    for index, ch in enumerate(letters):
        value = ROMAN_VALUES[ch]
        if index + 1 < len(letters) and value < ROMAN_VALUES[letters[index + 1]]:
            total -= value
        else:
            total += value
    return total


class SyllabusStructuringService:
    """Turns raw syllabus text (and its tables) into the structured syllabus."""

    # ------------------------------------------------------------------
    # Title block: course name and code
    # ------------------------------------------------------------------
    def extract_subject_name(self, lines: List[str], fallback_filename: str) -> str:
        """Read the course title from the title block, else derive it from the filename."""
        for line in lines[:TITLE_BLOCK_LINE_LIMIT]:
            match = SUBJECT_LABEL_PATTERN.match(line)
            if not match:
                continue
            # A wide gap separates the value from the next table column ("L  T  P  Credit")
            value = re.split(r"\s{2,}", match.group("value").strip())[0].strip(" .:;-")
            if 2 < len(value) < 100:
                return value

        clean_name = re.sub(r"\.pdf$", "", fallback_filename, flags=re.IGNORECASE)
        clean_name = clean_name.replace("_", " ").replace("-", " ")
        return clean_name.title()

    def extract_course_code(self, lines: List[str]) -> Optional[str]:
        for line in lines[:TITLE_BLOCK_LINE_LIMIT]:
            match = COURSE_CODE_PATTERN.match(line)
            if match:
                return match.group("code").strip(".")
        return None

    # ------------------------------------------------------------------
    # Course description
    # ------------------------------------------------------------------
    def extract_course_description(self, lines: List[str]) -> Optional[str]:
        """The text after 'Course Description:' up to the next section heading."""
        for index, line in enumerate(lines):
            match = COURSE_DESCRIPTION_PATTERN.match(line)
            if not match:
                continue
            parts = [match.group("text")]
            for following in lines[index + 1:]:
                if SECTION_HEADING_PATTERN.match(following) or UNIT_HEADING_PATTERN.match(following):
                    break
                parts.append(following)
            return self._tidy(" ".join(parts)) or None
        return None

    # ------------------------------------------------------------------
    # Course outcomes (from the tables)
    # ------------------------------------------------------------------
    def extract_course_outcomes(self, tables: Optional[Sequence[Sequence[Sequence[str]]]]) -> List[CourseOutcome]:
        """
        Read outcome rows ("CO1 | description | II | Understand") from the extracted tables.
        CO-PO grid rows also start with 'CO1' but hold only digits, so they are skipped.
        """
        outcomes: List[CourseOutcome] = []
        seen: set = set()
        for table in tables or []:
            for row in table:
                cells = [" ".join((cell or "").split()) for cell in row]
                cells = [cell for cell in cells if cell]
                if len(cells) < 2 or not CO_CODE_PATTERN.fullmatch(cells[0]):
                    continue
                rest = cells[1:]
                if all(GRID_CELL_PATTERN.fullmatch(cell) for cell in rest):
                    continue

                code = cells[0].upper()
                if code in seen:
                    continue
                roman = next((c for c in rest if ROMAN_CELL_PATTERN.fullmatch(c)), None)
                descriptor = next((c for c in rest if BLOOM_WORD_PATTERN.fullmatch(c)), None)
                description = self._tidy(" ".join(c for c in rest if c not in (roman, descriptor)))
                if not description:
                    continue

                seen.add(code)
                level = roman_to_int(roman) if roman else None
                if level not in BLOOMS_NAMES and descriptor:
                    level = next((n for stem, n in BLOOMS_STEMS if descriptor.lower().startswith(stem)), None)
                level = level if level in BLOOMS_NAMES else None
                outcomes.append(
                    CourseOutcome(
                        code=code,
                        description=description,
                        blooms_level=level,
                        blooms_descriptor=BLOOMS_NAMES.get(level) or descriptor,
                    )
                )
        return outcomes

    # ------------------------------------------------------------------
    # Topics
    # ------------------------------------------------------------------
    def parse_topics_from_text(self, text: str) -> List[str]:
        """Split the text of one unit into a flat list of topics."""
        lines = [" ".join(line.split()) for line in text.split("\n")]
        topics: List[str] = []
        for item in self._group_into_items([line for line in lines if line]):
            for part in self._split_list(item):
                topic = self._topic_text(part)
                if topic:
                    topics.append(topic)
        return topics

    def _group_into_items(self, lines: List[str]) -> List[str]:
        """
        Join PDF-wrapped lines back together. A bullet, or a line that does not
        continue the previous one, starts a new item.
        """
        items: List[str] = []
        previous = ""
        for line in lines:
            if any(p.search(line) for p in BOILERPLATE_PATTERNS):
                previous = ""
                continue

            bullet = BULLET_PATTERN.match(line)
            if bullet:
                items.append(line[bullet.end():])
            elif items and self._continues(previous, line):
                items[-1] = f"{items[-1]} {line}"
            else:
                items.append(line)
            previous = line
        return items

    @staticmethod
    def _continues(previous: str, line: str) -> bool:
        if not previous:
            return False
        if previous.endswith((",", "-", "–", "&", "/")) or line[0].islower():
            return True
        ends_sentence = previous.endswith((".", ";", ":", "?", "!"))
        return len(previous) >= WRAPPED_LINE_MIN_LENGTH and not ends_sentence

    def _split_list(self, text: str) -> List[str]:
        """Split on commas, semicolons and sentence ends, never inside brackets."""
        parts: List[str] = []
        buffer: List[str] = []
        depth = 0
        for index, char in enumerate(text):
            if char in "([":
                depth += 1
            elif char in ")]":
                depth = max(0, depth - 1)

            if depth == 0 and (char in ",;" or self._ends_sentence(text, index)):
                parts.append("".join(buffer))
                buffer = []
            else:
                buffer.append(char)
        parts.append("".join(buffer))
        return parts

    @staticmethod
    def _ends_sentence(text: str, index: int) -> bool:
        """A period after a word or ')' that is followed by a capitalised word."""
        if text[index] != "." or index < 2 or index + 1 >= len(text) or not text[index + 1].isspace():
            return False
        before = text[index - 1]
        if not (before == ")" or (before.islower() and text[index - 2].islower())):
            return False
        following = text[index + 1:].lstrip()
        return bool(following) and following[0].isupper()

    def _topic_text(self, text: str) -> Optional[str]:
        topic = self._tidy(text).strip(" .,;:-–—")
        if len(topic) < 2 or not re.search(r"[A-Za-z]", topic):
            return None
        return topic[0].upper() + topic[1:] if topic[0].islower() else topic

    @staticmethod
    def _tidy(text: str) -> str:
        """Collapse whitespace and close hyphens left by line wraps ('real- world' -> 'real-world')."""
        return re.sub(r"(?<=\w)- (?=[a-z])", "-", " ".join(text.split()))

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------
    def _find_unit_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Locate unit headings, preferring the 'Course Contents' section."""
        start = next(
            (i + 1 for i, line in enumerate(lines) if CONTENTS_START_PATTERN.match(line)),
            0,
        )
        blocks = self._scan_units(lines[start:])
        if not blocks and start:
            blocks = self._scan_units(lines)
        return blocks

    @staticmethod
    def _scan_units(lines: List[str]) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None
        for line in lines:
            heading = UNIT_HEADING_PATTERN.match(line)
            if heading:
                token = heading.group("number")
                number = int(token) if token.isdigit() else roman_to_int(token)
                rest = heading.group("rest")
                hours = HOURS_PATTERN.search(rest)
                title = rest[: hours.start()] if hours else rest
                current = {
                    "number": number or len(blocks) + 1,
                    "title": " ".join(title.split()).strip(" :.-–"),
                    "lines": [],
                }
                blocks.append(current)
            elif current is not None:
                if CONTENTS_END_PATTERN.match(line):
                    break
                current["lines"].append(line)
        return blocks

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def structure_syllabus_text(
        self,
        extracted_text: str,
        subject_name: str | None = None,
        filename: str = "syllabus.pdf",
        page_count: int = 1,
        tables: Optional[Sequence[Sequence[Sequence[str]]]] = None,
    ) -> Dict[str, Any]:
        """
        Structure syllabus text (and, when available, its tables) into the stored shape.
        """
        lines = [
            line.strip()
            for line in extracted_text.splitlines()
            if line.strip() and not any(p.match(line.strip()) for p in PAGE_FOOTER_PATTERNS)
        ]

        blocks = self._find_unit_blocks(lines)
        course_content = [
            CourseUnit(
                unit_number=block["number"],
                unit_name=block["title"] or f"Unit {block['number']}",
                topics=self.parse_topics_from_text("\n".join(block["lines"])),
            )
            for block in blocks
        ]
        course_outcomes = self.extract_course_outcomes(tables)

        if course_content:
            message = f"Found {len(course_content)} units and {len(course_outcomes)} course outcomes."
        else:
            message = "No unit headings were found, so the course contents could not be structured. Please review."

        return {
            "subject_name": (subject_name or "").strip() or self.extract_subject_name(lines, filename),
            "course_code": self.extract_course_code(lines),
            "course_description": self.extract_course_description(lines),
            "course_outcomes": course_outcomes,
            "course_content": course_content,
            "filename": filename,
            "page_count": page_count,
            "extracted_text": extracted_text,
            "processing_status": "structured" if course_content else "extracted",
            "message": message,
        }


syllabus_structuring_service = SyllabusStructuringService()
