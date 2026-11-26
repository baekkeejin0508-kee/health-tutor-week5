"""Existing public HEALTH QUEST deployment with student access codes."""

from integrated_app_runtime import run_integrated_app


run_integrated_app(firebase_required=True, student_login_mode="access_code")
