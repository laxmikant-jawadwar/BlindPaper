"""
PDF generation service for BlindPaper.
Generates clean, professional, publication-ready examination question paper PDFs using ReportLab.
"""

import io
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.export import PaperExportRequest


class PDFExportError(Exception):
    """Raised when PDF generation fails."""
    pass


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that accurately computes and prints 'Page X of Y' page numbers
    along with a clean running footer.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[dict] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_footer(self, total_pages: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))  # Slate grey

        # Running bottom separator line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 36, 595.27 - 40, 36)

        # Left footer watermark
        self.drawString(40, 24, "BlindPaper Examination System — Confidential Question Paper")

        # Right footer page counter
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(595.27 - 40, 24, page_str)
        self.restoreState()


class PDFExportService:
    """Service responsible for formatting and generating examination paper PDFs."""

    def generate_question_paper_pdf(self, request: PaperExportRequest) -> bytes:
        """
        Generate an in-memory PDF for the requested question paper.
        Returns raw bytes suitable for streaming or file download.
        """
        buffer = io.BytesIO()

        # A4: 595.27 x 841.89 points
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=48,
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        college_style = ParagraphStyle(
            "CollegeHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            alignment=1,  # Centered
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=3,
        )

        exam_style = ParagraphStyle(
            "ExamHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=2,
        )

        subject_style = ParagraphStyle(
            "SubjectHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=1,
            textColor=colors.HexColor("#1E3A8A"),  # Deep navy blue
            spaceAfter=6,
        )

        meta_label_style = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )

        meta_val_style = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A"),
        )

        instr_title_style = ParagraphStyle(
            "InstrTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=2,
        )

        instr_item_style = ParagraphStyle(
            "InstrItem",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#475569"),
        )

        q_num_style = ParagraphStyle(
            "QNum",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0F172A"),
            alignment=0,
        )

        q_text_style = ParagraphStyle(
            "QText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#0F172A"),
        )

        q_meta_style = ParagraphStyle(
            "QMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#64748B"),
        )

        marks_style = ParagraphStyle(
            "QMarks",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            alignment=2,  # Right-aligned
            textColor=colors.HexColor("#1E3A8A"),
        )

        end_text_style = ParagraphStyle(
            "EndText",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            alignment=1,
            textColor=colors.HexColor("#64748B"),
        )

        story: List[object] = []

        # 1. College Header (Optional)
        if request.college_name:
            story.append(Paragraph(request.college_name.upper(), college_style))

        # 2. Exam Name (Optional or Subject-based)
        if request.exam_name:
            story.append(Paragraph(request.exam_name.upper(), exam_style))

        # 3. Subject Name
        story.append(Paragraph(f"SUBJECT: {request.subject_name.upper()}", subject_style))

        # 4. Metadata Details Grid (Paper Code, Semester, Duration, Max Marks)
        meta_data = [
            [
                Paragraph(f"<b>Paper Code:</b> {request.paper_code or 'N/A'}", meta_label_style),
                Paragraph(f"<b>Semester:</b> {request.semester or 'N/A'}", meta_label_style),
                Paragraph(f"<b>Max. Marks:</b> {request.total_marks}", meta_label_style),
            ],
            [
                Paragraph(f"<b>Time Allowed:</b> {request.duration or '3 Hours'}", meta_label_style),
                Paragraph(f"<b>Total Questions:</b> {request.question_count}", meta_label_style),
                Paragraph("<b>Passing Marks:</b> As per rules", meta_label_style),
            ],
        ]

        # Printable width: 595.27 - 80 = 515.27
        meta_table = Table(meta_data, colWidths=[170, 175, 170])
        meta_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(meta_table)

        # Thick separating rule
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#0F172A"), spaceAfter=6))

        # 5. Instructions Section (if provided or standard)
        instructions = request.instructions or [
            "Attempt all questions. Every question carries the marks indicated against it.",
            "Assume suitable missing data if necessary, and state the assumptions clearly.",
            "Draw neat and labeled diagrams wherever applicable.",
        ]

        instr_elements = [
            Paragraph("<b>GENERAL INSTRUCTIONS:</b>", instr_title_style)
        ]
        for idx, instr in enumerate(instructions, start=1):
            instr_elements.append(Paragraph(f"{idx}. {instr}", instr_item_style))

        instr_box = Table([[instr_elements]], colWidths=[515])
        instr_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(instr_box)
        story.append(Spacer(1, 10))

        # 6. Questions Section
        table_rows = []
        # Header row
        header_row = [
            Paragraph("<b>Q. No.</b>", meta_label_style),
            Paragraph("<b>Question Description</b>", meta_label_style),
            Paragraph("<b>Marks</b>", ParagraphStyle("HdrMarks", parent=meta_label_style, alignment=2)),
        ]
        table_rows.append(header_row)

        for q in request.questions:
            q_num_p = Paragraph(f"<b>Q.{q.question_id}</b>", q_num_style)
            
            # Question text + metadata details
            q_content = [
                Paragraph(q.question_text, q_text_style),
                Spacer(1, 2),
                Paragraph(f"[Unit: {q.unit_or_topic} &nbsp;|&nbsp; Type: {q.question_type} &nbsp;|&nbsp; Difficulty: {q.difficulty.capitalize()}]", q_meta_style),
            ]
            
            marks_p = Paragraph(f"<b>[{q.marks}]</b>", marks_style)
            table_rows.append([q_num_p, q_content, marks_p])

        # Printable width: 515 total
        q_table = Table(table_rows, colWidths=[40, 415, 60], repeatRows=1)
        q_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                    ("TOPPADDING", (0, 0), (-1, 0), 4),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#94A3B8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ]
            )
        )
        story.append(q_table)

        # 7. End of Paper Indicator
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8"), spaceAfter=8))
        story.append(
            Paragraph(
                f"— END OF QUESTION PAPER (TOTAL MARKS: {request.total_marks}) —",
                end_text_style,
            )
        )

        try:
            doc.build(story, canvasmaker=NumberedCanvas)
            return buffer.getvalue()
        except Exception as e:
            raise PDFExportError(f"Failed to generate question paper PDF: {str(e)}") from e


# Singleton PDF export service
pdf_export_service = PDFExportService()
