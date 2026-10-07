"""Bounded acceptance probe for the two synthetic public preview environments.

This is separate from the destructive localhost lab harness. It cannot target
production, register accounts, change roles or contact a paid LLM/mail provider.
An operator provisions one approved ordinary QA account before CI is enabled.
"""

import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

URLS = {"dev": "https://dev.firehose360.com", "qa": "https://qa.firehose360.com"}


def check_identity(value, commit, version, schema=None):
    if (
        value.get("status") != "ok"
        or value.get("commit") != commit
        or value.get("version") != version
        or not value.get("schema")
        or (schema is not None and value.get("schema") != schema)
        or value.get("provider") != "mock"
    ):
        raise ValueError("Preview health does not match the tested synthetic release")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=URLS)
    parser.add_argument("commit")
    parser.add_argument("version")
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    url = URLS[args.stage]
    deployed = json.loads(Path(args.stage + "-deployment.json").read_text())
    with sync_playwright() as playwright:
        request = playwright.request.new_context(base_url=url, timeout=15000)
        response = request.get("/api/health")
        if not response.ok:
            raise ValueError("Public HTTPS readiness failed")
        health = response.json()
        check_identity(health, args.commit, args.version, deployed["schema"])
        evidence = {
            "environment": args.stage,
            "url": url,
            **health,
            "checks": ["https", "commit/version/schema", "mock provider"],
        }
        if args.browser:
            options = request.get("/api/auth/options").json()
            if options.get("email_enabled"):
                raise ValueError("QA mail must be disabled")
            email, password = os.environ["QA_SMOKE_EMAIL"], os.environ["QA_SMOKE_PASSWORD"]
            authentication = request.post(
                "/api/auth/login",
                data={"email": email, "password": password},
                headers={"Origin": url},
            )
            if not authentication.ok:
                raise ValueError("Synthetic QA account cannot sign in")
            login = authentication.json()
            token = login["access_token"]
            if (
                login["user"]["role"] != "user"
                or not login["user"]["approved"]
                or not login["user"]["active"]
            ):
                raise ValueError("QA probe requires an approved ordinary synthetic user")
            headers = {"Authorization": "Bearer " + token, "Origin": url}
            cid = None
            browser = playwright.chromium.launch()
            context = browser.new_context(base_url=url)
            try:
                page = context.new_page()
                page.goto("/", wait_until="networkidle")
                page.get_by_label("Email", exact=True).fill(email)
                page.get_by_label("Password", exact=True).fill(password)
                page.get_by_role("button", name="Sign in", exact=True).click()
                create = page.get_by_role("button", name="＋ New conversation", exact=True)
                expect(create).to_be_visible()
                with page.expect_response(
                    lambda r: r.url == url + "/api/conversations" and r.request.method == "POST"
                ) as created:
                    create.click()
                cid = created.value.json()["id"]
                prompt = "QA acceptance for " + args.commit[:12]
                page.get_by_label("Message", exact=True).fill(prompt)
                page.get_by_role("button", name="Send", exact=False).click()
                expect(page.locator(".message.assistant")).to_contain_text(
                    "Workshop reply: " + prompt, timeout=30000
                )
                expect(page.get_by_role("button", name="Send", exact=False)).to_be_visible(
                    timeout=30000
                )
                saved = request.get("/api/conversations/" + cid, headers=headers)
                if not saved.ok or not any(
                    item["role"] == "assistant" and prompt in item["content"]
                    for item in saved.json()["messages"]
                ):
                    raise ValueError("Streamed response was not persisted")
                page.reload(wait_until="networkidle")
                expect(create).to_be_visible()
                page.get_by_role("navigation", name="Conversations").get_by_role(
                    "button"
                ).first.click()
                expect(page.locator(".message.assistant")).to_contain_text(prompt)
                page.get_by_role("button", name="Sign out", exact=True).click()
                expect(page.get_by_role("button", name="Sign in", exact=True)).to_be_visible()
                evidence["checks"] += [
                    "mail disabled",
                    "ordinary login",
                    "browser stream",
                    "persisted history",
                    "refresh after reload",
                    "logout",
                ]
            finally:
                context.close()
                browser.close()
                if cid and not request.delete("/api/conversations/" + cid, headers=headers).ok:
                    raise ValueError("Synthetic QA conversation cleanup failed")
                if not request.post("/api/auth/logout", headers={"Origin": url}).ok:
                    raise ValueError("Synthetic probe session cleanup failed")
        Path(args.stage + "-smoke.json").write_text(json.dumps(evidence, indent=2) + "\n")
        request.dispose()


if __name__ == "__main__":
    main()
