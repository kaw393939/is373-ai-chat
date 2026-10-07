"""A preview's private key cannot operate production or obtain a shell."""

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

loader = SourceFileLoader("chat_ssh", str(Path(__file__).parents[2] / "deploy/chat-ssh"))
spec = importlib.util.spec_from_loader(loader.name, loader)
ssh = importlib.util.module_from_spec(spec)
loader.exec_module(ssh)
DIGEST, SHA = "sha256:" + "a" * 64, "b" * 40


@pytest.mark.parametrize(
    "scope,operation",
    [("dev", "deploy dev"), ("qa", "deploy qa"), ("qa", "attest"), ("production", "promote")],
)
def test_each_key_permits_only_its_command(scope, operation):
    text = f"{operation} {DIGEST} {SHA} 2.0.0" + (
        " 42" if operation in {"attest", "promote"} else ""
    )
    assert ssh.command(scope, text) == text.split()


@pytest.mark.parametrize(
    "scope,text",
    [
        ("dev", "promote"),
        ("qa", "promote"),
        ("production", "attest"),
        ("production", "deploy qa"),
        ("dev", "deploy qa"),
    ],
)
def test_cross_environment_access_is_refused(scope, text):
    with pytest.raises(ValueError):
        ssh.command(scope, f"{text} {DIGEST} {SHA} 2.0.0 42")


@pytest.mark.parametrize("suffix", ["; id", "\nwhoami", " $(id)", " && id", " | sh"])
def test_shell_syntax_is_refused(suffix):
    with pytest.raises(ValueError):
        ssh.command("qa", f"deploy qa {DIGEST} {SHA} 2.0.0" + suffix)
