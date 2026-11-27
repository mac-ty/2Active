"""
API schemas.

Defines request and response models used for data validation,
serialization, and business rule enforcement for authentication
and account-related API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class SignupRequest(EmailRequest):
    name: str
    password: str

    @field_validator("name")
    @classmethod
    def name_rules(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        if len(value) > 100:
            raise ValueError("Name must be 100 characters or fewer")
        return value

    @field_validator("password")
    @classmethod
    def password_rules(cls, value: str) -> str:
        if not 8 <= len(value) <= 64:
            raise ValueError("Password must be 8 to 64 characters")
        has_letter = any(char.isalpha() for char in value)
        has_number = any(char in "0123456789" for char in value)
        if not (has_letter and has_number):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class VerifyEmailRequest(EmailRequest):
    code: str = Field(pattern=r"^[0-9]{6}$")


class MessageResponse(BaseModel):
    message: str