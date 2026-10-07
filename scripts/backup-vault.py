#!/usr/bin/env python3
"""Pull encrypted backups to an existing recovery computer over pinned-host SSH.

The restricted export key cannot access a shell or plaintext configuration.
The separate age decryption identity is never sent to the application host.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

NAME = re.compile(r"daily-(\d{8}T\d{6}Z)\.tar\.age\Z")
MAX_BYTES = 1024 * 1024 * 1024


def validate_list(values):
    if not isinstance(values, list) or len(values) > 30:
        raise ValueError("Invalid backup inventory")
    for value in values:
        if (
            not isinstance(value, dict)
            or not NAME.fullmatch(value.get("name", ""))
            or not isinstance(value.get("bytes"), int)
            or not 0 < value["bytes"] <= MAX_BYTES
            or not re.fullmatch(r"[a-f0-9]{64}", value.get("sha256", ""))
        ):
            raise ValueError("Invalid backup metadata")
    return sorted(values, key=lambda value: value["name"])


def ssh_command(host, key, known_hosts):
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+", host):
        raise ValueError("Use an explicit SSH user@host")
    for path in (key, known_hosts):
        if not path.is_file() or path.is_symlink():
            raise ValueError("SSH key and pinned known-hosts file are required")
        if any(character in str(path) for character in ('"', "\\", "\n", "\r")):
            raise ValueError("SSH paths contain unsupported configuration characters")
    if key.stat().st_mode & 0o077:
        raise ValueError("SSH key must be private (mode 0600)")
    return [
        "ssh",
        "-T",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f'UserKnownHostsFile="{known_hosts}"',
        "-o",
        "ConnectTimeout=10",
        "-i",
        str(key),
        host,
    ]


def checksum(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def pull(command, destination, run=subprocess.run):
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.is_symlink() or destination.stat().st_mode & 0o077:
        raise ValueError("Vault directory must be private (mode 0700)")
    result = run([*command, "list"], capture_output=True, check=True, timeout=30)
    if len(result.stdout) > 32768:
        raise ValueError("Backup inventory exceeded its bound")
    values = validate_list(json.loads(result.stdout))
    if not values:
        raise ValueError("No encrypted backup is available")
    for value in values:
        target = destination / value["name"]
        if target.is_symlink():
            raise ValueError("Vault contains an unsafe symlink")
        if target.exists() and checksum(target) == value["sha256"]:
            continue
        # The final filename appears only after a complete checked transfer.
        with tempfile.NamedTemporaryFile(
            dir=destination, prefix=".download-", delete=False
        ) as file:
            temp = Path(file.name)
            try:
                run(
                    [*command, "fetch " + value["name"]],
                    stdout=file,
                    stderr=subprocess.PIPE,
                    check=True,
                    timeout=120,
                )
                file.flush()
                os.fsync(file.fileno())
                if temp.stat().st_size != value["bytes"] or checksum(temp) != value["sha256"]:
                    raise ValueError("Encrypted backup transfer failed integrity check")
                temp.replace(target)
            finally:
                temp.unlink(missing_ok=True)
    newest = values[-1]
    run(
        [*command, f"ack {newest['name']} {newest['sha256']}"],
        capture_output=True,
        check=True,
        timeout=30,
    )
    receipt = {**newest, "received_at": datetime.now(timezone.utc).isoformat()}
    temp = destination / ".receipt.partial"
    temp.write_text(json.dumps(receipt, indent=2) + "\n")
    temp.chmod(0o600)
    temp.replace(destination / "receipt.json")
    # Prune only this vault's recognized ciphertext after a successful receipt.
    cutoff = datetime.now(timezone.utc).timestamp() - 28 * 86400
    for path in destination.glob("daily-*.tar.age"):
        match = NAME.fullmatch(path.name)
        if match and path.name != newest["name"] and not path.is_symlink():
            created = datetime.strptime(match[1], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            if created.timestamp() < cutoff:
                path.unlink()
    return receipt


def status(destination, instant=None):
    receipt = json.loads((destination / "receipt.json").read_text())
    value = validate_list([receipt])[0]
    if checksum(destination / value["name"]) != value["sha256"]:
        raise ValueError("Vault backup no longer matches its receipt")
    # A fresh download of an old dump must not make the backup look fresh.
    created = datetime.strptime(NAME.fullmatch(value["name"])[1], "%Y%m%dT%H%M%SZ").replace(
        tzinfo=timezone.utc
    )
    age_hours = ((instant or datetime.now(timezone.utc)) - created).total_seconds() / 3600
    if not 0 <= age_hours <= 36:
        raise ValueError("Off-host backup is older than 36 hours or has a future timestamp")
    return {"backup": value["name"], "age_hours": round(age_hours, 2), "integrity": "verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["pull", "status"])
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--host")
    parser.add_argument("--key", type=Path)
    parser.add_argument("--known-hosts", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "pull":
            if not all((args.host, args.key, args.known_hosts)):
                raise ValueError("Pull requires SSH host, key and pinned known-hosts file")
            pull(ssh_command(args.host, args.key, args.known_hosts), args.destination)
        print(json.dumps(status(args.destination)))
    except (OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit("Backup vault check failed; inspect protected operator evidence") from None


if __name__ == "__main__":
    main()
