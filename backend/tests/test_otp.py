from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services.email import _safe_resend_error_message
from tests.helpers import auth_headers, login, register


def _enable_otp(client: TestClient, token: str, password: str = "StrongPass!123") -> dict:
    resp = client.patch(
        "/api/v1/auth/otp/settings",
        json={"enabled": True, "password": password},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestOtpSettings:
    def test_otp_disabled_by_default(self, client: TestClient):
        data = register(client)
        assert data["user"]["otp_enabled"] is False

    def test_enable_otp_requires_valid_password(self, client: TestClient):
        data = register(client)
        resp = client.patch(
            "/api/v1/auth/otp/settings",
            json={"enabled": True, "password": "WrongPass!999"},
            headers=auth_headers(data["access_token"]),
        )
        assert resp.status_code == 400

    def test_enable_then_disable(self, client: TestClient):
        data = register(client)
        _enable_otp(client, data["access_token"])
        resp = client.patch(
            "/api/v1/auth/otp/settings",
            json={"enabled": False, "password": "StrongPass!123"},
            headers=auth_headers(data["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["otp_enabled"] is False


class TestOtpLogin:
    def test_login_requires_otp_when_enabled(self, client: TestClient):
        data = register(client)
        _enable_otp(client, data["access_token"])

        resp = client.post("/api/v1/auth/login", json={"email": "admin@acme.com", "password": "StrongPass!123"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["requires_otp"] is True
        assert body["otp_token"]
        assert "access_token" not in body

    def test_verify_otp_returns_tokens(self, client: TestClient):
        data = register(client)
        _enable_otp(client, data["access_token"])

        challenge = client.post(
            "/api/v1/auth/login", json={"email": "admin@acme.com", "password": "StrongPass!123"}
        ).json()
        assert len(challenge["dev_otp"]) == 6

        resp = client.post("/api/v1/auth/otp/verify", json={"otp_token": challenge["otp_token"], "code": challenge["dev_otp"]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["user"]["email"] == "admin@acme.com"
        assert body["user"]["otp_enabled"] is True

    def test_resend_otp_returns_new_challenge(self, client: TestClient):
        data = register(client)
        _enable_otp(client, data["access_token"])

        challenge = client.post(
            "/api/v1/auth/login", json={"email": "admin@acme.com", "password": "StrongPass!123"}
        ).json()
        resend = client.post("/api/v1/auth/otp/resend", json={"challenge_token": challenge["otp_token"]})
        assert resend.status_code == 200, resend.text
        body = resend.json()
        assert body["requires_otp"] is True
        assert body["otp_token"]
        assert len(body["dev_otp"]) == 6

        verified = client.post("/api/v1/auth/otp/verify", json={"otp_token": body["otp_token"], "code": body["dev_otp"]})
        assert verified.status_code == 200

    def test_wrong_code_rejected_but_valid_code_still_works(self, client: TestClient):
        data = register(client)
        _enable_otp(client, data["access_token"])

        challenge = client.post(
            "/api/v1/auth/login", json={"email": "admin@acme.com", "password": "StrongPass!123"}
        ).json()

        bad = client.post("/api/v1/auth/otp/verify", json={"otp_token": challenge["otp_token"], "code": "000000"})
        assert bad.status_code == 400

        good = client.post("/api/v1/auth/otp/verify", json={"otp_token": challenge["otp_token"], "code": challenge["dev_otp"]})
        assert good.status_code == 200

    def test_code_is_single_use(self, client: TestClient):
        data = register(client)
        _enable_otp(client, data["access_token"])

        challenge = client.post(
            "/api/v1/auth/login", json={"email": "admin@acme.com", "password": "StrongPass!123"}
        ).json()
        assert client.post(
            "/api/v1/auth/otp/verify", json={"otp_token": challenge["otp_token"], "code": challenge["dev_otp"]}
        ).status_code == 200

        again = client.post(
            "/api/v1/auth/otp/verify", json={"otp_token": challenge["otp_token"], "code": challenge["dev_otp"]}
        )
        assert again.status_code in (400, 401)

    def test_invalid_otp_token_rejected(self, client: TestClient):
        resp = client.post("/api/v1/auth/otp/verify", json={"otp_token": "garbage.token.value", "code": "123456"})
        assert resp.status_code == 400

    def test_otp_login_without_enable_returns_direct_tokens(self, client: TestClient):
        register(client)
        body = login(client)
        assert "access_token" in body
        assert "requires_otp" not in body

    def test_otp_email_service_required_when_code_not_exposed(self, client: TestClient, monkeypatch):
        data = register(client)
        _enable_otp(client, data["access_token"])

        monkeypatch.setenv("DEMO_MODE", "false")
        monkeypatch.setenv("OTP_EXPOSE_DEMO_CODE", "false")
        monkeypatch.setenv("SMTP_HOST", "")
        get_settings.cache_clear()
        try:
            resp = client.post("/api/v1/auth/login", json={"email": "admin@acme.com", "password": "StrongPass!123"})
            assert resp.status_code == 503
            assert "e-mail" in resp.json()["detail"]
        finally:
            get_settings.cache_clear()


class TestEmailDeliveryMessages:
    def test_resend_domain_error_message_is_actionable(self):
        message = _safe_resend_error_message("You can only send testing emails to your own email address. Verify a domain.")
        assert "RESEND_FROM_EMAIL" in message
        assert "domaine vérifié" in message
