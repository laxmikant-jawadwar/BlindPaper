"""Builders shared by the paper tests: a template, a configuration and a stored syllabus."""

from app.schemas.paper import PaperConfig


def sub(slot_id: str, marks: float = 10, co: str = "CO1", unit: int = 1, description: str = "") -> dict:
    return {"id": slot_id, "co": co, "marks": marks, "unit_number": unit, "description": description}


def group(group_id: str, instruction: str, *subs: dict) -> dict:
    return {"id": group_id, "instruction": instruction, "sub_questions": list(subs)}


def config_data(groups: list[dict], **overrides) -> dict:
    data = {
        "syllabus_id": "507f1f77bcf86cd799439011",
        "course_name": "Operations Research",
        "course_code": "UCBEM0404",
        "year": "Third Year",
        "semester": "Semester 5",
        "exam_type": "MSE",
        "difficulty": "Balanced",
        "question_types": ["MCQ", "Descriptive", "Numerical"],
        "selected_units": [1, 2],
        "groups": groups,
    }
    return {**data, **overrides}


def config(groups: list[dict], **overrides) -> PaperConfig:
    return PaperConfig(**config_data(groups, **overrides))


# The default MSE template: two groups of three sub-questions, "attempt any two"
MSE_GROUPS = [
    group("g1", "Attempt any two", sub("a1"), sub("b1"), sub("c1")),
    group("g2", "Attempt any two", sub("a2", co="CO2", unit=2), sub("b2", co="CO2", unit=2), sub("c2", co="CO2", unit=2)),
]

# A syllabus as stored in MongoDB (shortened from the Operations Research sample)
SYLLABUS = {
    "id": "507f1f77bcf86cd799439011",
    "subject_name": "Operations Research",
    "course_code": "UCBEM0404",
    "course_description": "Operations Research is the study of Optimization techniques.",
    "course_outcomes": [
        {"code": "CO1", "description": "Demonstrate essential operations research modelling tools.", "blooms_level": 2, "blooms_descriptor": "Understand"},
        {"code": "CO2", "description": "Make use of Course knowledge to solve LPP and Queuing problems.", "blooms_level": 3, "blooms_descriptor": "Apply"},
        {"code": "CO3", "description": "Analyze the concept of LPP.", "blooms_level": 4, "blooms_descriptor": "Analyze"},
        {"code": "CO4", "description": "Choose the appropriate models.", "blooms_level": 5, "blooms_descriptor": "Evaluate"},
    ],
    "course_content": [
        {"unit_number": 1, "unit_name": "Linear Programming Problems", "topics": ["Graphical method", "Simplex method", "Concept of duality in LPP"]},
        {"unit_number": 2, "unit_name": "Inventory Control", "topics": ["Concept of inventory costs", "Concept of EOQ", "EOQ Models"]},
        {"unit_number": 3, "unit_name": "Network Models", "topics": ["CPM and PERT", "Determination of critical paths"]},
    ],
    "extracted_text": "Operations Research syllabus text",
}
