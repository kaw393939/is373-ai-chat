import json
from pathlib import Path

from tests.conftest import login, signup


async def test_admin_roles_budgets_and_audit(client):
    student = await signup(client)
    assert (await client.get("/api/admin/users")).status_code == 403
    admin = await login(client)
    assert len((await client.get("/api/admin/users")).json()) == 2
    edit = {
        "role": "user",
        "active": True,
        "approved": True,
        "daily_requests": 2,
        "daily_units": 2000,
        "max_concurrent": 1,
    }
    assert (await client.patch(f"/api/admin/users/{admin['id']}", json=edit)).status_code == 400
    assert (await client.patch("/api/admin/users/missing", json=edit)).status_code == 404
    assert (await client.patch(f"/api/admin/users/{student['id']}", json=edit)).status_code == 200
    assert (await client.post("/api/admin/users/missing/recovery")).status_code == 404
    assert (await client.post(f"/api/admin/users/{student['id']}/revoke")).status_code == 204
    budgets = (await client.get("/api/admin/budgets")).json()
    body = {k: v for k, v in budgets[0].items() if k != "role"}
    assert (await client.put("/api/admin/budgets/missing", json=body)).status_code == 404
    assert (await client.put("/api/admin/budgets/user", json=body)).status_code == 200
    overview = (await client.get("/api/admin/overview")).json()
    assert overview["totals"]["users"] == 2
    assert overview["audit"][0]["action"] == "budget.updated"
    assert overview["host"]["status"] == "collector unavailable"


async def test_monitoring_collector_data(client, application):
    Path(application.state.config.metrics_path).write_text(
        json.dumps({"samples": [{"at": 1, "cpu_percent": 5, "containers": []}]})
    )
    await login(client)
    data = (await client.get("/api/admin/overview")).json()
    assert data["host"]["samples"][0]["cpu_percent"] == 5
    assert (await client.get("/api/models")).json()[0]["id"] == "default"
