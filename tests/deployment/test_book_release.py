"""The app footer must not publish an edition link while its bundle is pending."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "deploy"))
from check_book_release import accepted, edition, required_assets, wait_for_edition  # noqa: E402

TAG = "book-v0.3.0"


def published():
    return {
        "tag_name": TAG,
        "draft": False,
        "immutable": True,
        "prerelease": True,
        "assets": [
            {"name": name, "state": "uploaded", "size": 10} for name in required_assets(TAG)
        ],
    }


@pytest.mark.parametrize(
    "change",
    [
        {"draft": True},
        {"immutable": False},
        {"tag_name": "book-v0.2.0"},
        {"assets": []},
        {"assets": [{"name": "book-build.json", "state": "uploaded", "size": 0}]},
    ],
)
def test_incomplete_or_mutable_edition_is_not_ready(change):
    assert not accepted({**published(), **change}, TAG)


@pytest.mark.parametrize("change", [{"size": 0}, {"state": "new"}])
def test_named_zip_must_have_uploaded_nonempty_bytes(change):
    release = published()
    bundle = next(item for item in release["assets"] if item["name"].endswith(".zip"))
    bundle.update(change)
    assert not accepted(release, TAG)


def test_footer_is_the_fixed_edition_identity_and_prerelease_is_allowed():
    assert edition("`${repository}/releases/tag/book-v0.3.0`") == TAG
    assert accepted(published(), TAG)
    with pytest.raises(ValueError):
        edition("no downloadable release")
    with pytest.raises(ValueError):
        edition("/releases/tag/book-v0.3.0 /releases/tag/book-v0.4.0")


class Clock:
    value = 0

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class API:
    def __init__(self, values):
        self.values, self.calls = values, 0

    def get(self, path, missing):
        assert path == "/releases/tags/" + TAG and missing is True
        self.calls += 1
        value = self.values[min(self.calls - 1, len(self.values) - 1)]
        if isinstance(value, Exception):
            raise value
        return value


def test_publication_race_waits_for_uploaded_assets_then_accepts():
    clock = Clock()
    api = API([None, {**published(), "draft": True}, published()])
    assert wait_for_edition(api, TAG, clock.now, clock.sleep) == published()
    assert api.calls == 3 and clock.value == 20


def test_failed_publication_is_bounded_before_any_deployment():
    clock = Clock()
    api = API([RuntimeError("synthetic unavailable API")])
    with pytest.raises(RuntimeError, match="five minutes"):
        wait_for_edition(api, TAG, clock.now, clock.sleep)
    assert clock.value <= 300 and api.calls <= 30
