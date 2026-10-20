"""
Rule-based structuring of real university syllabus layouts (application flow, step 3).

Only these parts of a syllabus are kept: course name and code, course description,
course outcomes and the course contents (unit number, unit name, topics). Everything
else (prerequisites, objectives, CO-PO grid, assessment, textbooks, hours) is dropped.

The text fixtures are copied from what PyMuPDF produces for real syllabus PDFs; the
table fixtures have the shape pdfplumber returns for them.
"""

from pathlib import Path

import pytest

from app.services.syllabus_service import syllabus_service
from app.services.syllabus_structuring_service import syllabus_structuring_service

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample"
needs_sample_pdfs = pytest.mark.skipif(
    not (SAMPLE_DIR / "Syllabus.pdf").exists() or not (SAMPLE_DIR / "OR Syllabus.pdf").exists(),
    reason="sample syllabus PDFs are not present in the sample/ folder",
)

ACCOUNTING_TEXT = """\
Title of the Course: Financial and cost accounting.                 L   T  P  Credit

Course Code: UCBMM0441                                          3       -     -     3

Course Pre-Requisite: overview of business organizations and their operations.

Course Description: The course helps the students to know the necessary skills and knowledge
required in accounting practice

Course Learning Objectives:

    1.  Understand current accounting practices at basic level.
    2.  Differentiate between various cost and their behavior and overheads.


Course Outcomes:

 CO1  of   the  accounting  concepts  and   their  managerial      II       Understand
 CO4  To analyze and interpret financial statements.              IV       Analyze

CO-PO Mapping:

 CO   PO1  PO2  PO3  PO4   PO5  PO6  PO7  PO8  PO9  PO10  PO11  PO12  PSO1   PSO2


                                                                                4 | P a g e

Assessments:

Teacher Assessment:

MSE: Assessment is based on 50% of course content (Normally first three modules)

Course Contents:

Unit 1: Accounting Concept:                                               6 Hours

Introduction, Techniques and Conventions, Financial Statements- Understanding & Interpreting
Financial statements

Unit 2: Accounting Process:                                               10 Hours

Bookkeeping and Record Maintenance, Fundamental Principles and Double Entry, Journal, Ledger,
Trial Balance, Balance Sheet, Final Accounts, Cash Book and Subsidiary Books, Rectification of
Errors.

Unit 3: Financial Statements:                                              8 Hours

Form and Contents of Financial Statements, Analysing and Interpreting Financial Statements,
Accounting Standards., Class Discussion: Corporate Accounting Fraud- A Case Study of Satyam.

Unit 4: Cash Flow and Fund Flow Techniques:                               10 Hours

Introduction, how to prepare cash flow statement and funds flow statement, Difference between both
statements.

Unit 5: Costing Systems:                                                  4 Hours

Elements of Cost, Cost Behavior, Cost Allocation, OH Allocation,




                                                                                5 | P a g e

Unit 6: Company Accounts and Annual Reports:                              4 Hours

Audit Reports and Statutory Requirements, Director’s Report, Notes to accounts,  Pitfalls in
accounting.

Home Assignment:

    1.  Students must solve problems in accounting and learn to prepare Profit loss and Balance
        sheet.

Textbooks:

    1.  Robert N Anthony, David Hawkins, Kenneth Marchant, Accounting: Texts and Cases       ,
      McGraw-Hill.

References:

    1.  Pillai R.S.N.,Kala S.(2013). Principles and Practice of Management, S.Chand publication.
"""

OPERATIONS_RESEARCH_TEXT = """\
Course Code:      UCBEM0404                                L   T    P  Credit
Course Name:        Operations Research                                     3     0       -     3

Course Prerequsites:
Fundamentals of Mathematics and Basic functional areas of Engineering.

Course Description:
Operations Research is the study of Optimization techniques. OR has wide scope of applications in various fields
as it helps solve various Industry problems.

Course Objectives:
This course provides strong foundation for understanding the fundamental principles and laws of Operation
Research to understand Linear programming.

Course Contents:
Unit 1 Linear Programming Problems                                                   8 Hours
Introduction to OR, Origin of OR and its definition. Scope and Applications, Types of OR Models, Formulation of
linear programming problem (LPP), Graphical method, Simplex method, Artificial variable technique- Big M
method , concept of duality in LPP.


Unit 2 Inventory Control:                                                              6 Hours
Objectives of Inventory Control, Concept of inventory costs, Classification of Inventory Models, Concept of EOQ,
EOQ Models.

Unit 4 Transportation and Assignment Model                                             8 Hours
TP - Formulation, Balanced & unbalanced situations, Solution methods – NWCR, least cost and VAM, test for
optimality(MODI method).
AP - Examples, Definitions – decision variables, constraints, formulation, Balanced & unbalanced situations,
Solution method – Hungarian, test for optimality.


Unit 5 Queuing Theory                                                                8 Hours
Definitions – queue (waiting line), waiting costs, characteristics (arrival, queue, service discipline) of queuing
system, queue types (channel vs. phase). Classification of Queuing models, Kendall's notation for representing
Queuing models , M/M/1 Model.

Text Books:
1. S.D.Sharma (2012). Operations Research. KEDAR NATH
"""

# What pdfplumber returns for the outcome table and the CO-PO grid of such a syllabus
ACCOUNTING_TABLES = [
    [
        ["CO", "After the completion of the course the student should be able to", "Bloom’s Cognitive", ""],
        ["", "", "Level", "Descriptor"],
        ["CO1", "To create an awareness about the importance and usefulness of the accounting concepts and their managerial implications.", "II", "Understand"],
        ["CO2", "To develop an understanding of the financial statements and the underlying principles and learn to interpret financial statements.", "II", "Understand"],
        ["CO4", "To analyze and interpret financial statements.", "IV", "Analyze"],
    ],
    [
        ["CO", "PO1", "PO2", "PO3", "PO4", "PO5", "PO6"],
        ["CO1", "", "", "", "", "", "1"],
        ["CO2", "", "1", "", "", "", ""],
    ],
]

OPERATIONS_RESEARCH_TABLES = [
    [
        ["COs", "Upon completion of the course, students shall have ability to", "Blooms", "Descriptor"],
        ["CO1", "Demonstrate essential operations research modelling tools to solve the real- world business problems.", "II", "Understanding"],
        ["CO2", "Make use of Course knowledge to solve LPP.", "III", "Applying"],
        ["CO5", "Do something without a stated level.", "", "Evaluating"],
        ["CO6", "A row with no level at all.", "", ""],
    ],
]


def structure(text: str, tables=None, **kwargs):
    return syllabus_structuring_service.structure_syllabus_text(
        extracted_text=text, filename="syllabus.pdf", page_count=1, tables=tables, **kwargs
    )


def units_of(result):
    return result["course_content"]


def test_subject_and_course_code_come_from_the_title_block():
    result = structure(ACCOUNTING_TEXT)

    assert result["subject_name"] == "Financial and cost accounting"
    assert result["course_code"] == "UCBMM0441"


def test_subject_name_stops_at_the_column_gap():
    result = structure(OPERATIONS_RESEARCH_TEXT)

    assert result["subject_name"] == "Operations Research"
    assert result["course_code"] == "UCBEM0404"


def test_course_description_may_follow_its_label_on_the_same_line():
    result = structure(ACCOUNTING_TEXT)

    assert result["course_description"] == (
        "The course helps the students to know the necessary skills and knowledge required in accounting practice"
    )


def test_course_description_may_start_on_the_next_line_and_stops_at_the_next_heading():
    result = structure(OPERATIONS_RESEARCH_TEXT)

    assert result["course_description"] == (
        "Operations Research is the study of Optimization techniques. OR has wide scope of "
        "applications in various fields as it helps solve various Industry problems."
    )


def test_course_description_is_none_when_the_syllabus_has_none():
    assert structure("Unit 1: Stacks\nPush, Pop")["course_description"] is None


def test_units_have_a_number_a_name_and_no_hours():
    units = units_of(structure(ACCOUNTING_TEXT))

    assert [(u.unit_number, u.unit_name) for u in units] == [
        (1, "Accounting Concept"),
        (2, "Accounting Process"),
        (3, "Financial Statements"),
        (4, "Cash Flow and Fund Flow Techniques"),
        (5, "Costing Systems"),
        (6, "Company Accounts and Annual Reports"),
    ]
    assert not hasattr(units[0], "hours")


def test_unit_titles_without_a_colon_are_normalised_and_keep_their_own_numbers():
    units = units_of(structure(OPERATIONS_RESEARCH_TEXT))

    assert [(u.unit_number, u.unit_name) for u in units] == [
        (1, "Linear Programming Problems"),
        (2, "Inventory Control"),
        (4, "Transportation and Assignment Model"),
        (5, "Queuing Theory"),
    ]


def test_roman_numeral_unit_numbers_are_converted():
    units = units_of(structure("Course Contents:\nUnit II Trees\nBinary trees, Heaps\nUnit IV Graphs\nBFS, DFS"))

    assert [(u.unit_number, u.unit_name) for u in units] == [(2, "Trees"), (4, "Graphs")]


def test_wrapped_comma_separated_lines_become_individual_topics():
    unit2 = units_of(structure(ACCOUNTING_TEXT))[1]

    assert unit2.topics == [
        "Bookkeeping and Record Maintenance",
        "Fundamental Principles and Double Entry",
        "Journal",
        "Ledger",
        "Trial Balance",
        "Balance Sheet",
        "Final Accounts",
        "Cash Book and Subsidiary Books",
        "Rectification of Errors",
    ]


def test_sentences_in_a_topic_list_are_split_into_topics_and_start_with_a_capital():
    unit1 = units_of(structure(OPERATIONS_RESEARCH_TEXT))[0]

    assert unit1.topics == [
        "Introduction to OR",
        "Origin of OR and its definition",
        "Scope and Applications",
        "Types of OR Models",
        "Formulation of linear programming problem (LPP)",
        "Graphical method",
        "Simplex method",
        "Artificial variable technique- Big M method",
        "Concept of duality in LPP",
    ]


def test_commas_inside_parentheses_do_not_split_a_topic():
    unit5 = units_of(structure(OPERATIONS_RESEARCH_TEXT))[3]

    assert "Characteristics (arrival, queue, service discipline) of queuing system" in unit5.topics
    assert "Queue types (channel vs. phase)" in unit5.topics


def test_a_labelled_topic_is_kept_as_one_topic():
    unit3 = units_of(structure(ACCOUNTING_TEXT))[2]

    assert unit3.topics == [
        "Form and Contents of Financial Statements",
        "Analysing and Interpreting Financial Statements",
        "Accounting Standards",
        "Class Discussion: Corporate Accounting Fraud- A Case Study of Satyam",
    ]


def test_page_footers_and_sections_after_the_contents_are_not_topics():
    units = units_of(structure(ACCOUNTING_TEXT))

    assert units[4].topics == ["Elements of Cost", "Cost Behavior", "Cost Allocation", "OH Allocation"]
    assert units[5].topics == [
        "Audit Reports and Statutory Requirements",
        "Director’s Report",
        "Notes to accounts",
        "Pitfalls in accounting",
    ]


def test_sections_the_faculty_does_not_need_are_not_stored():
    result = structure(ACCOUNTING_TEXT, tables=ACCOUNTING_TABLES)
    stored = [result["course_description"]]
    stored += [o.description for o in result["course_outcomes"]]
    stored += [u.unit_name for u in units_of(result)] + [t for u in units_of(result) for t in u.topics]

    for unwanted in (
        "Understand current accounting practices",  # course learning objectives
        "overview of business organizations",  # prerequisite
        "Assessment is based",  # assessment scheme
        "Robert N Anthony",  # textbook
        "Pillai",  # reference
        "Students must solve",  # home assignment
        "P a g e",  # page footer
    ):
        assert not any(unwanted in text for text in stored), unwanted
    assert not {"objectives", "co_po_mapping", "prerequisites"} & set(result)


def test_course_outcomes_are_read_from_the_outcome_table_with_numeric_bloom_levels():
    outcomes = structure(ACCOUNTING_TEXT, tables=ACCOUNTING_TABLES)["course_outcomes"]

    assert [(o.code, o.blooms_level, o.blooms_descriptor) for o in outcomes] == [
        ("CO1", 2, "Understand"),
        ("CO2", 2, "Understand"),
        ("CO4", 4, "Analyze"),
    ]
    assert outcomes[0].description == (
        "To create an awareness about the importance and usefulness of the accounting concepts "
        "and their managerial implications."
    )


def test_the_co_po_grid_is_not_mistaken_for_course_outcomes():
    outcomes = structure(ACCOUNTING_TEXT, tables=ACCOUNTING_TABLES)["course_outcomes"]

    assert len(outcomes) == 3  # the two CO-PO rows (CO1, CO2) were not added again


def test_bloom_descriptors_are_normalised_and_wrapped_hyphens_are_closed():
    outcomes = structure(OPERATIONS_RESEARCH_TEXT, tables=OPERATIONS_RESEARCH_TABLES)["course_outcomes"]

    assert [(o.code, o.blooms_level, o.blooms_descriptor) for o in outcomes] == [
        ("CO1", 2, "Understand"),  # "Understanding" in the PDF
        ("CO2", 3, "Apply"),  # "Applying"
        ("CO5", 5, "Evaluate"),  # level taken from the descriptor when the number is missing
        ("CO6", None, None),
    ]
    assert outcomes[0].description.endswith("solve the real-world business problems.")


def test_there_are_no_outcomes_without_tables():
    assert structure(ACCOUNTING_TEXT)["course_outcomes"] == []


def test_status_is_structured_when_unit_headings_are_found():
    assert structure(ACCOUNTING_TEXT)["processing_status"] == "structured"


def test_status_is_extracted_and_content_empty_when_no_unit_headings_exist():
    result = structure("Some free text about nothing in particular.\nIt has no units at all.")

    assert result["processing_status"] == "extracted"
    assert result["course_content"] == []
    assert result["course_code"] is None


@needs_sample_pdfs
def test_sample_accounting_pdf_structures_end_to_end():
    pdf = (SAMPLE_DIR / "Syllabus.pdf").read_bytes()
    extracted = syllabus_service.extract_text_from_pdf_bytes(pdf, "Syllabus.pdf")

    result = structure(extracted["extracted_text"], tables=extracted["tables"])

    assert result["subject_name"] == "Financial and cost accounting"
    assert result["course_code"] == "UCBMM0441"
    assert result["course_description"] == (
        "The course helps the students to know the necessary skills and knowledge required in accounting practice"
    )
    assert [(o.code, o.blooms_level, o.blooms_descriptor) for o in result["course_outcomes"]] == [
        ("CO1", 2, "Understand"),
        ("CO2", 2, "Understand"),
        ("CO3", 2, "Understand"),
        ("CO4", 4, "Analyze"),
    ]
    assert result["course_outcomes"][3].description == "To analyze and interpret financial statements."
    assert [(u.unit_number, u.unit_name, len(u.topics)) for u in units_of(result)] == [
        (1, "Accounting Concept", 3),
        (2, "Accounting Process", 9),
        (3, "Financial Statements", 4),
        (4, "Cash Flow and Fund Flow Techniques", 3),
        (5, "Costing Systems", 4),
        (6, "Company Accounts and Annual Reports", 4),
    ]
    assert result["processing_status"] == "structured"


@needs_sample_pdfs
def test_sample_operations_research_pdf_structures_end_to_end():
    pdf = (SAMPLE_DIR / "OR Syllabus.pdf").read_bytes()
    extracted = syllabus_service.extract_text_from_pdf_bytes(pdf, "OR Syllabus.pdf")

    result = structure(extracted["extracted_text"], tables=extracted["tables"])
    units = units_of(result)

    assert result["subject_name"] == "Operations Research"
    assert result["course_code"] == "UCBEM0404"
    assert result["course_description"].startswith("Operations Research is the study of Optimization techniques.")
    assert result["course_description"].endswith("to obtain optimal solutions to various problems.")
    assert "Fundamentals of Mathematics" not in result["course_description"]  # prerequisite
    assert "strong foundation" not in result["course_description"]  # objectives
    assert [(o.code, o.blooms_level, o.blooms_descriptor) for o in result["course_outcomes"]] == [
        ("CO1", 2, "Understand"),
        ("CO2", 3, "Apply"),
        ("CO3", 4, "Analyze"),
        ("CO4", 5, "Evaluate"),
    ]
    assert result["course_outcomes"][0].description == (
        "Demonstrate essential operations research modelling tools to solve the real-world business problems."
    )
    assert [(u.unit_number, u.unit_name) for u in units] == [
        (1, "Linear Programming Problems"),
        (2, "Inventory Control"),
        (3, "Network Models"),
        (4, "Transportation and Assignment Model"),
        (5, "Queuing Theory"),
        (6, "Game Theory"),
    ]
    # The unit content must land under the right title (the PDF layout scrambles reading order).
    assert "Simplex method" in units[0].topics
    assert "Concept of EOQ" in units[1].topics
    assert any("CPM and PERT" in topic for topic in units[2].topics)
    assert any("NWCR" in topic for topic in units[3].topics)
    assert any("Kendall's notation" in topic for topic in units[4].topics)
    assert "Dominance theory" in units[5].topics
