"""
Authentication endpoint tests.

Verifies user registration, email verification,
verification code validation, and verification
code resend behavior.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import EmailCode, User
from app.routers.auth import RESEND_MESSAGE

VALID = {"name": "Ama Mensah", "email": "ama@example.com", "password": "Test1234"}


def signup(client, **overrides):
    return client.post("/auth/signup", json={**VALID, **overrides})


def verify(client, code, email=VALID["email"]):
    return client.post("/auth/verify-email", json={"email": email, "code": code})


def resend(client, email=VALID["email"]):
    return client.post("/auth/resend-verification", json={"email": email})


def get_user(db):
    db.expire_all()
    return db.scalars(select(User)).one()


def get_code_record(db):
    db.expire_all()
    return db.scalars(select(EmailCode)).one()


def age_codes(db, seconds):
    """Make every stored code look older, to get past the 60-second wait."""
    db.expire_all()
    for record in db.scalars(select(EmailCode)):
        record.created_at -= timedelta(seconds=seconds)
    db.commit()


def wrong_code(real):
    return "000000" if real != "000000" else "999999"


# ---------- sign up ----------


def test_signup_creates_unverified_user_and_sends_code(client, db, sent_codes):
    response = signup(client)
    assert response.status_code == 201
    user = get_user(db)
    assert user.is_verified is False
    assert user.password_hash != "Test1234"
    assert len(sent_codes) == 1
    assert len(sent_codes[0]["code"]) == 6


def test_email_is_stored_lowercase(client, db):
    assert signup(client, email="Ama@Example.COM").status_code == 201
    assert get_user(db).email == "ama@example.com"


def test_duplicate_email_is_rejected(client):
    assert signup(client).status_code == 201
    assert signup(client).status_code == 409
    assert signup(client, email="AMA@example.com").status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"name": "   "},
        {"password": "Ab1"},
        {"password": "A1" + "b" * 63},
        {"password": "onlyletters"},
        {"password": "12345678"},
    ],
)
def test_invalid_signup_input_is_rejected(client, sent_codes, overrides):
    assert signup(client, **overrides).status_code == 422
    assert sent_codes == []


# ---------- verify ----------


def test_correct_code_verifies_the_user(client, db, sent_codes):
    signup(client)
    response = verify(client, sent_codes[0]["code"])
    assert response.status_code == 200
    assert get_user(db).is_verified is True


def test_wrong_code_is_rejected(client, db, sent_codes):
    signup(client)
    response = verify(client, wrong_code(sent_codes[0]["code"]))
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired code"
    assert get_user(db).is_verified is False


def test_unknown_email_gets_the_same_error(client):
    response = verify(client, "123456", email="nobody@example.com")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired code"


@pytest.mark.parametrize("code", ["12345", "1234567", "abcdef"])
def test_badly_formatted_code_is_rejected(client, code):
    assert verify(client, code).status_code == 422


def test_code_cannot_be_used_twice(client, sent_codes):
    signup(client)
    code = sent_codes[0]["code"]
    assert verify(client, code).status_code == 200
    assert verify(client, code).status_code == 400


def test_expired_code_is_rejected(client, db, sent_codes):
    signup(client)
    record = get_code_record(db)
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    assert verify(client, sent_codes[0]["code"]).status_code == 400
    assert get_user(db).is_verified is False


def test_code_is_locked_after_five_wrong_attempts(client, db, sent_codes):
    signup(client)
    real = sent_codes[0]["code"]
    for _ in range(5):
        assert verify(client, wrong_code(real)).status_code == 400
    assert verify(client, real).status_code == 400
    assert get_user(db).is_verified is False


def test_code_still_works_after_four_wrong_attempts(client, sent_codes):
    signup(client)
    real = sent_codes[0]["code"]
    for _ in range(4):
        assert verify(client, wrong_code(real)).status_code == 400
    assert verify(client, real).status_code == 200


# ---------- resend ----------


def test_resend_within_60_seconds_sends_no_new_code(client, sent_codes):
    signup(client)
    response = resend(client)
    assert response.status_code == 200
    assert response.json()["message"] == RESEND_MESSAGE
    assert len(sent_codes) == 1


def test_resend_after_the_wait_replaces_the_old_code(client, db, sent_codes):
    signup(client)
    age_codes(db, 61)
    assert resend(client).status_code == 200
    assert len(sent_codes) == 2
    old, new = sent_codes[0]["code"], sent_codes[1]["code"]
    if old == new:
        pytest.skip("The two random codes happened to match")
    assert verify(client, old).status_code == 400
    assert verify(client, new).status_code == 200


def test_resend_for_unknown_email_gives_the_same_message(client, sent_codes):
    response = resend(client, email="nobody@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == RESEND_MESSAGE
    assert sent_codes == []


def test_resend_for_verified_user_sends_nothing(client, db, sent_codes):
    signup(client)
    verify(client, sent_codes[0]["code"])
    age_codes(db, 61)
    response = resend(client)
    assert response.status_code == 200
    assert len(sent_codes) == 1


def test_resend_with_invalid_email_is_rejected(client):
    assert resend(client, email="not-an-email").status_code == 422