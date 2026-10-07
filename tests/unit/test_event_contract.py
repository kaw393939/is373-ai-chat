"""An adapter's local failure cannot masquerade as a provider terminal result."""

import pytest

from app.events import GenerationState, provider_outcome


def test_provider_outcomes_are_explicit():
    assert provider_outcome("complete") == GenerationState.COMPLETE
    assert provider_outcome("incomplete") == GenerationState.INCOMPLETE
    assert provider_outcome("refused") == GenerationState.REFUSED
    for unsupported in ("streaming", "failed", "cancelled", "interrupted", "unknown"):
        with pytest.raises(KeyError):
            provider_outcome(unsupported)
