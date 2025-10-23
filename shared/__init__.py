"""
Shared modules for JobSync application.
Consolidates common functionality to reduce code duplication.
"""

from .models import EmailData, JobApplicationData, WeeklyReportData, WeeklyReportState
from .utils import (
    setup_path_imports,
    format_entries_for_llm,
    format_deadlines_for_llm,
    generate_week_range,
    get_llm_config,
    get_llm_config_creative,
)
from .config import (
    NOTION_TOKEN,
    NOTION_DATABASE_ID,
    NOTION_WEEKLY_REPORTS_DB_ID,
    OPENROUTER_KEY,
    OPENROUTER_MODEL,
    GMAIL_CREDENTIALS_PATH,
    GMAIL_TOKEN_PATH,
    validate_config,
)
from .entry_points import (
    run_workflow_with_error_handling,
    run_weekly_report_with_error_handling,
)

__all__ = [
    # Models
    "EmailData",
    "JobApplicationData",
    "WeeklyReportData",
    "WeeklyReportState",
    # Utils
    "setup_path_imports",
    "format_entries_for_llm",
    "format_deadlines_for_llm",
    "generate_week_range",
    "get_llm_config",
    "get_llm_config_creative",
    # Config
    "NOTION_TOKEN",
    "NOTION_DATABASE_ID",
    "NOTION_WEEKLY_REPORTS_DB_ID",
    "OPENROUTER_KEY",
    "OPENROUTER_MODEL",
    "GMAIL_CREDENTIALS_PATH",
    "GMAIL_TOKEN_PATH",
    "validate_config",
    # Entry points
    "run_workflow_with_error_handling",
    "run_weekly_report_with_error_handling",
]
