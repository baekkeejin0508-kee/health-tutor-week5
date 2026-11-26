"""HEALTH QUEST with student access codes and Google teacher login."""

from integrated_app_runtime import run_integrated_app


run_integrated_app(firebase_required=True, student_login_mode="access_code")
