from fastapi.testclient import TestClient

from app.core.config import get_settings


def _register(client: TestClient, email: str = "admin@acme.com", password: str = "StrongPass!123", company: str = "Acme SAS") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Admin Acme", "password": password, "company_name": company},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(client: TestClient, email: str = "admin@acme.com", password: str = "StrongPass!123") -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestRegister:
    def test_register_returns_tokens_and_admin_role(self, client: TestClient):
        data = _register(client)
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == "admin@acme.com"
        assert data["user"]["company_id"] == data["user"]["company_id"]

    def test_register_duplicate_email_conflict(self, client: TestClient):
        _register(client)
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "admin@acme.com", "full_name": "Autre", "password": "StrongPass!123", "company_name": "Autre SAS"},
        )
        assert resp.status_code == 409

    def test_register_weak_password_rejected(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "x@y.com", "full_name": "X", "password": "short", "company_name": "Acme SAS"},
        )
        assert resp.status_code == 422

    def test_register_same_company_keeps_slug_unique(self, client: TestClient):
        first = _register(client, email="a@acme.com", company="Acme SAS")
        second = _register(client, email="b@acme.com", company="Acme SAS")
        assert first["user"]["company_id"] != second["user"]["company_id"]

    def test_register_requires_email_verification_when_enabled(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "true")
        get_settings.cache_clear()
        try:
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "verify@acme.com",
                    "full_name": "Verify Acme",
                    "password": "StrongPass!123",
                    "company_name": "Verify SAS",
                },
            )
            assert resp.status_code == 201, resp.text
            challenge = resp.json()
            assert challenge["requires_email_verification"] is True
            assert challenge["verification_token"]
            assert challenge["email"] == "verify@acme.com"
            assert len(challenge["dev_otp"]) == 6

            verified = client.post(
                "/api/v1/auth/email/verify",
                json={"verification_token": challenge["verification_token"], "code": challenge["dev_otp"]},
            )
            assert verified.status_code == 200, verified.text
            body = verified.json()
            assert body["access_token"]
            assert body["user"]["email_verified"] is True
        finally:
            monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
            get_settings.cache_clear()

    def test_login_resends_email_verification_for_unverified_account(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "true")
        get_settings.cache_clear()
        try:
            created = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "pending@acme.com",
                    "full_name": "Pending Acme",
                    "password": "StrongPass!123",
                    "company_name": "Pending SAS",
                },
            ).json()
            assert created["requires_email_verification"] is True

            login = client.post(
                "/api/v1/auth/login",
                json={"email": "pending@acme.com", "password": "StrongPass!123"},
            )
            assert login.status_code == 200, login.text
            body = login.json()
            assert body["requires_email_verification"] is True
            assert body["verification_token"]

            resend = client.post("/api/v1/auth/email/resend", json={"challenge_token": body["verification_token"]})
            assert resend.status_code == 200, resend.text
            assert resend.json()["requires_email_verification"] is True
        finally:
            monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
            get_settings.cache_clear()


class TestLogin:
    def test_login_success(self, client: TestClient):
        _register(client)
        data = _login(client)
        assert data["access_token"]
        assert data["user"]["email"] == "admin@acme.com"

    def test_login_wrong_password(self, client: TestClient):
        _register(client)
        resp = client.post("/api/v1/auth/login", json={"email": "admin@acme.com", "password": "WrongPass!999"})
        assert resp.status_code == 401

    def test_login_unknown_email(self, client: TestClient):
        resp = client.post("/api/v1/auth/login", json={"email": "nobody@nowhere.com", "password": "StrongPass!123"})
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_current_user(self, client: TestClient):
        data = _register(client)
        resp = client.get("/api/v1/auth/me", headers=_auth_headers(data["access_token"]))
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@acme.com"

    def test_me_requires_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_rejects_garbage_token(self, client: TestClient):
        resp = client.get("/api/v1/auth/me", headers=_auth_headers("not.a.token"))
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_rotates_tokens(self, client: TestClient):
        first = _register(client)
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert resp.status_code == 200
        second = resp.json()
        assert second["access_token"]
        assert second["refresh_token"] != first["refresh_token"]

        old_used_again = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert old_used_again.status_code == 401

    def test_refresh_invalid_token(self, client: TestClient):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.token.value"})
        assert resp.status_code == 401


class TestLogout:
    def test_logout_revokes_refresh_token(self, client: TestClient):
        data = _register(client)
        resp = client.post("/api/v1/auth/logout", json={"refresh_token": data["refresh_token"]}, headers=_auth_headers(data["access_token"]))
        assert resp.status_code == 204

        reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert reuse.status_code == 401


class TestRBAC:
    def _create_member(self, client: TestClient, admin_token: str, email: str, role: str = "lecture_seule") -> dict:
        resp = client.post(
            "/api/v1/users",
            json={"email": email, "full_name": "Membre", "password": "StrongPass!123", "role": role},
            headers=_auth_headers(admin_token),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_non_admin_cannot_list_users(self, client: TestClient):
        admin = _register(client, email="admin@acme.com", company="Acme SAS")
        admin_token = admin["access_token"]
        member = self._create_member(client, admin_token, "membre@acme.com")

        member_login = _login(client, email="membre@acme.com")
        member_token = member_login["access_token"]

        assert client.get("/api/v1/users", headers=_auth_headers(admin_token)).status_code == 200
        assert client.get("/api/v1/users", headers=_auth_headers(member_token)).status_code == 403
        assert member["role"] == "lecture_seule"

    def test_admin_can_change_role(self, client: TestClient):
        admin = _register(client, email="admin@acme.com", company="Acme SAS")
        member = self._create_member(client, admin["access_token"], "membre@acme.com")

        resp = client.patch(
            f"/api/v1/users/{member['id']}",
            json={"role": "consultant"},
            headers=_auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "consultant"

    def test_admin_cannot_demote_self(self, client: TestClient):
        admin = _register(client)
        resp = client.patch(
            f"/api/v1/users/{admin['user']['id']}",
            json={"role": "consultant"},
            headers=_auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 400


class TestMultiTenant:
    def test_tenant_isolation_for_users_listing(self, client: TestClient):
        company_a = _register(client, email="admin@acme.com", company="Acme SAS")
        company_b = _register(client, email="admin@globex.com", company="Globex Corp")

        users_a = client.get("/api/v1/users", headers=_auth_headers(company_a["access_token"])).json()
        users_b = client.get("/api/v1/users", headers=_auth_headers(company_b["access_token"])).json()

        assert len(users_a) == 1
        assert len(users_b) == 1
        assert users_a[0]["company_id"] != users_b[0]["company_id"]

    def test_admin_cannot_read_other_tenant_user(self, client: TestClient):
        company_a = _register(client, email="admin@acme.com", company="Acme SAS")
        company_b = _register(client, email="admin@globex.com", company="Globex Corp")
        user_b_id = company_b["user"]["id"]

        resp = client.get(
            f"/api/v1/users/{user_b_id}",
            headers=_auth_headers(company_a["access_token"]),
        )
        assert resp.status_code == 404

    def test_audit_logs_scoped_to_tenant(self, client: TestClient):
        company_a = _register(client, email="admin@acme.com", company="Acme SAS")
        _login(client, email="admin@acme.com")
        company_b = _register(client, email="admin@globex.com", company="Globex Corp")
        _login(client, email="admin@globex.com")

        logs_a = client.get("/api/v1/users/audit/logs", headers=_auth_headers(company_a["access_token"])).json()
        logs_b = client.get("/api/v1/users/audit/logs", headers=_auth_headers(company_b["access_token"])).json()

        assert logs_a
        assert logs_b
        assert all(log["company_id"] == company_a["user"]["company_id"] for log in logs_a)
        assert all(log["company_id"] == company_b["user"]["company_id"] for log in logs_b)

    def test_failed_login_is_audited(self, client: TestClient):
        company = _register(client)
        resp = client.post("/api/v1/auth/login", json={"email": "admin@acme.com", "password": "WrongPass!999"})
        assert resp.status_code == 401

        logs = client.get("/api/v1/users/audit/logs", headers=_auth_headers(company["access_token"])).json()
        assert any(log["action"] == "login_failed" for log in logs)


class TestHealth:
    def test_health(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
