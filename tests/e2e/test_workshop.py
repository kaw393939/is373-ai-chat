"""Browser journeys against a migrated, seeded application with a mock provider."""

import os
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("E2E_URL", "http://localhost:9001")
ADMIN_EMAIL = os.environ.get("E2E_ADMIN_EMAIL", "admin@example.org")
ADMIN_PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD", "browser-workshop-admin-1234")


def sign_in(page, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    page.goto(URL)
    page.get_by_label("Email", exact=True).fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.get_by_role("button", name="New conversation")).to_be_visible()


def test_registration_approval_chat_and_session_reload():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        student = browser.new_page()
        errors = []
        student.on("pageerror", lambda error: errors.append(str(error)))
        email = f"learner-{uuid4().hex[:8]}@example.org"
        password = "learner-workshop-password-123"
        student.goto(URL)
        student.get_by_role("button", name="Need an account? Register").click()
        student.get_by_label("Email", exact=True).fill(email)
        student.get_by_label("Password", exact=True).fill(password)
        student.get_by_role("button", name="Request account").click()
        expect(student.get_by_role("status")).to_contain_text("administrator")
        admin = browser.new_page()
        sign_in(admin)
        admin.get_by_role("button", name="Administration").click()
        admin.get_by_role("button", name=f"Edit {email}", exact=True).click()
        admin.get_by_label("approved", exact=True).check()
        admin.get_by_role("button", name="Save account", exact=True).click()
        expect(admin.get_by_role("dialog")).not_to_be_visible()
        sign_in(student, email, password)
        expect(student.get_by_role("button", name="Administration")).not_to_be_visible()
        student.get_by_label("Message", exact=True).fill(
            "Explain the adapter pattern <script>alert(1)</script>"
        )
        student.get_by_role("button", name="Send", exact=False).click()
        expect(student.locator(".message.assistant")).to_contain_text("adapter", timeout=15000)
        expect(student.get_by_role("button", name="Send", exact=False)).to_be_visible(timeout=15000)
        student.reload()
        expect(student.get_by_role("button", name="New conversation")).to_be_visible()
        student.get_by_role("navigation", name="Conversations").get_by_role("button").first.click()
        expect(student.locator(".message.assistant")).to_contain_text("<script>alert(1)</script>")
        student.once("dialog", lambda dialog: dialog.accept("Adapter lesson"))
        student.get_by_role("button", name="Rename", exact=True).click()
        expect(student.get_by_role("heading", name="Adapter lesson")).to_be_visible()
        student.get_by_role("button", name="Retry last prompt").click()
        expect(student.locator(".message.assistant")).to_have_count(2)
        expect(student.get_by_role("button", name="Send", exact=False)).to_be_visible(timeout=15000)
        student.once("dialog", lambda dialog: dialog.accept())
        student.get_by_role("button", name="Delete", exact=True).click()
        expect(student.locator(".message")).to_have_count(0)
        assert errors == []
        browser.close()


def test_admin_budget_controls_and_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        sign_in(page)
        page.get_by_role("button", name="Administration").click()
        expect(page.get_by_role("heading", name="Role defaults")).to_be_visible()
        form = page.locator(".budget-form").filter(
            has=page.get_by_role("button", name="Save user budget")
        )
        form.get_by_label("Requests / day", exact=True).fill("50")
        form.get_by_role("button", name="Save user budget").click()
        expect(form.get_by_label("Requests / day", exact=True)).to_have_value("50")
        expect(page.get_by_role("heading", name="Host resources", exact=False)).to_be_visible()
        Path("artifacts").mkdir(exist_ok=True)
        page.screenshot(path="artifacts/admin.png", full_page=True)
        page.get_by_role("button", name="New conversation").click()
        page.get_by_label("Message", exact=True).fill("word " * 120)
        page.get_by_role("button", name="Send", exact=False).click()
        expect(page.locator(".message.assistant")).to_contain_text("Workshop", timeout=15000)
        page.get_by_role("button", name="Stop", exact=True).click()
        expect(page.get_by_role("button", name="Send", exact=False)).to_be_visible(timeout=15000)
        page.screenshot(path="artifacts/chat.png", full_page=True)
        page.get_by_role("button", name="Sign out").click()
        expect(page.get_by_role("heading", name="Welcome back")).to_be_visible()
        browser.close()
