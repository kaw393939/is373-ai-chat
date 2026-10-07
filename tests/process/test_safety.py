import pytest

from tests.process.safety import nonce, process_database, process_url, verify_identity


@pytest.mark.parametrize(
    "url",
    [
        "https://firehose360.com",
        "http://127.0.0.1:9001",
        "http://127.0.0.1:9002/api",
        "http://u:p@127.0.0.1:9002",
        "http://127.0.0.1:9002?x=1",
    ],
)
def test_process_target_rejected_before_any_network(url):
    with pytest.raises(ValueError):
        process_url(url)


@pytest.mark.parametrize(
    "url,ack",
    [
        ("postgresql+asyncpg://u:p@159.203.182.71/process_test", "process_test"),
        ("postgresql+asyncpg://u:p@localhost/chat_test", "chat_test"),
        ("postgresql+asyncpg://u:p@localhost/process_test", "chat_test"),
    ],
)
def test_process_database_is_separate_and_loopback(url, ack):
    with pytest.raises(ValueError):
        process_database(url, ack)


def test_process_requires_its_nonce_and_replica_identity():
    token = "a" * 64
    expected = {
        "nonce": token,
        "replica": 0,
        "database": "process_test",
        "provider": "fault-mock",
        "mail": "disabled",
    }
    verify_identity(expected, token, 0)
    with pytest.raises(ValueError):
        verify_identity(expected, token, 1)
    with pytest.raises(ValueError):
        verify_identity({**expected, "nonce": "b" * 64}, token, 0)
    with pytest.raises(ValueError):
        nonce("existing-server")
