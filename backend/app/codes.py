"""
Verification code services.

Provides business logic for issuing, validating, expiring,
and rate-limiting email verification and password reset
codes.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CodePurpose, EmailCode, User
from app.security import generate_code, hash_code, verify_code

CODE_LIFETIME = {
    CodePurpose.verify_email: timedelta(minutes=5),
    CodePurpose.reset_password: timedelta(minutes=10),
}
RESEND_WAIT = timedelta(seconds=60)
MAX_FAILED_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _latest_unused(db: Session, user: User, purpose: CodePurpose):
    return db.scalars(
        select(EmailCode)
        .where(
            EmailCode.user_id == user.id,
            EmailCode.purpose == purpose,
            EmailCode.used.is_(False),
        )
        .order_by(EmailCode.created_at.desc())
    ).first()


def issue_code(db: Session, user: User, purpose: CodePurpose) -> str | None:
    """Create a new code. Returns the plain code, or None if the 60-second wait has not passed."""
    now = _now()
    latest = db.scalars(
        select(EmailCode)
        .where(EmailCode.user_id == user.id, EmailCode.purpose == purpose)
        .order_by(EmailCode.created_at.desc())
    ).first()
    if latest is not None and now - latest.created_at < RESEND_WAIT:
        return None

    # A new code replaces any earlier unused code.
    for old in db.scalars(
        select(EmailCode).where(
            EmailCode.user_id == user.id,
            EmailCode.purpose == purpose,
            EmailCode.used.is_(False),
        )
    ):
        old.used = True

    code = generate_code()
    db.add(
        EmailCode(
            user_id=user.id,
            code_hash=hash_code(code),
            purpose=purpose,
            expires_at=now + CODE_LIFETIME[purpose],
        )
    )
    db.commit()
    return code


def check_code(db: Session, user: User, purpose: CodePurpose, code: str) -> bool:
    """True only for a correct, unused, unexpired code with attempts left."""
    record = _latest_unused(db, user, purpose)
    if (
        record is None
        or record.expires_at <= _now()
        or record.failed_attempts >= MAX_FAILED_ATTEMPTS
    ):
        return False

    if verify_code(code, record.code_hash):
        record.used = True
        db.commit()
        return True

    record.failed_attempts += 1
    if record.failed_attempts >= MAX_FAILED_ATTEMPTS:
        record.used = True
    db.commit()
    return False