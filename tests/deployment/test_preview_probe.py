"""The public smoke probe is constrained to mock previews, never production."""

import pytest

from deploy.check_preview import URLS, check_identity


def test_probe_has_no_production_target():
    assert URLS == {"dev": "https://dev.firehose360.com", "qa": "https://qa.firehose360.com"}


@pytest.mark.parametrize(
    "changes",
    [
        {"provider": "openai"},
        {"commit": "old"},
        {"version": "1.0.0"},
        {"schema": "0002"},
        {"status": "failed"},
    ],
)
def test_wrong_release_or_real_provider_is_refused(changes):
    health = {
        "status": "ok",
        "commit": "new",
        "version": "2.0.0",
        "schema": "0003",
        "provider": "mock",
    }
    with pytest.raises(ValueError):
        check_identity({**health, **changes}, "new", "2.0.0", "0003")
