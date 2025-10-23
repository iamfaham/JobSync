"""
Shared Pydantic models for JobSync application.
Consolidates all data models to avoid duplication.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class EmailData(BaseModel):
    """Email data structure used across Gmail operations."""

    id: str
    subject: str
    sender: str
    date: str
    text: str
    snippet: str


class JobApplicationData(BaseModel):
    """Job application data structure."""

    company: str
    job_title: str
    status: str
    applied_on: str
    notes: str = ""
    app_id: Optional[str] = None


class WeeklyReportData(BaseModel):
    """Weekly report data structure."""

    total: int
    applied: int
    interview: int
    assessment: int
    offer: int
    rejected: int
    deadlines: List[Dict[str, str]]
    entries: List[Dict[str, str]]


class WeeklyReportState(BaseModel):
    """Weekly report workflow state."""

    days: int
    report_data: Optional[WeeklyReportData] = None
    summary: Optional[str] = None
    week_range: Optional[str] = None
    errors: List[str] = []
