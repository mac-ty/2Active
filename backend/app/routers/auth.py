"""
Authentication API endpoints.

Provides routes for user registration, email verification,
and verification code management. Coordinates validation,
database operations, and email delivery for account
activation workflows.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.codes import check_code, issue_code
from app.database import get_db
from app.mailer import EmailSendError, send_verification_code
from app.models import CodePurpose, User
from app.schemas import EmailRequest, MessageResponse, SignupRequest, VerifyEmailRequest
from app.security import hash_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

RESEND_MESSAGE = (
    "If an account exists for this email and is not verified, a new code has been sent."
)


def _get_user(db: Session, email: str):
    return db.scalars(select(User).where(User.email == email)).first()


def _send_code_email(db: Session, user: User) -> None:
    code = issue_code(db, user, CodePurpose.verify_email)
    if code is None:
        return
    try:
        send_verification_code(user.email, user.name, code)
    except EmailSendError:
        logger.exception("Could not send verification email")


@router.post("/signup", response_model=MessageResponse, status_code=201)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    _send_code_email(db, user)
    return {"message": "Account created. Check your email for a 6-digit code."}


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = _get_user(db, data.email)
    if user is None or not check_code(db, user, CodePurpose.verify_email, data.code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user.is_verified = True
    db.commit()
    return {"message": "Email verified"}


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(data: EmailRequest, db: Session = Depends(get_db)):
    user = _get_user(db, data.email)
    if user is not None and not user.is_verified:
        _send_code_email(db, user)
    return {"message": RESEND_MESSAGE}