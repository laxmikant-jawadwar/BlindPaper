"""The faculty side of a paper's life: generate, preview and correct, regenerate, submit, delete, download."""

import httpx

from app.core.config import settings
from tests.conftest import auth_header, register_faculty, store_syllabus
from tests.groq_fake import completion, error_response, valid_questions
from tests.paper_helpers import MSE_GROUPS, config_data, group, sub

SERVICE_DOWN = httpx.ConnectError("no route")


def generate(client, faculty, syllabus_id, groups=None, **overrides):
    payload = config_data(groups or MSE_GROUPS, syllabus_id=syllabus_id, **overrides)
    return client.post("/api/papers/generate", json=payload, headers=faculty["headers"])


def make_draft(client, faculty, groq) -> dict:
    response = generate(client, faculty, store_syllabus(faculty))
    assert response.status_code == 201, response.text
    return response.json()


def edits_for(paper: dict, **changes) -> dict:
    """The paper's current questions, as an update request, with optional overrides per question."""
    questions = []
    for q in paper["questions"]:
        edit = {"sub_question_id": q["sub_question_id"], "question_text": q["question_text"], "options": q["options"], "answer": q["answer"]}
        edit.update(changes.get(q["sub_question_id"], {}))
        questions.append(edit)
    return {"questions": questions}


# ---- generating ----------------------------------------------------------------------------

def test_generating_needs_a_faculty_login(client, admin, faculty, groq):
    syllabus_id = store_syllabus(faculty)
    payload = config_data(MSE_GROUPS, syllabus_id=syllabus_id)

    assert client.post("/api/papers/generate", json=payload).status_code == 401
    assert client.post("/api/papers/generate", json=payload, headers=admin["headers"]).status_code == 403


def test_a_generated_paper_is_saved_as_a_draft_with_its_questions_and_checks(client, faculty, groq):
    response = generate(client, faculty, store_syllabus(faculty))

    assert response.status_code == 201
    paper = response.json()
    assert paper["status"] == "Draft"
    assert paper["course_name"] == "Operations Research" and paper["exam_type"] == "MSE"
    assert paper["faculty_name"] == "Prof. A" and paper["department"] == "Computer Science"
    assert paper["total_marks"] == 40
    assert [q["sub_question_id"] for q in paper["questions"]] == ["a1", "b1", "c1", "a2", "b2", "c2"]
    assert paper["analysis"]["status"] == "pass"
    assert paper["generation"]["model"] == settings.groq_model
    # a snapshot of the syllabus used, limited to the selected units, so the paper stands on its own
    assert [u["unit_number"] for u in paper["syllabus_snapshot"]["units"]] == [1, 2]
    assert paper["syllabus_snapshot"]["outcomes"][0]["code"] == "CO1"


def test_the_paper_is_stored_in_mongodb_under_the_faculty_member(client, faculty, groq, fake_mongo):
    paper = generate(client, faculty, store_syllabus(faculty)).json()

    stored = fake_mongo["blindpaper"]["papers"].find_one({})
    assert str(stored["_id"]) == paper["id"]
    assert stored["faculty_id"] == faculty["user"]["id"]
    assert stored["status"] == "Draft" and len(stored["questions"]) == 6


def test_a_syllabus_that_is_not_yours_cannot_be_used(client, faculty, other_faculty, groq):
    theirs = store_syllabus(other_faculty)

    assert generate(client, faculty, theirs).status_code == 404
    assert generate(client, faculty, "507f1f77bcf86cd799439099").status_code == 404


def test_an_inconsistent_configuration_is_explained_and_nothing_is_saved(client, faculty, groq, fake_mongo):
    groups = [group("g1", "Attempt any three", sub("a", unit=3), sub("b"))]  # unit 3 not selected; asks for 3 of 2

    response = generate(client, faculty, store_syllabus(faculty), groups=groups)

    assert response.status_code == 422
    problems = response.json()["problems"]
    assert any("Unit 3" in p for p in problems) and any("Attempt any three" in p for p in problems)
    assert fake_mongo["blindpaper"]["papers"].count_documents({}) == 0
    assert groq.requests == []  # no Groq call is spent on a configuration that cannot work


def test_a_failed_generation_is_reported_and_nothing_is_saved(client, faculty, groq, fake_mongo):
    groq.responses[:] = [error_response(500), error_response(503)]

    response = generate(client, faculty, store_syllabus(faculty))

    assert response.status_code == 502
    assert "could not generate" in response.json()["detail"].lower()
    assert fake_mongo["blindpaper"]["papers"].count_documents({}) == 0


def test_a_rate_limited_generation_tells_the_faculty_how_long_to_wait(client, faculty, groq):
    groq.responses[:] = [error_response(429, headers={"retry-after": "20"}), error_response(429, headers={"retry-after": "35"})]

    response = generate(client, faculty, store_syllabus(faculty))

    assert response.status_code == 429
    assert response.headers["retry-after"] == "20"
    assert "20 seconds" in response.json()["detail"]


def test_generation_without_an_api_key_is_a_clear_503(client, faculty, monkeypatch):
    from app.services.paper_generation_service import paper_generation_service

    monkeypatch.setattr(paper_generation_service, "_client_factory", None)
    monkeypatch.setattr(settings, "groq_api_key", None)

    response = generate(client, faculty, store_syllabus(faculty))

    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


# ---- reading -------------------------------------------------------------------------------

def test_faculty_only_see_their_own_papers(client, faculty, other_faculty, groq):
    mine = make_draft(client, faculty, groq)
    groq.responses.append(completion(valid_questions()))
    theirs = make_draft(client, other_faculty, groq)

    listed = client.get("/api/papers", headers=faculty["headers"]).json()
    assert [p["id"] for p in listed] == [mine["id"]]
    assert "questions" not in listed[0]  # the list rows are summaries

    assert client.get(f"/api/papers/{mine['id']}", headers=faculty["headers"]).status_code == 200
    assert client.get(f"/api/papers/{theirs['id']}", headers=faculty["headers"]).status_code == 404


def test_papers_can_be_listed_by_status(client, faculty, groq):
    draft = make_draft(client, faculty, groq)
    groq.responses.append(completion(valid_questions()))
    submitted = make_draft(client, faculty, groq)
    client.post(f"/api/papers/{submitted['id']}/submit", headers=faculty["headers"])

    pending = client.get("/api/papers", params={"status": "Pending Approval"}, headers=faculty["headers"]).json()
    drafts = client.get("/api/papers", params={"status": "Draft"}, headers=faculty["headers"]).json()

    assert [p["id"] for p in pending] == [submitted["id"]]
    assert [p["id"] for p in drafts] == [draft["id"]]


def test_the_paper_endpoints_are_for_faculty_only(client, admin):
    assert client.get("/api/papers", headers=admin["headers"]).status_code == 403
    assert client.get("/api/papers").status_code == 401


# ---- correcting ----------------------------------------------------------------------------

def test_a_draft_can_be_corrected_and_is_checked_again(client, faculty, groq):
    paper = make_draft(client, faculty, groq)

    response = client.put(
        f"/api/papers/{paper['id']}",
        json=edits_for(paper, b1={"question_text": "Describe the history of the Roman empire and its emperors."}),
        headers=faculty["headers"],
    )

    assert response.status_code == 200
    updated = response.json()
    assert next(q for q in updated["questions"] if q["sub_question_id"] == "b1")["question_text"].startswith("Describe the history")
    assert updated["analysis"]["status"] == "warnings"  # the edit made Q1b) look off-syllabus
    assert client.get(f"/api/papers/{paper['id']}", headers=faculty["headers"]).json()["questions"] == updated["questions"]


def test_a_correction_cannot_change_the_type_of_a_question(client, faculty, groq):
    paper = make_draft(client, faculty, groq)

    updated = client.put(
        f"/api/papers/{paper['id']}", json=edits_for(paper, b1={"options": ["x", "y", "z", "w"], "answer": "A"}), headers=faculty["headers"]
    ).json()

    b1 = next(q for q in updated["questions"] if q["sub_question_id"] == "b1")
    assert b1["question_type"] == "Descriptive" and b1["options"] == [] and b1["answer"] == ""


def test_a_correction_for_an_unknown_question_is_rejected(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    body = edits_for(paper)
    body["questions"][0]["sub_question_id"] = "zzz"

    assert client.put(f"/api/papers/{paper['id']}", json=body, headers=faculty["headers"]).status_code == 422


def test_a_paper_waiting_for_approval_can_no_longer_be_edited(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"])

    response = client.put(f"/api/papers/{paper['id']}", json=edits_for(paper), headers=faculty["headers"])

    assert response.status_code == 409
    assert "Pending Approval" in response.json()["detail"]


def test_a_draft_can_be_regenerated_from_the_same_configuration(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    fresh = valid_questions()
    fresh[1]["question_text"] = "Explain how the graphical method finds the optimal point of a linear programming problem."
    groq.responses.append(completion(fresh))

    response = client.post(f"/api/papers/{paper['id']}/regenerate", headers=faculty["headers"])

    assert response.status_code == 200
    again = response.json()
    assert again["id"] == paper["id"] and again["status"] == "Draft"
    assert next(q for q in again["questions"] if q["sub_question_id"] == "b1")["question_text"].startswith("Explain how the graphical")


# ---- submitting ----------------------------------------------------------------------------

def test_submitting_moves_a_draft_to_pending_approval_with_the_faculty_and_department(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    client.put("/api/auth/me", json={"department": "Electronics"}, headers=faculty["headers"])

    response = client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"])

    assert response.status_code == 200
    submitted = response.json()
    assert submitted["status"] == "Pending Approval"
    assert submitted["submitted_at"]
    assert submitted["department"] == "Electronics"  # the department at the time of submission
    assert submitted["faculty_name"] == "Prof. A"


def test_a_paper_that_fails_its_checks_cannot_be_submitted(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    broken = edits_for(paper, a1={"options": ["only", "two"], "answer": "A"})
    client.put(f"/api/papers/{paper['id']}", json=broken, headers=faculty["headers"])

    response = client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"])

    assert response.status_code == 422
    assert "Q1a)" in response.json()["detail"]
    assert client.get(f"/api/papers/{paper['id']}", headers=faculty["headers"]).json()["status"] == "Draft"


def test_a_paper_cannot_be_submitted_twice(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"])

    assert client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"]).status_code == 409


# ---- deleting ------------------------------------------------------------------------------

def test_a_draft_can_be_deleted_but_a_submitted_paper_cannot(client, faculty, groq):
    draft = make_draft(client, faculty, groq)
    groq.responses.append(completion(valid_questions()))
    submitted = make_draft(client, faculty, groq)
    client.post(f"/api/papers/{submitted['id']}/submit", headers=faculty["headers"])

    assert client.delete(f"/api/papers/{draft['id']}", headers=faculty["headers"]).status_code == 200
    assert client.get(f"/api/papers/{draft['id']}", headers=faculty["headers"]).status_code == 404
    assert client.delete(f"/api/papers/{submitted['id']}", headers=faculty["headers"]).status_code == 409


def test_someone_elses_paper_cannot_be_changed(client, faculty, other_faculty, groq):
    paper = make_draft(client, faculty, groq)
    intruder = other_faculty["headers"]

    assert client.put(f"/api/papers/{paper['id']}", json=edits_for(paper), headers=intruder).status_code == 404
    assert client.post(f"/api/papers/{paper['id']}/submit", headers=intruder).status_code == 404
    assert client.delete(f"/api/papers/{paper['id']}", headers=intruder).status_code == 404


# ---- regenerating one question -------------------------------------------------------------------

NEW_B1 = "Describe how the graphical method locates the optimal corner point of a linear programming problem."


def regenerate_question(client, faculty, paper_id, question_id="b1", headers=None):
    return client.post(f"/api/papers/{paper_id}/questions/{question_id}/regenerate", headers=headers or faculty["headers"])


def new_answer(slot_id="b1", text=NEW_B1, **extra):
    return completion([{"slot_id": slot_id, "question_text": text, "options": extra.get("options", []), "answer": extra.get("answer", "")}])


def test_one_question_can_be_regenerated_and_the_others_stay_exactly_as_they_were(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    before = {q["sub_question_id"]: q for q in paper["questions"]}
    groq.responses.append(new_answer())

    response = regenerate_question(client, faculty, paper["id"])

    assert response.status_code == 200
    after = {q["sub_question_id"]: q for q in response.json()["questions"]}
    assert after["b1"]["question_text"] == NEW_B1 and after["b1"]["question_text"] != before["b1"]["question_text"]
    assert {k: v for k, v in after.items() if k != "b1"} == {k: v for k, v in before.items() if k != "b1"}
    assert response.json()["status"] == "Draft"
    prompt = groq.requests[-1]["body"]["messages"][-1]["content"]
    assert before["b1"]["question_text"] in prompt  # told to write something different from the old one
    assert '"slot_id": "a1"' not in prompt  # only this question was asked for


def test_a_regenerated_mcq_stays_an_mcq_with_new_options(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    groq.responses.append(
        new_answer("a1", "Which statement about duality in linear programming is correct?", options=["Opt one", "Opt two", "Opt three", "Opt four"], answer="C")
    )

    updated = regenerate_question(client, faculty, paper["id"], "a1").json()

    a1 = next(q for q in updated["questions"] if q["sub_question_id"] == "a1")
    assert a1["question_type"] == "MCQ" and a1["options"] == ["Opt one", "Opt two", "Opt three", "Opt four"] and a1["answer"] == "C"
    assert updated["analysis"]["status"] in ("pass", "warnings")  # the checks were run again


def test_saved_corrections_to_other_questions_survive_regenerating_one(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    edit = {"questions": [{"sub_question_id": "c2", "question_text": "A faculty-corrected numerical problem about the economic order quantity.", "options": [], "answer": ""}]}
    client.put(f"/api/papers/{paper['id']}", json=edit, headers=faculty["headers"])
    groq.responses.append(new_answer())

    updated = regenerate_question(client, faculty, paper["id"]).json()

    c2 = next(q for q in updated["questions"] if q["sub_question_id"] == "c2")
    assert c2["question_text"] == "A faculty-corrected numerical problem about the economic order quantity."


def test_a_paper_waiting_for_approval_cannot_have_a_question_regenerated(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"])

    response = regenerate_question(client, faculty, paper["id"])

    assert response.status_code == 409 and "Pending Approval" in response.json()["detail"]


def test_regenerating_a_question_that_is_not_in_the_paper_is_a_404(client, faculty, groq):
    paper = make_draft(client, faculty, groq)

    assert regenerate_question(client, faculty, paper["id"], "no-such-question").status_code == 404


def test_someone_elses_paper_cannot_have_a_question_regenerated(client, faculty, other_faculty, groq):
    paper = make_draft(client, faculty, groq)

    assert regenerate_question(client, faculty, paper["id"], headers=other_faculty["headers"]).status_code == 404


def test_the_admin_cannot_regenerate_questions(client, faculty, admin, groq):
    paper = make_draft(client, faculty, groq)

    assert regenerate_question(client, faculty, paper["id"], headers=admin["headers"]).status_code == 403


def test_a_failed_question_regeneration_is_reported_and_the_paper_is_unchanged(client, faculty, groq):
    paper = make_draft(client, faculty, groq)
    groq.responses[:] = [error_response(500), error_response(503)]

    response = regenerate_question(client, faculty, paper["id"])

    assert response.status_code == 502
    assert client.get(f"/api/papers/{paper['id']}", headers=faculty["headers"]).json()["questions"] == paper["questions"]
