"""Firebase-enabled HEALTH QUEST deployment entrypoint.

Deploy this file as a separate Streamlit Community Cloud app and configure
``firebase.enabled = true`` only in that app's Secrets.  The existing
``app_integrated.py`` deployment can therefore remain independent.
"""

# Importing the integrated entrypoint runs the Streamlit application.  Keeping
# this tiny wrapper gives Community Cloud a distinct GitHub coordinate
# (repository + branch + entrypoint) for the Firebase deployment.
import app_integrated  # noqa: F401,E402
