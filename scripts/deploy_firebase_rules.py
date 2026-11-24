"""Deploy version-controlled Firebase rules with a service-account credential.

The credential path is supplied at runtime and is never copied into the repo.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account


API_ROOT = "https://firebaserules.googleapis.com/v1"
PROJECT_ID = "health-quest-agent"
TARGETS = (
    ("firestore.rules", "cloud.firestore"),
    (
        "storage.rules",
        "firebase.storage/health-quest-agent.firebasestorage.app",
    ),
)


def _session(credential_path: Path) -> AuthorizedSession:
    credentials = service_account.Credentials.from_service_account_file(
        str(credential_path),
        scopes=["https://www.googleapis.com/auth/firebase"],
    )
    return AuthorizedSession(credentials)


def _deploy(
    session: AuthorizedSession,
    repo_root: Path,
    rules_file: str,
    release_id: str,
) -> str:
    content = (repo_root / rules_file).read_text(encoding="utf-8")
    create = session.post(
        f"{API_ROOT}/projects/{PROJECT_ID}/rulesets",
        json={"source": {"files": [{"name": rules_file, "content": content}]}},
        timeout=30,
    )
    create.raise_for_status()
    ruleset_name = create.json()["name"]

    release_name = f"projects/{PROJECT_ID}/releases/{release_id}"
    update = session.patch(
        f"{API_ROOT}/{release_name}",
        json={
            "release": {"name": release_name, "rulesetName": ruleset_name},
            "updateMask": "rulesetName",
        },
        timeout=30,
    )
    update.raise_for_status()

    verify = session.get(f"{API_ROOT}/{release_name}", timeout=30)
    verify.raise_for_status()
    if verify.json().get("rulesetName") != ruleset_name:
        raise RuntimeError(f"Release verification failed for {rules_file}")
    return ruleset_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("credential", type=Path)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    session = _session(args.credential)
    for rules_file, release_id in TARGETS:
        ruleset_name = _deploy(session, repo_root, rules_file, release_id)
        print(f"deployed {rules_file}: {ruleset_name}")


if __name__ == "__main__":
    main()
