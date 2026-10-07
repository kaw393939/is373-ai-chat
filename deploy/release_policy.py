"""Release identity and QA authorization shared by Actions and the privileged host.

Values travel as data, never shell programs. GitHub is checked independently of
the caller's assertions; the root-owned QA record binds that evidence to bytes.
"""

import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

REPOSITORY = "kaw393939/is373-ai-chat"
IMAGE = "ghcr.io/" + REPOSITORY
ROOTS = {
    "dev": Path("/opt/is373-ai-chat-dev"),
    "qa": Path("/opt/is373-ai-chat-qa"),
    "production": Path("/opt/is373-ai-chat"),
}
DIGEST = re.compile(r"sha256:[a-f0-9]{64}")
SHA = re.compile(r"[a-f0-9]{40}")
RUN_ID = re.compile(r"[1-9][0-9]{0,19}")
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


def version(value):
    """Use canonical SemVer, with commit metadata separate from the version.

    Build metadata (+suffix) is intentionally outside this project's contract:
    two artifacts cannot hide behind equal SemVer precedence/release names.
    """
    match = SEMVER.fullmatch(value)
    if not match or (
        match[4] and any(x.isdigit() and len(x) > 1 and x[0] == "0" for x in match[4].split("."))
    ):
        raise ValueError("Expected canonical MAJOR.MINOR.PATCH or prerelease version")
    return value


def identity(digest, commit, release_version):
    if not DIGEST.fullmatch(digest) or not SHA.fullmatch(commit):
        raise ValueError("Invalid immutable image/source identity")
    return {"image": IMAGE + "@" + digest, "commit": commit, "version": version(release_version)}


def run_id(value):
    if not RUN_ID.fullmatch(str(value)):
        raise ValueError("Invalid GitHub run ID")
    return str(value)


class GitHub:
    def __init__(self, token):
        if not token:
            raise ValueError("Short-lived GitHub credential required")
        self.token = token

    def get(self, path, missing=False):
        request = urllib.request.Request(
            "https://api.github.com/repos/" + REPOSITORY + path,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if missing and error.code == 404:
                return None
            raise RuntimeError("GitHub authorization/evidence request failed") from None

    def archive(self, identifier):
        """GitHub's signed HTTPS artifact URL must not receive the bearer header."""

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, request, file, code, message, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        request = urllib.request.Request(
            "https://api.github.com/repos/"
            + REPOSITORY
            + "/actions/artifacts/"
            + run_id(identifier)
            + "/zip",
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
            },
        )
        try:
            try:
                response = opener.open(request, timeout=20)
            except urllib.error.HTTPError as redirect:
                if redirect.code != 302:
                    raise
                location = redirect.headers["Location"]
                url = urlsplit(location)
                if url.scheme != "https" or not url.hostname or url.username or url.password:
                    raise ValueError("Unsafe artifact redirect")
                # Fresh request, no Authorization, and no additional redirects.
                response = opener.open(urllib.request.Request(location), timeout=20)
            with response:
                data = response.read(1048577)
            if len(data) > 1048576:
                raise ValueError("Candidate archive is unexpectedly large")
            return data
        except Exception:
            raise RuntimeError("Candidate provenance download failed") from None

    def candidate(self, number):
        records = self.get("/actions/runs/" + run_id(number) + "/artifacts?per_page=100")[
            "artifacts"
        ]
        records = [
            item
            for item in records
            if item["name"] == "published-candidate" and not item["expired"]
        ]
        if len(records) != 1:
            raise ValueError("Published immutable candidate evidence is absent or ambiguous")
        item = records[0]
        data = self.archive(item["id"])
        if (
            len(data) > 1048576
            or item.get("digest") != "sha256:" + hashlib.sha256(data).hexdigest()
        ):
            raise ValueError("Published candidate archive digest mismatch")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entry = archive.getinfo("candidate.json")
            if entry.file_size > 65536:
                raise ValueError("Candidate record is unexpectedly large")
            return json.loads(archive.read(entry))


def verify_run(api, number, expected, finished=True):
    """A successful run from this exact main workflow is necessary for promotion."""
    number = run_id(number)
    run = api.get("/actions/runs/" + number)
    if (
        run["head_sha"] != expected["commit"]
        or run["head_branch"] != "main"
        or run["event"] != "push"
        or run["path"] != ".github/workflows/delivery.yml"
        or (finished and (run["status"] != "completed" or run["conclusion"] != "success"))
    ):
        raise ValueError("Candidate lacks a successful main delivery run")
    jobs = api.get("/actions/runs/" + number + "/jobs?per_page=100")["jobs"]
    accepted = [job for job in jobs if job["name"] == "QA acceptance"]
    if (
        len(accepted) != 1
        or accepted[0]["status"] != "completed"
        or accepted[0]["conclusion"] != "success"
    ):
        raise ValueError("QA migration/browser/smoke job did not succeed")
    published = api.candidate(number)
    if not matches(published, expected) or published.get("run_id") != number:
        raise ValueError("Digest/version did not belong to the tested published candidate")
    return run


def unused_version(api, release_version):
    tag = "v" + version(release_version)
    if api.get("/git/ref/tags/" + tag, missing=True) or api.get(
        "/releases/tags/" + tag, missing=True
    ):
        raise ValueError("Release tag/version already exists; never move or reuse it")


def matches(record, expected):
    return all(record.get(key) == value for key, value in expected.items())


def promotion(api, number, expected, qa_root, history):
    """The workflow and the currently installed QA bytes must agree."""
    verify_run(api, number, expected)
    unused_version(api, expected["version"])
    attestation = json.loads((qa_root / "qa-attestation.json").read_text())
    current = json.loads((qa_root / "release.json").read_text())
    if (
        attestation.get("status") != "accepted"
        or current.get("status") != "deployed"
        or not matches(attestation, expected)
        or not matches(current, expected)
        or attestation.get("run_id") != run_id(number)
        or attestation.get("schema") != current.get("schema")
    ):
        raise ValueError("QA attestation is absent, stale or belongs to another artifact")
    if expected["version"] in history:
        raise ValueError("Version already deployed; reconcile release finalization explicitly")
    return attestation
