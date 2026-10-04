"""Onboarding extraction schemas."""

from typing import Literal
from pydantic import BaseModel, Field

class ExtractedField(BaseModel):
    value: str | int | float | None
    evidence: str | None

class ExtractionWithEvidence(BaseModel):
    name: ExtractedField | None = None
    legal_name: ExtractedField | None = None
    date_of_birth: ExtractedField | None = None
    gender: ExtractedField | None = None
    state_of_residence: ExtractedField | None = None
    employment_type: ExtractedField | None = None
    occupation: ExtractedField | None = None
    income_frequency: ExtractedField | None = None
    average_income: ExtractedField | None = None
    financial_pain_points: ExtractedField | None = None
