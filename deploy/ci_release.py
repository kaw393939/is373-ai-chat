"""Small Actions helper: validate metadata and write reviewable release evidence."""

import argparse
import json
import os
import re
from pathlib import Path

from release_policy import GitHub, identity, run_id, unused_version, verify_run, version


def read_candidate(path):
    value = json.loads(Path(path).read_text())
    digest = value["image"].split("@", 1)[1]
    expected = identity(digest, value["commit"], value["version"])
    if expected["image"] != value["image"]:
        raise ValueError("Candidate image belongs to another repository")
    run_id(value["run_id"])
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["version", "candidate", "preflight", "notes"])
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    if args.operation == "version":
        print(version(Path("VERSION").read_text().strip()))
        return
    if args.operation == "candidate":
        record = {
            **identity(
                args.value, os.environ["GITHUB_SHA"], version(Path("VERSION").read_text().strip())
            ),
            "run_id": run_id(os.environ["GITHUB_RUN_ID"]),
            "qa_run": "https://github.com/kaw393939/is373-ai-chat/actions/runs/"
            + os.environ["GITHUB_RUN_ID"],
        }
        Path("candidate.json").write_text(json.dumps(record, indent=2) + "\n")
        return
    record = read_candidate(args.value)
    if args.operation == "preflight":
        if run_id(os.environ["CANDIDATE_RUN"]) != record["run_id"]:
            raise ValueError("Artifact belongs to another delivery run")
        api = GitHub(os.environ["GH_TOKEN"])
        verify_run(api, record["run_id"], record)
        unused_version(api, record["version"])
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            for key in ("commit", "version", "run_id"):
                stream.write(key + "=" + record[key] + "\n")
            stream.write("digest=" + record["image"].split("@")[1] + "\n")
        return
    deployed = json.loads(Path("production.json").read_text())
    if deployed["status"] != "deployed" or any(
        deployed[key] != record[key] for key in ("image", "commit", "version")
    ):
        raise ValueError("Production record does not match selected QA candidate")
    api = GitHub(os.environ["GH_TOKEN"])
    previous = api.get("/releases/latest", missing=True)
    if previous:
        commits = api.get("/compare/" + previous["tag_name"] + "..." + record["commit"])["commits"]
    else:
        commits = api.get("/commits?sha=" + record["commit"] + "&per_page=100")
    trace = [
        {
            "commit": item["sha"],
            "url": item["html_url"],
            "subject": item["commit"]["message"].splitlines()[0],
        }
        for item in commits
    ]
    Path("atomic-commits.json").write_text(json.dumps(trace, indent=2) + "\n")
    numbers = sorted(
        {int(number) for item in trace for number in re.findall(r"#([1-9][0-9]*)", item["subject"])}
    )
    issue_links = (
        ", ".join(
            f"[#{number}](https://github.com/kaw393939/is373-ai-chat/issues/{number})"
            for number in numbers
        )
        or "Consult the linked commit history."
    )
    migration = (
        "This first formal 2.0.0 release follows untagged legacy 1.0.0. Administrator MFA changes login compatibility; the matching frontend is included."
        if record["version"] == "2.0.0"
        else "Review the linked migration and configuration notes for this version."
    )
    text = f"""Application {record["version"]} promotes the accepted QA artifact without rebuilding it.

Source: https://github.com/kaw393939/is373-ai-chat/commit/{record["commit"]}
QA evidence: {record["qa_run"]}
Image: `{record["image"]}`
Schema: `{deployed["previous_schema"]}` → `{deployed["schema"]}`

Migration/recovery: https://github.com/kaw393939/is373-ai-chat/blob/{record["commit"]}/docs/install-and-delivery.md#database-deployment-and-recovery
Version contract: https://github.com/kaw393939/is373-ai-chat/blob/{record["commit"]}/docs/decisions/0001-environments-and-releases.md#version-contract
Canonical lesson: https://github.com/kaw393939/is373-ai-chat/blob/{record["commit"]}/book/08-delivery.md
Referenced work: {issue_links}
Atomic commits: attached `atomic-commits.json` (up to 100 commits for the first release; subsequent releases compare with the latest stable release). The linked source history remains the complete trace.

{migration} Automatic rollback is allowed only when the schema is unchanged. Otherwise the app stops and an operator must choose a reviewed forward fix or restore the pre-migration backup. No schema downgrade runs automatically. A container replacement interrupts streams; zero downtime is not claimed.

Attached records, SBOM, vulnerability report and QA probe evidence persist beyond Actions artifact retention. A green fixable HIGH/CRITICAL gate does not establish absence of unfixed vulnerabilities.
"""
    Path("release-notes.md").write_text(text)


if __name__ == "__main__":
    main()
