"""The printable question paper (an approved paper's download), laid out with ReportLab."""

import io
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.paper import QuestionGroupSpec
from app.services import paper_rules

logger = logging.getLogger(__name__)

EXAM_TITLES = {"MSE": "MID SEMESTER EXAMINATION", "ESE": "END SEMESTER EXAMINATION"}
PAGE_WIDTH, MARGIN = A4[0], 40
INK, MUTED, NAVY = colors.HexColor("#0F172A"), colors.HexColor("#64748B"), colors.HexColor("#1E3A8A")

# ---- fonts -------------------------------------------------------------------------------------
# Numericals use Greek letters, subscripts (x1), currency signs and maths symbols. The app ships DejaVu Sans
# (app/assets/fonts) because it covers all of them, so papers print the same on every machine.
FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
FONT_FILES = ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf")
FONT_NAMES = ("DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Oblique")


@dataclass(frozen=True)
class Fonts:
    regular: str
    bold: str
    italic: str
    unicode: bool  # False: only Helvetica, so symbols must be spelled out
    glyphs: Optional[FrozenSet[int]] = None  # code points the font can print (None: not tracked)


@lru_cache(maxsize=1)
def load_fonts() -> Fonts:
    try:
        faces = [TTFont(name, str(FONT_DIR / file)) for name, file in zip(FONT_NAMES, FONT_FILES)]
        for face in faces:
            pdfmetrics.registerFont(face)
        return Fonts(*FONT_NAMES, unicode=True, glyphs=frozenset(faces[0].face.charToGlyph))
    except Exception:
        # The font files are missing or damaged: still produce a paper, with symbols spelled out in ASCII
        logger.warning("Could not load the bundled DejaVu fonts; falling back to Helvetica", exc_info=True)
        return Fonts("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", unicode=False)


# ---- text clean-up -----------------------------------------------------------------------------
# Typographic look-alikes that fonts often lack, and invisible characters
TYPOGRAPHY = {
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2212": "-",
    "\u00a0": " ", "\u2007": " ", "\u2009": " ", "\u200a": " ", "\u202f": " ",
    "\u200b": "", "\u200c": "", "\u200d": "", "\u2060": "", "\ufeff": "",
}
# What to print when the font is only Helvetica
ASCII_FALLBACK = {
    "\u2264": "<=", "\u2265": ">=", "\u2260": "!=", "\u2248": "~", "\u2192": "->", "\u2190": "<-", "\u2194": "<->",
    "\u221e": "infinity", "\u221a": "sqrt", "\u2211": "sum", "\u222b": "integral", "\u2206": "Delta", "\u2202": "d",
    "\u03b1": "alpha", "\u03b2": "beta", "\u03b3": "gamma", "\u03b4": "delta", "\u03b5": "epsilon", "\u03b8": "theta",
    "\u03bb": "lambda", "\u03bc": "mu", "\u03c0": "pi", "\u03c1": "rho", "\u03c3": "sigma", "\u03c4": "tau",
    "\u03c6": "phi", "\u03c9": "omega", "\u0394": "Delta", "\u03a3": "Sigma", "\u03a0": "Pi", "\u03a6": "Phi",
    "\u03a9": "Omega", "\u0398": "Theta", "\u039b": "Lambda",
}


def printable(value: str, fonts: Fonts) -> str:
    """
    Normalise typography, then make sure every character can be printed: with the bundled font only
    something it really lacks (an emoji, say) is replaced, by '?'; with plain Helvetica symbols are spelled out.
    """
    text = "".join(TYPOGRAPHY.get(ch, ch) for ch in value)
    if not fonts.unicode:
        text = "".join(ASCII_FALLBACK.get(ch, ch) for ch in text)
        return text.encode("cp1252", errors="replace").decode("cp1252")
    if fonts.glyphs is not None:
        # ReportLab can only embed characters up to U+FFFF; emoji and other astral characters would print as garbage
        text = "".join(
            ch if ch == "\n" or (ord(ch) <= 0xFFFF and ord(ch) in fonts.glyphs) else ASCII_FALLBACK.get(ch, "?") for ch in text
        )
    return text


def _text(value: str, fonts: Fonts) -> str:
    """Question text is plain text; escape it so '<=' or '&' can't be read as markup."""
    return escape(printable(value, fonts)).replace("\n", "<br/>")


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that prints 'Page X of Y' once the page count is known."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_states: List[dict] = []

    def showPage(self) -> None:
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self.setFont("Helvetica", 8)
            self.setFillColor(MUTED)
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.line(MARGIN, 36, PAGE_WIDTH - MARGIN, 36)
            self.drawString(MARGIN, 24, "BlindPaper - Question Paper")
            self.drawRightString(PAGE_WIDTH - MARGIN, 24, f"Page {self._pageNumber} of {total}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def build_styles(fonts: Fonts) -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]

    def make(name: str, font: str, **kwargs: Any) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base, fontName=font, **{"textColor": INK, **kwargs})

    regular, bold, italic = fonts.regular, fonts.bold, fonts.italic
    return {
        "title": make("Title", bold, fontSize=14, leading=18, alignment=1, spaceAfter=2),
        "course": make("Course", bold, fontSize=12, leading=16, alignment=1, textColor=NAVY),
        "meta": make("Meta", regular, fontSize=9.5, leading=13, alignment=1, textColor=MUTED),
        "info": make("Info", bold, fontSize=9.5, leading=13),
        "info_right": make("InfoRight", bold, fontSize=9.5, leading=13, alignment=2),
        "group": make("Group", bold, fontSize=10.5, leading=14),
        "group_marks": make("GroupMarks", bold, fontSize=10, leading=14, alignment=2, textColor=NAVY),
        "label": make("Label", bold, fontSize=10, leading=14),
        "question": make("Question", regular, fontSize=10, leading=14.5),
        "option": make("Option", regular, fontSize=9.5, leading=13.5, leftIndent=14),
        "marks": make("Marks", bold, fontSize=10, leading=14, alignment=2),
        "tag": make("Tag", italic, fontSize=7.5, leading=10, textColor=MUTED),
        "end": make("End", bold, fontSize=9, leading=12, alignment=1, textColor=MUTED),
    }


class PaperPdfService:
    def generate(self, paper: Dict[str, Any], fonts: Optional[Fonts] = None) -> bytes:
        fonts = fonts or load_fonts()
        styles = build_styles(fonts)
        text = lambda value: _text(value, fonts)  # noqa: E731
        questions = {q["sub_question_id"]: q for q in paper.get("questions", [])}
        groups = [QuestionGroupSpec(**group) for group in paper["groups"]]
        content_width = PAGE_WIDTH - 2 * MARGIN

        story: List[Any] = [
            Paragraph(EXAM_TITLES.get(paper["exam_type"], "EXAMINATION"), styles["title"]),
            Paragraph(f"{text(paper['course_name'])} ({text(paper['course_code'])})", styles["course"]),
            Paragraph(f"{text(paper['year'])} &nbsp;|&nbsp; {text(paper['semester'])}", styles["meta"]),
            Spacer(1, 8),
        ]
        info = Table(
            [[Paragraph(f"Maximum Marks: {_number(paper['total_marks'])}", styles["info"]),
              Paragraph("Instructions: answer as directed in each question.", styles["info_right"])]],
            colWidths=[content_width * 0.4, content_width * 0.6],
        )
        info.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1, INK), ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
                                  ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story += [info, Spacer(1, 10)]

        for group_index, group in enumerate(groups, start=1):
            story.append(self._group_header(group_index, group, styles, content_width, text))
            for sub_index, sub_question in enumerate(group.sub_questions):
                question = questions.get(sub_question.id)
                story.append(
                    self._sub_question(paper_rules.label_for(sub_index), sub_question, question, styles, content_width, text)
                )
            story.append(Spacer(1, 8))

        story += [HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceBefore=6, spaceAfter=6),
                  Paragraph("- END OF QUESTION PAPER -", styles["end"])]

        buffer = io.BytesIO()
        SimpleDocTemplate(buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=50).build(
            story, canvasmaker=NumberedCanvas
        )
        return buffer.getvalue()

    @staticmethod
    def _group_header(index: int, group: QuestionGroupSpec, styles: Dict[str, ParagraphStyle], width: float, text) -> Table:
        marks = paper_rules.total_marks_for_groups([group])
        header = Table(
            [[Paragraph(f"Q.{index} &nbsp; {text(group.instruction)}", styles["group"]),
              Paragraph(f"[{_number(marks)} Marks]", styles["group_marks"])]],
            colWidths=[width * 0.75, width * 0.25],
        )
        header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                                    ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return header

    @staticmethod
    def _sub_question(label: str, spec: Any, question: Optional[Dict[str, Any]], styles: Dict[str, ParagraphStyle],
                      width: float, text) -> KeepTogether:
        body: List[Any] = [Paragraph(text(question["question_text"]) if question else "(no question)", styles["question"])]
        if question and question.get("question_type") == "MCQ":
            for letter, option in zip("ABCD", question.get("options", [])):
                body.append(Paragraph(f"{letter}) {text(option)}", styles["option"]))
        body.append(Paragraph(f"{text(spec.co)} &nbsp;|&nbsp; Unit {spec.unit_number}", styles["tag"]))

        row = Table(
            [[Paragraph(label, styles["label"]), body, Paragraph(f"[{_number(spec.marks)}]", styles["marks"])]],
            colWidths=[26, width - 26 - 52, 52],
        )
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0"))]))
        return KeepTogether(row)


paper_pdf_service = PaperPdfService()
