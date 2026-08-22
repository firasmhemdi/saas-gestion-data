from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


class TestDataSources:
    def _admin(self, client: TestClient) -> dict:
        return register(client, email="admin@acme.com", company="Acme SAS")

    def _site(self, client: TestClient, token: str) -> int:
        resp = client.post("/api/v1/sites", json={"name": "Usine Lyon"}, headers=auth_headers(token))
        return resp.json()["id"]

    def test_create_with_encrypted_config(self, client: TestClient):
        admin = self._admin(client)
        site_id = self._site(client, admin["access_token"])
        resp = client.post(
            "/api/v1/data-sources",
            json={
                "name": "Compteur API EDF",
                "source_type": "api",
                "site_id": site_id,
                "config": {"base_url": "https://api.edf.fr", "api_key": "secret-key-1234"},
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        source = resp.json()
        assert source["name"] == "Compteur API EDF"
        assert source["config"] == {"base_url": "https://api.edf.fr", "api_key": "secret-key-1234"}
        assert "secret-key-1234" not in source["encrypted_config"] if "encrypted_config" in source else True

    def test_create_csv_source(self, client: TestClient):
        admin = self._admin(client)
        resp = client.post(
            "/api/v1/data-sources",
            json={
                "name": "Fichier CSV STEG",
                "source_type": "csv",
                "config": {"delimiter": ";", "encoding": "utf-8"},
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["source_type"] == "csv"

    def test_config_not_stored_in_clear_in_db(self, client: TestClient):
        admin = self._admin(client)
        client.post(
            "/api/v1/data-sources",
            json={"name": "DB SQL", "source_type": "sql", "config": {"password": "db-secret-999"}},
            headers=auth_headers(admin["access_token"]),
        )
        from app.core.database import SessionLocal
        from app.models.data_source import DataSource

        db = SessionLocal()
        try:
            row = db.query(DataSource).first()
            assert row.encrypted_config != '{"password": "db-secret-999"}'
            assert "db-secret-999" not in row.encrypted_config
            assert row.encrypted_config.startswith(("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "+", "/", "="))
        finally:
            db.close()

    def test_update_and_test_connection(self, client: TestClient):
        admin = self._admin(client)
        source = client.post(
            "/api/v1/data-sources",
            json={"name": "API", "source_type": "api", "config": {"api_key": "k1"}},
            headers=auth_headers(admin["access_token"]),
        ).json()

        updated = client.patch(
            f"/api/v1/data-sources/{source['id']}",
            json={"is_active": False, "source_type": "csv", "config": {"api_key": "k2"}},
            headers=auth_headers(admin["access_token"]),
        )
        assert updated.status_code == 200
        assert updated.json()["is_active"] is False
        assert updated.json()["source_type"] == "csv"
        assert updated.json()["config"] == {"api_key": "k2"}

        test_resp = client.post(
            f"/api/v1/data-sources/{source['id']}/test-connection",
            headers=auth_headers(admin["access_token"]),
        )
        assert test_resp.status_code == 200
        assert test_resp.json()["config_keys"] == ["api_key"]

    def test_site_must_belong_to_tenant(self, client: TestClient):
        admin_a = self._admin(client)
        admin_b = register(client, email="admin@globex.com", company="Globex Corp")
        site_b = client.post("/api/v1/sites", json={"name": "Site B"}, headers=auth_headers(admin_b["access_token"])).json()

        resp = client.post(
            "/api/v1/data-sources",
            json={"name": "API", "source_type": "api", "site_id": site_b["id"], "config": {}},
            headers=auth_headers(admin_a["access_token"]),
        )
        assert resp.status_code == 400

    def test_tenant_isolation(self, client: TestClient):
        admin_a = self._admin(client)
        admin_b = register(client, email="admin@globex.com", company="Globex Corp")
        source_a = client.post(
            "/api/v1/data-sources",
            json={"name": "API A", "source_type": "api", "config": {"k": "a"}},
            headers=auth_headers(admin_a["access_token"]),
        ).json()

        assert client.get(f"/api/v1/data-sources/{source_a['id']}", headers=auth_headers(admin_b["access_token"])).status_code == 404
        assert len(client.get("/api/v1/data-sources", headers=auth_headers(admin_b["access_token"])).json()) == 0
