"""Request validation models (Pydantic)."""
import re
from typing import Optional

from pydantic import BaseModel, field_validator

BRANCHES = ["CSE", "IT", "AI & ML / Data Science", "ECE", "EEE", "Mechanical", "Civil", "Other"]
YEARS = ["First Year", "Second Year", "Third Year", "Final Year"]
AI_LEVELS = ["Beginner", "Intermediate", "Advanced"]
GOALS = [
    "Placement preparation",
    "Building AI projects",
    "Learning AI fundamentals",
    "Exploring AI careers",
]
CHANNELS = ["WhatsApp", "Instagram", "LinkedIn", "Referral", "Direct"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    name: str
    email: str
    phone: str
    college: str
    branch: str
    year: str
    ai_level: str
    career_goal: str
    src: Optional[str] = None  # utm-style source, e.g. ?src=whatsapp
    ref: Optional[str] = None  # referral code, e.g. ?ref=MAHA_AI2026

    @field_validator("name", "college")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("must be at least 2 characters")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("enter a valid email address")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        digits = digits[-10:]  # drop +91 / 0 prefix
        if len(digits) != 10 or digits[0] not in "6789":
            raise ValueError("enter a valid 10-digit Indian mobile number")
        return digits

    @field_validator("branch")
    @classmethod
    def valid_branch(cls, v: str) -> str:
        if v not in BRANCHES:
            raise ValueError("choose a branch from the list")
        return v

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: str) -> str:
        if v not in YEARS:
            raise ValueError("choose your year of study")
        return v

    @field_validator("ai_level")
    @classmethod
    def valid_level(cls, v: str) -> str:
        if v not in AI_LEVELS:
            raise ValueError("choose your AI experience level")
        return v

    @field_validator("career_goal")
    @classmethod
    def valid_goal(cls, v: str) -> str:
        if v not in GOALS:
            raise ValueError("choose a career goal")
        return v


class VisitIn(BaseModel):
    src: Optional[str] = None
    ref: Optional[str] = None
