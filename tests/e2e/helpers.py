"""Shared browser authentication helpers; real server throttling remains enabled."""

import os
import time

from playwright.sync_api import expect

URL = os.environ.get("E2E_URL", "http://localhost:9001")
ADMIN_EMAIL = os.environ.get("E2E_ADMIN_EMAIL", "admin@example.org")
ADMIN_PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD", "browser-workshop-admin-1234")


_login_bucket = -1
_login_count = 0


def reserve_login():
    """Keep real browser logins within the app's real ten/minute IP limit."""
    global _login_bucket, _login_count
    bucket = int(time.time() // 60)
    if bucket != _login_bucket:
        _login_bucket, _login_count = bucket, 0
    if _login_count >= 10:
        time.sleep(max(0, (_login_bucket + 1) * 60 - time.time()) + 0.1)
        _login_bucket, _login_count = int(time.time() // 60), 0
    _login_count += 1


def sign_in(page, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    page.goto(URL)
    page.get_by_label("Email", exact=True).fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    reserve_login()
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.get_by_role("button", name="＋ New conversation", exact=True)).to_be_visible()
