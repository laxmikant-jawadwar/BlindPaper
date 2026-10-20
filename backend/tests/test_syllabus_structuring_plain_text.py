"""The plain 'Unit N: Title' text format is structured into units and topics."""

from app.services.syllabus_structuring_service import syllabus_structuring_service


def test_structuring_service_reads_units_and_topics():
    """Verify the structuring service splits plain 'Unit N: Title' text into units and topics."""
    raw_text = (
        "Course: Operating Systems\n\n"
        "Unit 1: Process Management\n"
        "Explain process states and life cycles.\n"
        "Implement CPU scheduling algorithms.\n\n"
        "Unit 2: Memory Management\n"
        "Evaluate page replacement policies.\n"
        "Virtual memory basics."
    )

    result = syllabus_structuring_service.structure_syllabus_text(
        extracted_text=raw_text,
        filename="os_syllabus.pdf",
        page_count=2,
    )

    assert result["subject_name"] == "Operating Systems"
    units = result["course_content"]
    assert [(u.unit_number, u.unit_name) for u in units] == [
        (1, "Process Management"),
        (2, "Memory Management"),
    ]
    assert units[0].topics == [
        "Explain process states and life cycles",
        "Implement CPU scheduling algorithms",
    ]
    assert units[1].topics == ["Evaluate page replacement policies", "Virtual memory basics"]
