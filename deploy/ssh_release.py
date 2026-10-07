"""Pass only a validated release command and ephemeral registry token over SSH."""

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from release_policy import identity, run_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["deploy", "attest", "promote"])
    parser.add_argument("scope", choices=["dev", "qa", "production"])
    args = parser.parse_args()
    expected = identity(os.environ["DIGEST"], os.environ["COMMIT"], os.environ["RELEASE_VERSION"])
    host = os.environ["DEPLOY_HOST"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]{0,252}", host):
        raise ValueError("Invalid deployment hostname")
    command = [args.operation]
    if args.operation == "deploy":
        if args.scope not in {"dev", "qa"}:
            raise ValueError("Production requires explicit promotion")
        command.append(args.scope)
    elif (args.operation, args.scope) not in {("attest", "qa"), ("promote", "production")}:
        raise ValueError("Invalid key scope")
    command += [os.environ["DIGEST"], expected["commit"], expected["version"]]
    if args.operation != "deploy":
        command.append(run_id(os.environ["CANDIDATE_RUN"]))
    with tempfile.TemporaryDirectory(prefix="chat-ssh-") as directory:
        key, known = Path(directory) / "key", Path(directory) / "known_hosts"
        for path, value in ((key, os.environ["DEPLOY_KEY"]), (known, os.environ["KNOWN_HOSTS"])):
            path.write_text(value + "\n")
            path.chmod(0o600)
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "ConnectTimeout=15",
                "-o",
                "UserKnownHostsFile=" + str(known),
                "-i",
                str(key),
                "kwilliams@" + host,
                " ".join(command),
            ],
            input=(os.environ["GH_TOKEN"] + "\n").encode(),
            capture_output=True,
            timeout=600,
        )
        if result.returncode:
            raise RuntimeError(
                "Remote release failed; inspect the protected host last-attempt.json"
            )
        record = json.loads(result.stdout)
        if any(record.get(field) != value for field, value in expected.items()):
            raise ValueError("Remote record identity mismatch")
        print(json.dumps(record))


if __name__ == "__main__":
    main()
