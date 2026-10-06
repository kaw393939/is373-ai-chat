from tests.conftest import PASSWORD, login, signup


async def test_password_reauthentication_and_no_input_echo(client):
    await signup(client)
    assert (await client.post("/api/auth/password", json={"password": PASSWORD})).status_code == 422
    assert (
        await client.post(
            "/api/auth/password", json={"current_password": "wrong", "password": PASSWORD}
        )
    ).status_code == 400
    assert (await client.get("/api/auth/me")).status_code == 200
    assert (
        await client.post(
            "/api/auth/password",
            json={"current_password": PASSWORD, "password": "new-test-password-123"},
        )
    ).status_code == 204
    assert (await client.get("/api/auth/me")).status_code == 401
    response = await client.post(
        "/api/auth/register", json={"email": "invalid", "password": "short-secret"}
    )
    assert response.status_code == 422 and "short-secret" not in response.text


async def test_common_attack_inputs_and_unauthenticated_surface(client):
    assert (
        await client.get("/api/health", headers={"Host": "attacker.example"})
    ).status_code == 400
    response = await client.post(
        "/api/auth/login", content=b"x" * 65537, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    for path in ["/.env", "/.git/config", "/docs", "/openapi.json", "/assets/../../.env"]:
        assert (await client.get(path)).status_code == 404
    for path in [
        "/api/admin/users",
        "/api/admin/overview",
        "/api/admin/budgets",
        "/api/conversations",
    ]:
        assert (await client.get(path)).status_code == 401
    response = await client.post(
        "/api/auth/login", json={"email": "x' OR '1'='1@example.org", "password": PASSWORD}
    )
    assert response.status_code in {401, 422}
    await login(client)
    chat = (await client.post("/api/conversations")).json()["id"]
    title = "<img src=x onerror=alert(1)>"
    assert (
        await client.patch(f"/api/conversations/{chat}", json={"title": title})
    ).status_code == 200
    assert (await client.get(f"/api/conversations/{chat}")).json()["title"] == title
    # React text rendering is exercised with script strings in Playwright.
    assert (
        await client.patch(f"/api/conversations/{chat}", json={"title": "x", "user_id": "attacker"})
    ).status_code == 200
    assert len((await client.get("/api/conversations")).json()) == 1


async def test_cross_account_writes_and_admin_methods_are_denied(client):
    await login(client)
    chat = (await client.post("/api/conversations")).json()["id"]
    await signup(client, "outsider@example.org")
    assert (
        await client.patch(f"/api/conversations/{chat}", json={"title": "Hijacked"})
    ).status_code == 404
    assert (
        await client.post(
            f"/api/conversations/{chat}/stream",
            json={"content": "Private data?", "request_key": "outsider-stream"},
        )
    ).status_code == 404
    for method, path, body in [
        ("GET", "/api/admin/overview", None),
        ("GET", "/api/admin/budgets", None),
        ("POST", "/api/admin/users/missing/recovery", None),
        ("POST", "/api/admin/users/missing/revoke", None),
        ("PATCH", "/api/admin/users/missing", {"role": "admin", "active": True, "approved": True}),
        (
            "PUT",
            "/api/admin/budgets/user",
            {
                "daily_requests": 100,
                "daily_units": 50000,
                "max_concurrent": 1,
                "max_output": 512,
                "model_enabled": True,
            },
        ),
    ]:
        assert (await client.request(method, path, json=body)).status_code == 403
