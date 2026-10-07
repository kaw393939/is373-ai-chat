"""A runner token or a stale QA result cannot authorize arbitrary production bits."""

import hashlib
import io
import json
import urllib.error
import zipfile

import pytest

from deploy import release_policy as policy

DIGEST = "sha256:" + "a" * 64
COMMIT = "b" * 40
IDENTITY = policy.identity(DIGEST, COMMIT, "2.0.0")


class GitHub:
    def __init__(self, conclusion="success", qa="success", tag=False, commit=COMMIT):
        self.conclusion, self.qa, self.tag, self.commit = conclusion, qa, tag, commit

    def get(self, path, **kwargs):
        if "/git/ref/" in path or "/releases/" in path:
            return {"ref": "exists"} if self.tag else None
        if "/jobs" in path:
            return {
                "jobs": [{"name": "QA acceptance", "status": "completed", "conclusion": self.qa}]
            }
        return {
            "head_sha": self.commit,
            "head_branch": "main",
            "event": "push",
            "path": ".github/workflows/delivery.yml",
            "status": "completed",
            "conclusion": self.conclusion,
        }

    def candidate(self, number):
        return {**IDENTITY, "run_id": number}


@pytest.fixture
def qa(tmp_path):
    current = {**IDENTITY, "schema": "0003", "status": "deployed"}
    attestation = {**current, "run_id": "42", "status": "accepted"}
    (tmp_path / "release.json").write_text(json.dumps(current))
    (tmp_path / "qa-attestation.json").write_text(json.dumps(attestation))
    return tmp_path


@pytest.mark.parametrize("value", ["2.0.0", "2.1.0-rc.1", "0.2.4-beta", "1.0.0-0"])
def test_canonical_versions(value):
    assert policy.version(value) == value


@pytest.mark.parametrize(
    "value", ["v2.0.0", "02.0.0", "1.0", "1.0.0-01", "1.0.0+build", "1.0.0;rm x"]
)
def test_invalid_release_version(value):
    with pytest.raises(ValueError):
        policy.version(value)


def test_approved_digest_can_be_promoted_without_rebuild(qa):
    assert policy.promotion(GitHub(), "42", IDENTITY, qa, {})["image"] == IDENTITY["image"]


@pytest.mark.parametrize(
    "api",
    [GitHub(qa="failure"), GitHub(conclusion="failure"), GitHub(commit="c" * 40), GitHub(tag=True)],
)
def test_failed_qa_wrong_source_or_existing_tag_blocks_promotion(qa, api):
    with pytest.raises(ValueError):
        policy.promotion(api, "42", IDENTITY, qa, {})


def test_stale_qa_digest_and_reused_version_are_refused(qa):
    with pytest.raises(ValueError, match="already deployed"):
        policy.promotion(GitHub(), "42", IDENTITY, qa, {"2.0.0": IDENTITY})
    (qa / "release.json").write_text(
        json.dumps({**IDENTITY, "image": "other", "status": "deployed"})
    )
    with pytest.raises(ValueError, match="stale"):
        policy.promotion(GitHub(), "42", IDENTITY, qa, {})


def test_spoofed_image_labels_cannot_borrow_a_successful_run(qa):
    forged = {**IDENTITY, "image": policy.IMAGE + "@sha256:" + "c" * 64}
    with pytest.raises(ValueError, match="tested published"):
        policy.verify_run(GitHub(), "42", forged)


def test_published_manifest_hash_is_checked_before_use(monkeypatch):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("candidate.json", json.dumps({**IDENTITY, "run_id": "42"}))
    data = output.getvalue()
    api = policy.GitHub("synthetic-fixture-token")
    metadata = {
        "artifacts": [
            {
                "id": 9,
                "name": "published-candidate",
                "expired": False,
                "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
            }
        ]
    }
    monkeypatch.setattr(api, "get", lambda _: metadata)
    monkeypatch.setattr(api, "archive", lambda _: data)
    assert api.candidate("42")["image"] == IDENTITY["image"]
    metadata["artifacts"][0]["digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        api.candidate("42")


def test_expired_or_missing_candidate_is_not_acceptance(monkeypatch):
    api = policy.GitHub("synthetic-fixture-token")
    monkeypatch.setattr(api, "get", lambda _: {"artifacts": []})
    with pytest.raises(ValueError, match="absent"):
        api.candidate("42")


def test_signed_artifact_redirect_does_not_forward_bearer(monkeypatch):
    requests = []

    class Opener:
        def open(self, request, **kwargs):
            requests.append(request)
            if len(requests) == 1:
                raise urllib.error.HTTPError(
                    request.full_url,
                    302,
                    "Found",
                    {"Location": "https://storage.example.org/signed-fixture"},
                    None,
                )
            return io.BytesIO(b"synthetic archive")

    monkeypatch.setattr(policy.urllib.request, "build_opener", lambda _: Opener())
    assert policy.GitHub("synthetic-token").archive("9") == b"synthetic archive"
    assert requests[0].get_header("Authorization") == "Bearer synthetic-token"
    assert requests[1].get_header("Authorization") is None


@pytest.mark.parametrize("value", ["0", "-1", "42/../secrets", "42\n", "1" * 21])
def test_run_id_cannot_change_api_path(value):
    with pytest.raises(ValueError):
        policy.run_id(value)
