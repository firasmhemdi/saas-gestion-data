from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


class TestEnvironmentalData:
    def _admin(self, client: TestClient) -> dict:
        return register(client, email="admin@acme.com", company="Acme SAS")

    def _indicator(self, client: TestClient, token: str) -> int:
        resp = client.post(
            "/api/v1/reference/indicators",
            json={"code": "ELEC_CONS", "name": "Consommation électrique", "unit": "kWh", "category": "energie"},
            headers=auth_headers(token),
        )
        return resp.json()["id"]

    def test_manual_entry_created_as_draft(self, client: TestClient):
        admin = self._admin(client)
        indicator_id = self._indicator(client, admin["access_token"])
        resp = client.post(
            "/api/v1/data",
            json={"indicator_id": indicator_id, "entry_date": "2026-01-15", "value": 1234.5, "unit": "kWh", "source": "manuel"},
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "brouillon"
        assert body["value"] == 1234.5
        assert body["entered_by"] == admin["user"]["id"]

        listed = client.get("/api/v1/data", headers=auth_headers(admin["access_token"])).json()
        assert len(listed) == 1

    def test_validate_entry(self, client: TestClient):
        admin = self._admin(client)
        indicator_id = self._indicator(client, admin["access_token"])
        entry = client.post(
            "/api/v1/data",
            json={"indicator_id": indicator_id, "entry_date": "2026-01-15", "value": 100, "unit": "kWh"},
            headers=auth_headers(admin["access_token"]),
        ).json()

        validated = client.post(
            f"/api/v1/data/{entry['id']}/validate",
            headers=auth_headers(admin["access_token"]),
        )
        assert validated.status_code == 200
        assert validated.json()["status"] == "valide"

    def test_validated_entry_cannot_be_modified(self, client: TestClient):
        admin = self._admin(client)
        indicator_id = self._indicator(client, admin["access_token"])
        entry = client.post(
            "/api/v1/data",
            json={"indicator_id": indicator_id, "entry_date": "2026-01-15", "value": 100, "unit": "kWh"},
            headers=auth_headers(admin["access_token"]),
        ).json()
        client.post(f"/api/v1/data/{entry['id']}/validate", headers=auth_headers(admin["access_token"]))

        resp = client.patch(
            f"/api/v1/data/{entry['id']}",
            json={"value": 200},
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 400

    def test_invalid_site_rejected(self, client: TestClient):
        admin = self._admin(client)
        admin_b = register(client, email="admin@globex.com", company="Globex Corp")
        site_b = client.post("/api/v1/sites", json={"name": "Site B"}, headers=auth_headers(admin_b["access_token"])).json()

        resp = client.post(
            "/api/v1/data",
            json={"site_id": site_b["id"], "entry_date": "2026-01-15", "value": 10, "unit": "kWh"},
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 400

    def test_tenant_isolation(self, client: TestClient):
        admin_a = self._admin(client)
        admin_b = register(client, email="admin@globex.com", company="Globex Corp")
        entry_a = client.post(
            "/api/v1/data",
            json={"entry_date": "2026-01-15", "value": 10, "unit": "kWh"},
            headers=auth_headers(admin_a["access_token"]),
        ).json()

        assert client.get(f"/api/v1/data/{entry_a['id']}", headers=auth_headers(admin_b["access_token"])).status_code == 404
