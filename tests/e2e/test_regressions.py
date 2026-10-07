"""Deterministic UI races and keyboard behavior on the guarded local browser app."""

from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect, sync_playwright

from tests.e2e.helpers import URL, reserve_login, sign_in


def conversation(cid, title, messages=None, cursor=None):
    return {
        "id": cid,
        "title": title,
        "messages": messages or [],
        "runs": [],
        "messages_cursor": cursor,
        "runs_cursor": None,
    }


def test_delayed_navigation_and_logout_stream_do_not_restore_old_view():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors, held_a, held_stream = [], [], []
        phase = {"fresh": False}
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/api/conversations?*",
            lambda route: route.fulfill(
                json={
                    "items": [{"id": "fresh", "title": "Fresh session"}]
                    if phase["fresh"]
                    else [
                        {"id": "a", "title": "Conversation A"},
                        {"id": "b", "title": "Conversation B"},
                    ],
                    "next_cursor": None,
                }
            ),
        )
        page.route("**/api/conversations/a", lambda route: held_a.append(route))
        page.route(
            "**/api/conversations/b",
            lambda route: route.fulfill(
                json=conversation(
                    "b",
                    "Conversation B",
                    [{"id": "b1", "role": "assistant", "content": "The selected B view"}],
                )
            ),
        )
        page.route("**/api/conversations/b/stream", lambda route: held_stream.append(route))
        # A different approved account must never inherit the first owner's work.
        from uuid import uuid4

        email = f"switch-{uuid4().hex[:8]}@example.org"
        password = "switch-learner-password-123"
        enrollment, approval = browser.new_page(), browser.new_page()
        enrollment.goto(URL)
        enrollment.get_by_role("button", name="Need an account? Register").click()
        enrollment.get_by_label("Email", exact=True).fill(email)
        enrollment.get_by_label("Password", exact=True).fill(password)
        enrollment.get_by_role("button", name="Request account").click()
        expect(enrollment.get_by_role("status")).to_contain_text("administrator")
        sign_in(approval)
        approval.get_by_role("button", name="Administration").click()
        approval.get_by_role("button", name=f"Edit {email}", exact=True).click()
        approval.get_by_label("approved", exact=True).check()
        approval.get_by_role("button", name="Save account", exact=True).click()
        expect(approval.get_by_role("dialog")).not_to_be_visible()
        enrollment.close()
        approval.close()
        sign_in(page)
        nav = page.get_by_role("navigation", name="Conversations")
        nav.get_by_role("button", name="Conversation A", exact=True).click()
        expect(page.get_by_role("heading", name="Conversation A", exact=True)).to_be_visible()
        nav.get_by_role("button", name="Conversation B", exact=True).click()
        expect(page.locator(".messages")).to_contain_text("The selected B view")
        assert len(held_a) == 1
        held_a[0].fulfill(
            json=conversation(
                "a",
                "Conversation A",
                [{"id": "a1", "role": "assistant", "content": "Obsolete A response"}],
            )
        )
        expect(page.get_by_role("heading", name="Conversation B", exact=True)).to_be_visible()
        expect(page.locator(".messages")).not_to_contain_text("Obsolete A response")
        page.get_by_label("Message", exact=True).fill("Old session prompt")
        page.get_by_role("button", name="Send", exact=False).click()
        expect(page.get_by_role("button", name="Stop", exact=True)).to_be_visible()
        page.get_by_role("button", name="Sign out", exact=True).click()
        expect(page.get_by_role("heading", name="Welcome back")).to_be_visible()
        phase["fresh"] = True
        page.get_by_label("Email", exact=True).fill(email)
        page.get_by_label("Password", exact=True).fill(password)
        reserve_login()
        page.get_by_role("button", name="Sign in", exact=True).click()
        expect(page.get_by_role("button", name="＋ New conversation", exact=True)).to_be_visible()
        assert len(held_stream) == 1
        held_stream[0].fulfill(
            content_type="text/event-stream",
            body='event: started\ndata: {"run_id":"obsolete"}\n\nevent: delta\ndata: {"text":"Obsolete private reply"}\n\nevent: completed\ndata: {"status":"complete","tokens":null}\n\n',
        )
        expect(nav.get_by_role("button", name="Fresh session", exact=True)).to_be_visible()
        expect(page.locator(".message")).to_have_count(0)
        expect(nav.get_by_role("button", name="Conversation B", exact=True)).not_to_be_visible()
        expect(page.get_by_role("button", name="Administration")).not_to_be_visible()
        assert errors == []
        browser.close()


def test_two_tabs_serialize_real_refresh_and_logout_invalidates_pending_refresh():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        a, b = context.new_page(), context.new_page()
        sign_in(a)
        b.goto(URL)
        expect(b.get_by_role("button", name="＋ New conversation", exact=True)).to_be_visible()
        held, statuses = [], []
        hold = {"next": True}

        def refresh_route(route):
            if hold["next"]:
                hold["next"] = False
                held.append(route)
            else:
                route.continue_()

        context.route("**/api/auth/refresh", refresh_route)
        context.on(
            "response",
            lambda response: (
                statuses.append(response.status)
                if response.url.endswith("/api/auth/refresh")
                else None
            ),
        )
        with a.expect_request("**/api/auth/refresh"):
            a.reload(wait_until="commit")
        b.reload(wait_until="commit")
        b.wait_for_function(
            "async () => (await navigator.locks.query()).pending.some(lock => lock.name === '373-auth-cookie')"
        )
        assert len(held) == 1  # The second tab has not sent the shared old cookie.
        held.pop().continue_()
        for page in (a, b):
            expect(
                page.get_by_role("button", name="＋ New conversation", exact=True)
            ).to_be_visible()
        assert statuses == [200, 200]
        # Hold another genuine rotation while logout in the other tab invalidates UI.
        hold["next"] = True
        with a.expect_request("**/api/auth/refresh"):
            a.reload(wait_until="commit")
        b.get_by_role("button", name="Sign out", exact=True).click()
        expect(b.get_by_role("heading", name="Welcome back")).to_be_visible()
        assert len(held) == 1
        held.pop().continue_()
        expect(a.get_by_role("heading", name="Welcome back")).to_be_visible()
        expect(b.get_by_role("button", name="＋ New conversation", exact=True)).not_to_be_visible()
        # No bearer, MFA key, or recovery code is persisted for cross-tab coordination.
        assert a.evaluate(
            "Object.keys(localStorage).every(key => key === '373-session-generation')"
        )
        context.close()
        browser.close()


def test_keyboard_dialog_focus_escape_restore_and_error_announcement():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route(
            "**/api/conversations?*",
            lambda route: route.fulfill(
                json={
                    "items": [{"id": "keyboard", "title": "Keyboard lesson"}],
                    "next_cursor": None,
                }
            ),
        )
        page.route(
            "**/api/conversations/keyboard",
            lambda route: (
                route.fulfill(json=conversation("keyboard", "Keyboard lesson"))
                if route.request.method == "GET"
                else route.fulfill(status=409, json={"detail": "A teaching conflict; retry later"})
            ),
        )
        user = {
            "id": "other",
            "email": "keyboard@example.org",
            "role": "user",
            "active": True,
            "approved": False,
            "email_verified": True,
            "daily_requests": None,
            "daily_units": None,
            "max_concurrent": None,
        }
        page.route(
            "**/api/admin/users?*",
            lambda route: route.fulfill(json={"items": [user], "next_cursor": None}),
        )
        sign_in(page)
        page.get_by_role("navigation", name="Conversations").get_by_role(
            "button", name="Keyboard lesson"
        ).click()
        rename = page.get_by_role("button", name="Rename", exact=True)
        rename.focus()
        page.keyboard.press("Enter")
        dialog = page.get_by_role("dialog", name="Rename conversation")
        expect(page.get_by_label("Conversation title")).to_be_focused()
        page.keyboard.press("Shift+Tab")
        expect(dialog.get_by_role("button", name="Cancel")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_label("Conversation title")).to_be_focused()
        page.keyboard.press("Escape")
        expect(dialog).not_to_be_visible()
        expect(rename).to_be_focused()
        rename.press("Enter")
        dialog.get_by_role("button", name="Save title").click()
        expect(dialog.get_by_role("alert")).to_contain_text("teaching conflict")
        expect(dialog).to_be_visible()
        page.keyboard.press("Escape")
        delete = page.get_by_role("button", name="Delete", exact=True)
        delete.focus()
        delete.press("Enter")
        dialog = page.get_by_role("dialog", name="Delete conversation?", exact=True)
        expect(dialog.get_by_role("button", name="Cancel")).to_be_focused()
        page.keyboard.press("Tab")
        expect(dialog.get_by_role("button", name="Delete conversation", exact=True)).to_be_focused()
        page.keyboard.press("Escape")
        expect(delete).to_be_focused()
        page.get_by_role("button", name="Administration").click()
        edit = page.get_by_role("button", name="Edit keyboard@example.org", exact=True)
        edit.focus()
        edit.press("Enter")
        dialog = page.get_by_role("dialog", name="Edit account", exact=True)
        expect(dialog.get_by_label("Role", exact=True)).to_be_focused()
        page.keyboard.press("Shift+Tab")
        expect(dialog.get_by_role("button", name="Cancel")).to_be_focused()
        page.keyboard.press("Escape")
        expect(edit).to_be_focused()
        browser.close()


def test_paged_history_and_account_search_reach_beyond_old_limits():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        chats = [{"id": f"chat-{index}", "title": f"Lesson {index:03}"} for index in range(150)]
        users = [
            {
                "id": f"person-{index}",
                "email": f"person-{index:03}@example.org",
                "role": "user",
                "active": True,
                "approved": True,
                "email_verified": True,
                "daily_requests": None,
                "daily_units": None,
                "max_concurrent": None,
            }
            for index in range(261)
        ]
        messages = [
            {"id": f"message-{index}", "role": "assistant", "content": f"History row {index:03}"}
            for index in range(150)
        ]

        def list_page(route, source, field):
            query = parse_qs(urlparse(route.request.url).query)
            matches = [item for item in source if query.get("q", [""])[0] in item[field]]
            offset = int(query.get("cursor", ["0"])[0])
            end = offset + 50
            route.fulfill(
                json={
                    "items": matches[offset:end],
                    "next_cursor": str(end) if end < len(matches) else None,
                }
            )

        page.route("**/api/conversations?*", lambda route: list_page(route, chats, "title"))
        page.route("**/api/admin/users?*", lambda route: list_page(route, users, "email"))
        page.route(
            "**/api/conversations/chat-149",
            lambda route: route.fulfill(
                json=conversation("chat-149", "Lesson 149", messages[100:], "100")
            ),
        )

        def older(route):
            offset = int(parse_qs(urlparse(route.request.url).query)["cursor"][0])
            start = max(0, offset - 50)
            route.fulfill(
                json={"items": messages[start:offset], "next_cursor": str(start) if start else None}
            )

        page.route("**/api/conversations/chat-149/messages?*", older)
        sign_in(page)
        nav = page.get_by_role("navigation", name="Conversations")
        for count in [100, 150]:
            nav.get_by_role("button", name="Load more conversations").click()
            expect(
                nav.get_by_role("button", name=f"Lesson {count - 1:03}", exact=True)
            ).to_be_visible()
        assert nav.get_by_role("button").count() == 150
        page.get_by_placeholder("Find a conversation…").fill("149")
        expect(nav.get_by_role("button", name="Lesson 149", exact=True)).to_be_visible()
        expect(nav.get_by_role("button")).to_have_count(1)
        nav.get_by_role("button", name="Lesson 149", exact=True).click()
        expect(page.locator(".message")).to_have_count(50)
        for count in [100, 150]:
            page.get_by_role("button", name="Load older messages").click()
            expect(page.locator(".message")).to_have_count(count)
        expect(page.locator(".message").first).to_contain_text("History row 000")
        expect(page.locator(".message").last).to_contain_text("History row 149")
        page.get_by_role("button", name="Administration").click()
        for count in [100, 150, 200, 250, 261]:
            page.get_by_role("button", name="Load more accounts").click()
            expect(
                page.get_by_role("status").filter(has_text=f"{count} accounts shown")
            ).to_be_visible()
        assert (
            page.locator("table tbody tr td:first-child").filter(has_text="person-").count() == 261
        )
        page.get_by_label("Search account email").fill("260")
        expect(page.get_by_role("cell", name="person-260@example.org", exact=True)).to_be_visible()
        expect(page.get_by_role("status").filter(has_text="1 accounts shown")).to_be_visible()
        expect(page.get_by_role("navigation", name="Project resources")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        browser.close()


def test_optional_authenticator_enrollment_recovery_and_replacement():
    import base64
    import hashlib
    import hmac
    import struct
    import time
    from uuid import uuid4

    def totp(secret):
        key = base64.b32decode(secret + "=" * (-len(secret) % 8))
        digest = hmac.new(key, struct.pack(">Q", int(time.time()) // 30), hashlib.sha1).digest()
        offset = digest[-1] & 15
        return f"{(struct.unpack('>I', digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000:06d}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        student_context = browser.new_context()
        student, admin = student_context.new_page(), browser.new_page()
        email = f"factor-{uuid4().hex[:8]}@example.org"
        password = "authenticator-learner-password-123"
        student.goto(URL)
        student.get_by_role("button", name="Need an account? Register").click()
        student.get_by_label("Email", exact=True).fill(email)
        student.get_by_label("Password", exact=True).fill(password)
        student.get_by_role("button", name="Request account").click()
        expect(student.get_by_role("status")).to_contain_text("administrator")
        sign_in(admin)
        admin.get_by_role("button", name="Administration").click()
        admin.get_by_role("button", name=f"Edit {email}", exact=True).click()
        admin.get_by_label("approved", exact=True).check()
        admin.get_by_role("button", name="Save account", exact=True).click()
        expect(admin.get_by_role("dialog")).not_to_be_visible()
        sign_in(student, email, password)
        student.get_by_role("button", name="Account", exact=False).click()
        student.get_by_label("Password to enable authenticator", exact=True).fill(password)
        student.get_by_role("button", name="Set up authenticator", exact=True).click()
        secret_field = student.get_by_label("New authenticator setup key", exact=True)
        expect(secret_field).to_be_visible()
        secret = secret_field.input_value()
        student.get_by_label("New authenticator code", exact=True).fill(totp(secret))
        with student.expect_response("**/api/auth/mfa/confirm") as confirmation:
            student.get_by_role("button", name="Confirm replacement", exact=True).click()
        assert confirmation.value.status == 200, confirmation.value.json().get(
            "detail", "MFA confirm failed"
        )
        expect(student.locator(".recovery-codes li")).to_have_count(10)
        recovery_codes = student.locator(".recovery-codes code").all_text_contents()
        storage = student.evaluate("JSON.stringify(localStorage)")
        assert secret not in storage and all(code not in storage for code in recovery_codes)
        student.get_by_role("button", name="I saved my codes", exact=True).click()
        expect(student.get_by_role("heading", name="Welcome back")).to_be_visible()
        student.get_by_label("Email", exact=True).fill(email)
        student.get_by_label("Password", exact=True).fill(password)
        reserve_login()
        student.get_by_role("button", name="Sign in", exact=True).click()
        expect(student.get_by_role("heading", name="Verify your second factor")).to_be_visible()
        expect(
            student.get_by_role("button", name="＋ New conversation", exact=True)
        ).not_to_be_visible()
        student.get_by_label("Authenticator or recovery code", exact=True).fill(recovery_codes[0])
        student.get_by_role("button", name="Verify code", exact=True).click()
        expect(
            student.get_by_role("button", name="＋ New conversation", exact=True)
        ).to_be_visible()
        peer = student.context.new_page()
        peer.goto(URL)
        expect(peer.get_by_role("button", name="＋ New conversation", exact=True)).to_be_visible()
        student.get_by_role("button", name="Account", exact=False).click()
        student.get_by_label("Password to replace authenticator", exact=True).fill(password)
        student.get_by_label("Current authenticator or recovery code", exact=True).fill(
            recovery_codes[1]
        )
        student.get_by_role("button", name="Replace authenticator", exact=True).click()
        expect(secret_field).to_be_visible()
        replacement = secret_field.input_value()
        assert replacement != secret
        stale = {"first": True}

        def expire_first_confirmation(route):
            if stale["first"]:
                stale["first"] = False
                route.fulfill(status=401, json={"detail": "Invalid or expired session"})
            else:
                route.continue_()

        student.route("**/api/auth/mfa/confirm", expire_first_confirmation)
        student.get_by_label("New authenticator code", exact=True).fill(totp(replacement))
        with student.expect_response(
            lambda response: (
                response.url.endswith("/api/auth/mfa/confirm") and response.status == 200
            )
        ) as confirmation:
            student.get_by_role("button", name="Confirm replacement", exact=True).click()
        assert confirmation.value.status == 200, confirmation.value.json().get(
            "detail", "MFA confirm failed"
        )
        expect(student.locator(".recovery-codes li")).to_have_count(10)
        replacement_codes = student.locator(".recovery-codes code").all_text_contents()
        assert replacement_codes != recovery_codes
        expect(peer.get_by_role("heading", name="Welcome back")).to_be_visible()
        expect(
            peer.get_by_role("button", name="＋ New conversation", exact=True)
        ).not_to_be_visible()
        student.get_by_role("button", name="I saved my codes", exact=True).click()
        browser.close()


def test_owned_export_collects_all_pages_and_cancels_private_work(tmp_path):
    import json

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        sign_in(page)
        page.get_by_role("button", name="Account", exact=False).click()
        expect(page.get_by_role("heading", name="Enable an authenticator")).to_be_visible()
        page.clock.install()
        seen = []

        def export_page(route):
            query = parse_qs(urlparse(route.request.url).query)
            section = query["section"][0]
            cursor = query.get("cursor", [None])[0]
            seen.append((section, cursor))
            items = (
                [{"id": "owned-first"}, {"id": "owned-second"}]
                if section == "conversations" and cursor is None
                else [{"id": "owned-third"}]
                if section == "conversations"
                else [{"id": f"owned-{section}"}]
            )
            route.fulfill(
                json={
                    "account": {},
                    "format": "firehose360-owned-v1",
                    "section": section,
                    "items": items,
                    "next_cursor": "older"
                    if section == "conversations" and cursor is None
                    else None,
                }
            )

        page.route("**/api/account/export?*", export_page)
        page.get_by_role("button", name="Download my account data", exact=True).click()
        expect(
            page.get_by_role("status").filter(has_text="Collected 2 conversations")
        ).to_be_visible()
        page.clock.fast_forward(6100)
        expect(
            page.get_by_role("status").filter(has_text="Collected 3 conversations")
        ).to_be_visible()
        page.clock.fast_forward(6100)
        expect(page.get_by_role("status").filter(has_text="Collected 1 messages")).to_be_visible()
        with page.expect_download() as received:
            page.clock.fast_forward(6100)
        path = tmp_path / "owned-account.json"
        received.value.save_as(path)
        data = json.loads(path.read_text())
        assert data["format"] == "firehose360-owned-v1"
        assert [item["id"] for item in data["conversations"]] == [
            "owned-first",
            "owned-second",
            "owned-third",
        ]
        assert data["messages"] == [{"id": "owned-messages"}]
        assert data["runs"] == [{"id": "owned-runs"}]
        assert seen == [
            ("conversations", None),
            ("conversations", "older"),
            ("messages", None),
            ("runs", None),
        ]
        # A cancellation aborts a held private page and never creates a second file.
        page.unroute("**/api/account/export?*", export_page)
        held, downloads = [], []
        page.on("download", lambda download: downloads.append(download))
        page.route("**/api/account/export?*", lambda route: held.append(route))
        with page.expect_request("**/api/account/export?*"):
            page.get_by_role("button", name="Download my account data", exact=True).click()
        page.get_by_role("button", name="Cancel export", exact=True).click()
        expect(page.get_by_role("status").filter(has_text="Export cancelled")).to_be_visible()
        assert len(held) == 1
        held[0].fulfill(json={"items": [{"id": "obsolete-private"}], "next_cursor": None})
        expect(
            page.get_by_role("button", name="Download my account data", exact=True)
        ).to_be_enabled()
        assert downloads == []
        browser.close()


def test_delayed_admin_mutation_preserves_the_current_server_search():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        alice = {
            "id": "alice",
            "email": "alice@example.org",
            "role": "user",
            "active": True,
            "approved": True,
            "email_verified": True,
            "daily_requests": None,
            "daily_units": None,
            "max_concurrent": None,
        }
        bob = {**alice, "id": "bob", "email": "bob@example.org"}
        held = []

        def accounts(route):
            q = parse_qs(urlparse(route.request.url).query).get("q", [""])[0]
            route.fulfill(
                json={
                    "items": [person for person in [alice, bob] if q in person["email"]],
                    "next_cursor": None,
                }
            )

        page.route("**/api/admin/users?*", accounts)
        page.route("**/api/admin/budgets/user", lambda route: held.append(route))
        sign_in(page)
        page.get_by_role("button", name="Administration").click()
        expect(page.get_by_role("cell", name="bob@example.org", exact=True)).to_be_visible()
        form = page.locator(".budget-form").filter(
            has=page.get_by_role("button", name="Save user budget")
        )
        form.get_by_role("button", name="Save user budget").click()
        page.get_by_label("Search account email", exact=True).fill("alice")
        expect(page.get_by_role("status").filter(has_text="1 accounts shown")).to_be_visible()
        assert len(held) == 1
        with page.expect_response(lambda response: "/api/admin/users?" in response.url):
            held[0].fulfill(json={"message": "Budget saved"})
        expect(page.get_by_label("Search account email", exact=True)).to_have_value("alice")
        expect(page.get_by_role("cell", name="alice@example.org", exact=True)).to_be_visible()
        expect(page.get_by_role("cell", name="bob@example.org", exact=True)).not_to_be_visible()
        browser.close()


def test_provider_markdown_cannot_execute_html_or_fetch_remote_images():
    """Provider text is data, including hostile HTML, links and image trackers."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        remote_requests = []
        page.on(
            "request",
            lambda request: (
                remote_requests.append(request.url)
                if request.url.startswith("https://tracking.invalid/")
                else None
            ),
        )
        page.route(
            "**/api/conversations?*",
            lambda route: route.fulfill(
                json={"items": [{"id": "hostile", "title": "Untrusted reply"}], "next_cursor": None}
            ),
        )
        text = (
            '<img src="x" onerror="window.__injected = true">\n\n'
            "<script>window.__injected = true</script>\n\n"
            "![tracker](https://tracking.invalid/private.png)\n\n"
            "[unsafe](javascript:alert%281%29)\n\n"
            "[safe](https://example.org/docs)"
        )
        page.route(
            "**/api/conversations/hostile",
            lambda route: route.fulfill(
                json=conversation(
                    "hostile",
                    "Untrusted reply",
                    [{"id": "untrusted-text", "role": "assistant", "content": text}],
                )
            ),
        )
        sign_in(page)
        page.get_by_role("navigation", name="Conversations").get_by_role(
            "button", name="Untrusted reply", exact=True
        ).click()
        message = page.locator(".message.assistant")
        expect(message).to_contain_text("External image omitted: tracker")
        expect(message.locator("img, script, svg, iframe")).to_have_count(0)
        assert page.evaluate("() => window.__injected") is None
        unsafe = message.get_by_role("link", name="unsafe", exact=True)
        assert not (unsafe.get_attribute("href") or "").lower().startswith("javascript:")
        safe = message.get_by_role("link", name="safe", exact=True)
        expect(safe).to_have_attribute("href", "https://example.org/docs")
        expect(safe).to_have_attribute("rel", "noopener noreferrer")
        expect(safe).to_have_attribute("referrerpolicy", "no-referrer")
        assert remote_requests == []
        browser.close()
