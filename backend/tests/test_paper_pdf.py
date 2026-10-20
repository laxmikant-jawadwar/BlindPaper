"""The printable question paper."""

import pymupdf

from app.services.paper_pdf_service import paper_pdf_service
from tests.conftest import store_syllabus
from tests.groq_fake import completion, valid_questions
from tests.paper_helpers import MSE_GROUPS, config_data


def pdf_text(pdf_bytes: bytes) -> str:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def make_paper(client, faculty, groq, questions=None) -> dict:
    groq.responses[:] = [completion(questions or valid_questions())]
    payload = config_data(MSE_GROUPS, syllabus_id=store_syllabus(faculty))
    return client.post("/api/papers/generate", json=payload, headers=faculty["headers"]).json()


def test_the_pdf_has_the_header_instructions_questions_marks_and_options(client, faculty, groq):
    pdf = paper_pdf_service.generate(make_paper(client, faculty, groq))

    assert pdf.startswith(b"%PDF-")
    text = pdf_text(pdf)
    for expected in (
        "MID SEMESTER EXAMINATION",
        "Operations Research",
        "UCBEM0404",
        "Third Year",
        "Semester 5",
        "Maximum Marks: 40",
        "Attempt any two",
        "Explain the graphical method",  # a question
        "[10]",  # its marks
        "It moves from one vertex",  # an MCQ option
    ):
        assert expected in text, expected


def test_the_answer_key_is_not_printed_on_the_paper(client, faculty, groq):
    text = pdf_text(paper_pdf_service.generate(make_paper(client, faculty, groq)))

    assert "Correct answer" not in text and "Answer:" not in text


def test_question_text_with_angle_brackets_and_ampersands_does_not_break_the_pdf(client, faculty, groq):
    questions = valid_questions()
    questions[2]["question_text"] = "Maximize Z = 3x1 + 5x2 subject to x1 <= 4 & 2x2 <= 12 and <b>x1</b> >= 0 in a <unclosed tag."

    text = pdf_text(paper_pdf_service.generate(make_paper(client, faculty, groq, questions)))

    assert "x1 <= 4 & 2x2 <= 12" in text and "<unclosed tag" in text


def test_greek_letters_subscripts_currency_and_maths_symbols_print_exactly_as_written(client, faculty, groq):
    questions = valid_questions()
    questions[1]["question_text"] = (
        "In an M/M/1 queue the arrival rate λ = 4 per hour and the service rate μ = 6 per hour, so "
        "ρ ≤ 1. Maximise Z = 3x₁ + 5x₂ with x₁ ≥ 0 and x₁ ≠ x₂; the cost is ₹ 1,200, "
        "√(2DS/H) → EOQ, ∑ xᵢ = ∞, in the non‑blocking real‑world case."
    )

    text = pdf_text(paper_pdf_service.generate(make_paper(client, faculty, groq, questions)))

    for expected in ("λ = 4", "μ = 6", "ρ ≤ 1", "3x₁ + 5x₂", "x₁ ≥ 0", "x₁ ≠ x₂",
                     "₹ 1,200", "√(2DS/H) → EOQ", "∑", "∞", "non-blocking real-world"):
        assert expected in text, expected  # the non-breaking hyphen is normalised to a normal one
    for broken in ("�", "■", "‑"):
        assert broken not in text


def test_the_paper_uses_the_bundled_font_whatever_the_machine_has():
    from app.services.paper_pdf_service import load_fonts

    fonts = load_fonts()

    assert (fonts.regular, fonts.bold, fonts.italic) == ("DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Oblique")
    assert fonts.unicode


def test_a_character_no_font_can_print_becomes_a_question_mark_not_a_blank_box(client, faculty, groq):
    questions = valid_questions()
    questions[1]["question_text"] = "Explain the graphical method 😀 for a linear programming problem."

    text = " ".join(pdf_text(paper_pdf_service.generate(make_paper(client, faculty, groq, questions))).split())

    assert "graphical method ? for a linear programming problem." in text  # (long lines wrap in the PDF)


def test_without_a_unicode_font_symbols_are_spelled_out_instead_of_lost(client, faculty, groq):
    from app.services.paper_pdf_service import Fonts

    questions = valid_questions()
    questions[1]["question_text"] = "Arrival rate λ and service rate μ with ρ ≤ 1, so x ≠ 0 and x ≥ 5."
    paper = make_paper(client, faculty, groq, questions)

    text = pdf_text(paper_pdf_service.generate(paper, fonts=Fonts("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", unicode=False)))

    assert "Arrival rate lambda and service rate mu with rho <= 1, so x != 0 and x >= 5." in text


def test_the_end_semester_paper_is_titled_accordingly(client, faculty, groq):
    paper = make_paper(client, faculty, groq)
    paper["exam_type"] = "ESE"

    assert "END SEMESTER EXAMINATION" in pdf_text(paper_pdf_service.generate(paper))
