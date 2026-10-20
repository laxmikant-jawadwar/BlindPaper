"""Registration, login, sessions, profile and the seeded admin account."""

from datetime import timedelta

from app.models.mongo import utcnow

from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, auth_header, register_faculty


def test_register_creates_a_faculty_user_and_returns_a_token(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Prof. Laxmikant", "email": "Laxmikant@College.edu", "password": "secret123", "department": "Computer Science"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token"]
    assert body["user"]["name"] == "Prof. Laxmikant"
    assert body["user"]["email"] == "laxmikant@college.edu"  # stored lower-case
    assert body["user"]["role"] == "faculty"
    assert body["user"]["department"] == "Computer Science"
    assert "password" not in body["user"] and "password_hash" not in body["user"]


def test_the_password_is_stored_hashed_never_in_plain_text(client, fake_mongo):
    register_faculty(client, password="secret123")

    stored = fake_mongo["blindpaper"]["users"].find_one({"email": "prof.a@college.edu"})
    assert "secret123" not in str(stored)
    assert stored["password_hash"].startswith("pbkdf2_sha256$")


def test_registering_the_same_email_twice_is_rejected_case_insensitively(client):
    register_faculty(client, email="prof.a@college.edu")

    response = client.post(
        "/api/auth/register",
        json={"name": "Someone Else", "email": "PROF.A@college.edu", "password": "secret123", "department": "Civil"},
    )

    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


def test_registration_input_is_validated(client):
    base = {"name": "Prof. X", "email": "x@college.edu", "password": "secret123", "department": "Civil"}

    assert client.post("/api/auth/register", json={**base, "password": "123"}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "email": "not-an-email"}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "department": "Astrology"}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "name": "  "}).status_code == 422


def test_nobody_can_register_themselves_as_admin(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Sneaky", "email": "sneaky@college.edu", "password": "secret123", "department": "Civil", "role": "admin"},
    )

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "faculty"


def test_login_returns_a_token_and_the_user(client):
    register_faculty(client)

    response = client.post("/api/auth/login", json={"email": "PROF.A@college.edu", "password": "secret123"})

    assert response.status_code == 200
    assert response.json()["token"]
    assert response.json()["user"]["email"] == "prof.a@college.edu"


def test_wrong_password_and_unknown_email_give_the_same_error(client):
    register_faculty(client)

    wrong_password = client.post("/api/auth/login", json={"email": "prof.a@college.edu", "password": "nope-nope"})
    unknown_email = client.post("/api/auth/login", json={"email": "ghost@college.edu", "password": "secret123"})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_needs_a_valid_token(client, faculty):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth_header("not-a-real-token")).status_code == 401

    response = client.get("/api/auth/me", headers=faculty["headers"])
    assert response.status_code == 200
    assert response.json()["email"] == "prof.a@college.edu"


def test_logout_invalidates_the_token(client, faculty):
    assert client.post("/api/auth/logout", headers=faculty["headers"]).status_code == 200

    assert client.get("/api/auth/me", headers=faculty["headers"]).status_code == 401


def test_an_expired_session_is_rejected(client, faculty, fake_mongo):
    fake_mongo["blindpaper"]["sessions"].update_many(
        {}, {"$set": {"expires_at": utcnow() - timedelta(minutes=1)}}
    )

    assert client.get("/api/auth/me", headers=faculty["headers"]).status_code == 401


def test_the_admin_account_is_seeded_from_the_settings(client):
    response = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"
    assert response.json()["user"]["name"] == "Admin"


def test_seeding_the_admin_twice_does_not_create_a_second_account(client, fake_mongo):
    from app.services.auth_service import auth_service

    auth_service.ensure_admin_user()
    auth_service.ensure_admin_user()

    assert fake_mongo["blindpaper"]["users"].count_documents({"role": "admin"}) == 1


def test_profile_can_be_updated_but_not_the_email_or_role(client, faculty):
    response = client.put(
        "/api/auth/me",
        headers=faculty["headers"],
        json={
            "name": "Prof. Laxmikant J",
            "department": "Electronics",
            "designation": "Associate Professor",
            "phone": "9876543210",
            "email": "hacker@evil.com",
            "role": "admin",
        },
    )

    assert response.status_code == 200
    user = response.json()
    assert (user["name"], user["department"], user["designation"], user["phone"]) == (
        "Prof. Laxmikant J", "Electronics", "Associate Professor", "9876543210",
    )
    assert user["email"] == "prof.a@college.edu" and user["role"] == "faculty"
    assert client.get("/api/auth/me", headers=faculty["headers"]).json()["department"] == "Electronics"


def test_profile_update_rejects_an_unknown_department(client, faculty):
    response = client.put("/api/auth/me", headers=faculty["headers"], json={"department": "Astrology"})

    assert response.status_code == 422
