"""The admin side: dashboard numbers, the review queue, approving and rejecting, faculty and departments."""

import time

from tests.conftest import register_faculty, auth_header, store_syllabus
from tests.groq_fake import completion, valid_questions
from tests.paper_helpers import MSE_GROUPS, config_data


def create_paper(client, faculty, groq, submit=True, **overrides) -> dict:
    """Generate (and normally submit) a paper for this faculty member."""
    groq.responses.append(completion(valid_questions()))
    payload = config_data(MSE_GROUPS, syllabus_id=store_syllabus(faculty), **overrides)
    response = client.post("/api/papers/generate", json=payload, headers=faculty["headers"])
    assert response.status_code == 201, response.text
    paper = response.json()
    if submit:
        time.sleep(0.002)  # keep the submission times distinct so ordering is deterministic
        paper = client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"]).json()
    return paper


def approve(client, admin, paper_id):
    return client.post(f"/api/admin/papers/{paper_id}/approve", headers=admin["headers"])


def reject(client, admin, paper_id, reason="Unit 2 questions are too easy for an end semester paper."):
    return client.post(f"/api/admin/papers/{paper_id}/reject", json={"reason": reason}, headers=admin["headers"])


def test_admin_endpoints_are_for_the_admin_only(client, faculty):
    for path in ("/api/admin/stats", "/api/admin/papers", "/api/admin/faculty", "/api/admin/departments"):
        assert client.get(path).status_code == 401, path
        assert client.get(path, headers=faculty["headers"]).status_code == 403, path


def test_the_admin_sees_submitted_papers_but_never_drafts(client, admin, faculty, groq):
    draft = create_paper(client, faculty, groq, submit=False)
    submitted = create_paper(client, faculty, groq)

    listed = client.get("/api/admin/papers", headers=admin["headers"]).json()

    assert [p["id"] for p in listed] == [submitted["id"]]
    assert client.get(f"/api/admin/papers/{draft['id']}", headers=admin["headers"]).status_code == 404
    assert client.get("/api/admin/stats", headers=admin["headers"]).json()["total"] == 1


def test_the_dashboard_counts_papers_by_status_and_by_department(client, admin, faculty, other_faculty, groq):
    pending = create_paper(client, faculty, groq)
    accepted = create_paper(client, faculty, groq)
    rejected = create_paper(client, other_faculty, groq)
    create_paper(client, other_faculty, groq, submit=False)  # a draft is not counted
    approve(client, admin, accepted["id"])
    reject(client, admin, rejected["id"])

    stats = client.get("/api/admin/stats", headers=admin["headers"]).json()

    assert (stats["total"], stats["pending"], stats["approved"], stats["rejected"]) == (3, 1, 1, 1)
    by_department = {row["department"]: row for row in stats["departments"]}
    assert list(by_department) == ["Computer Science", "Mechanical", "Civil", "Electrical", "Electronics", "Information Technology"]
    assert (by_department["Computer Science"]["total"], by_department["Computer Science"]["pending"], by_department["Computer Science"]["approved"]) == (2, 1, 1)
    assert (by_department["Mechanical"]["total"], by_department["Mechanical"]["rejected"]) == (1, 1)
    assert by_department["Civil"]["total"] == 0
    assert pending["status"] == "Pending Approval"


def test_the_department_filter_narrows_the_numbers_and_the_summary(client, admin, faculty, other_faculty, groq):
    create_paper(client, faculty, groq)
    create_paper(client, other_faculty, groq)

    stats = client.get("/api/admin/stats", params={"department": "Mechanical"}, headers=admin["headers"]).json()

    assert (stats["total"], stats["pending"]) == (1, 1)
    assert [row["department"] for row in stats["departments"]] == ["Mechanical"]


def test_papers_can_be_filtered_by_status_department_and_search_and_come_newest_first(client, admin, faculty, other_faculty, groq):
    first = create_paper(client, faculty, groq)
    second = create_paper(client, other_faculty, groq, course_name="Engineering Mechanics", course_code="ME201")
    approve(client, admin, first["id"])

    def ids(**params):
        return [p["id"] for p in client.get("/api/admin/papers", params=params, headers=admin["headers"]).json()]

    assert ids() == [second["id"], first["id"]]  # most recently submitted first
    assert ids(status="Pending Approval") == [second["id"]]
    assert ids(status="Approved") == [first["id"]]
    assert ids(department="Computer Science") == [first["id"]]
    assert ids(q="mechanics") == [second["id"]]
    assert ids(q="Prof. A") == [first["id"]]


def test_a_submitted_paper_shows_its_details_questions_and_review_analysis(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)

    detail = client.get(f"/api/admin/papers/{paper['id']}", headers=admin["headers"]).json()

    assert (detail["course_name"], detail["course_code"], detail["exam_type"]) == ("Operations Research", "UCBEM0404", "MSE")
    assert (detail["faculty_name"], detail["department"], detail["status"]) == ("Prof. A", "Computer Science", "Pending Approval")
    assert detail["submitted_at"] and len(detail["questions"]) == 6
    analysis = detail["analysis"]
    assert analysis["total_marks"] == 40 and analysis["marks_by_unit"] and analysis["question_relevance"]
    assert analysis["status"] == "pass"


def test_approving_a_pending_paper_records_who_decided_and_when(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)

    response = approve(client, admin, paper["id"])

    assert response.status_code == 200
    approved = response.json()
    assert approved["status"] == "Approved" and approved["reviewed_at"] and approved["rejection_reason"] is None
    assert approved["review_history"][-1]["status"] == "Approved" and approved["review_history"][-1]["by"] == "Admin"


def test_rejecting_needs_a_reason(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)

    assert client.post(f"/api/admin/papers/{paper['id']}/reject", json={}, headers=admin["headers"]).status_code == 422
    assert reject(client, admin, paper["id"], reason="  ").status_code == 422
    assert client.get(f"/api/admin/papers/{paper['id']}", headers=admin["headers"]).json()["status"] == "Pending Approval"


def test_only_a_pending_paper_can_be_decided(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)
    approve(client, admin, paper["id"])

    assert approve(client, admin, paper["id"]).status_code == 409
    assert reject(client, admin, paper["id"]).status_code == 409


def test_the_faculty_sees_the_decision_and_the_reason(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)
    reject(client, admin, paper["id"], reason="Unit 2 questions are too easy.")

    seen = client.get(f"/api/papers/{paper['id']}", headers=faculty["headers"]).json()
    notes = client.get("/api/papers/notifications", headers=faculty["headers"]).json()

    assert seen["status"] == "Rejected" and seen["rejection_reason"] == "Unit 2 questions are too easy."
    assert notes[0]["paper_id"] == paper["id"] and notes[0]["status"] == "Rejected" and notes[0]["reason"] == "Unit 2 questions are too easy."


def test_a_rejected_paper_can_be_corrected_and_resubmitted_for_approval(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)
    reject(client, admin, paper["id"])
    edit = {"questions": [{"sub_question_id": "b2", "question_text": "Discuss the classification of inventory models and compare the EOQ model with a periodic review model.", "options": [], "answer": ""}]}

    assert client.put(f"/api/papers/{paper['id']}", json=edit, headers=faculty["headers"]).status_code == 200
    resubmitted = client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"]).json()

    assert resubmitted["status"] == "Pending Approval"
    assert resubmitted["rejection_reason"] is None
    assert [entry["status"] for entry in resubmitted["review_history"]] == ["Rejected"]  # the earlier decision is kept
    assert client.get("/api/admin/stats", headers=admin["headers"]).json()["pending"] == 1


def test_an_approved_paper_is_final_for_the_faculty(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)
    approve(client, admin, paper["id"])

    assert client.put(f"/api/papers/{paper['id']}", json={"questions": [{"sub_question_id": "a1", "question_text": "A changed question text."}]}, headers=faculty["headers"]).status_code == 409
    assert client.post(f"/api/papers/{paper['id']}/submit", headers=faculty["headers"]).status_code == 409
    assert client.delete(f"/api/papers/{paper['id']}", headers=faculty["headers"]).status_code == 409


def test_the_faculty_list_shows_each_member_with_paper_counts_and_no_secrets(client, admin, faculty, other_faculty, groq):
    create_paper(client, faculty, groq)
    create_paper(client, faculty, groq, submit=False)

    members = client.get("/api/admin/faculty", headers=admin["headers"]).json()

    assert [m["email"] for m in members] == ["prof.a@college.edu", "prof.b@college.edu"]  # the admin is not listed
    first = members[0]
    assert (first["name"], first["department"]) == ("Prof. A", "Computer Science")
    assert first["papers"] == {"total": 1, "pending": 1, "approved": 0, "rejected": 0, "drafts": 1}
    assert "password_hash" not in str(members)


def test_the_departments_overview_lists_every_department_with_faculty_and_paper_counts(client, admin, faculty, other_faculty, groq):
    create_paper(client, faculty, groq)
    register_faculty(client, email="prof.c@college.edu", name="Prof. C", department="Computer Science")

    rows = {row["department"]: row for row in client.get("/api/admin/departments", headers=admin["headers"]).json()}

    assert len(rows) == 6
    assert (rows["Computer Science"]["faculty_count"], rows["Computer Science"]["total"], rows["Computer Science"]["pending"]) == (2, 1, 1)
    assert (rows["Mechanical"]["faculty_count"], rows["Mechanical"]["total"]) == (1, 0)
    assert rows["Civil"]["faculty_count"] == 0


# ---- downloading ----------------------------------------------------------------------------

def test_a_faculty_member_can_download_the_paper_only_once_it_is_approved(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)

    before = client.get(f"/api/papers/{paper['id']}/pdf", headers=faculty["headers"])
    approve(client, admin, paper["id"])
    after = client.get(f"/api/papers/{paper['id']}/pdf", headers=faculty["headers"])

    assert before.status_code == 403 and "approved" in before.json()["detail"].lower()
    assert after.status_code == 200
    assert after.headers["content-type"] == "application/pdf"
    assert after.content.startswith(b"%PDF-")
    assert "attachment" in after.headers["content-disposition"] and ".pdf" in after.headers["content-disposition"]


def test_someone_elses_paper_cannot_be_downloaded(client, admin, faculty, other_faculty, groq):
    paper = create_paper(client, faculty, groq)
    approve(client, admin, paper["id"])

    assert client.get(f"/api/papers/{paper['id']}/pdf", headers=other_faculty["headers"]).status_code == 404


def test_the_admin_can_download_any_submitted_paper_for_review(client, admin, faculty, groq):
    paper = create_paper(client, faculty, groq)

    response = client.get(f"/api/admin/papers/{paper['id']}/pdf", headers=admin["headers"])

    assert response.status_code == 200 and response.content.startswith(b"%PDF-")
