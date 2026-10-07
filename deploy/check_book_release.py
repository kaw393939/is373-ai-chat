"""Require the footer's immutable downloadable edition before preview deployment."""

import json
import os
import re
import time
from pathlib import Path

from release_policy import GitHub, version


def edition(source):
    tags = re.findall(r"/releases/tag/(book-v[0-9A-Za-z.-]+)", source)
    if len(tags) != 1:
        raise ValueError("Footer must declare one fixed downloadable book edition")
    return "book-v" + version(tags[0].removeprefix("book-v"))


def required_assets(tag):
    name = "from-request-to-release-v" + tag.removeprefix("book-v") + ".zip"
    return {name, name + ".sha256", "book-build.json"}


def accepted(release, tag):
    if (
        not release
        or release.get("tag_name") != tag
        or release.get("draft") is not False
        or release.get("immutable") is not True
    ):
        return False
    names = {
        item["name"]
        for item in release.get("assets", [])
        if item.get("state") == "uploaded" and item.get("size", 0) > 0
    }
    return required_assets(tag) <= names


def wait_for_edition(api, tag, clock=time.monotonic, sleep=time.sleep):
    """Allow a bounded publication race; API requests have a 20-second timeout."""
    deadline = clock() + 300
    while clock() + 20 <= deadline:
        try:
            release = api.get("/releases/tags/" + tag, missing=True)
        except RuntimeError:
            release = None  # Transient API failure is bounded by the same deadline.
        if accepted(release, tag):
            return release
        remaining = deadline - clock() - 20
        if remaining <= 0:
            break
        sleep(min(10, remaining))
    raise RuntimeError("Downloadable book edition was not ready within five minutes")


def main():
    tag = edition(Path("frontend/src/ProjectFooter.tsx").read_text())
    release = wait_for_edition(GitHub(os.environ["GH_TOKEN"]), tag)
    record = {
        "status": "published",
        "tag": tag,
        "release_id": release["id"],
        "immutable": True,
        "source_target": release["target_commitish"],
        "assets": [
            {key: item[key] for key in ("name", "size", "digest")}
            for item in release["assets"]
            if item["name"] in required_assets(tag)
        ],
    }
    Path("dev-book-release.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Downloadable edition is published: " + tag)


if __name__ == "__main__":
    main()
