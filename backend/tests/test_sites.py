from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


class TestSites:
    def _admin(self, client: TestClient) -> dict:
        return register(client, email="admin@acme.com", company="Acme SAS")

    def test_create_and_list_site(self, client: TestClient):
        admin = self._admin(client)
        resp = client.post(
            "/api/v1/sites",
            json={"name": "Usine Lyon", "code": "LYN-01", "location": "Lyon, France"},
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        site = resp.json()
        assert site["name"] == "Usine Lyon"
        assert site["company_id"] == admin["user"]["company_id"]

        listed = client.get("/api/v1/sites", headers=auth_headers(admin["access_token"])).json()
        assert len(listed) == 1

    def test_duplicate_site_name_conflict(self, client: TestClient):
        admin = self._admin(client)
        client.post("/api/v1/sites", json={"name": "Usine Lyon"}, headers=auth_headers(admin["access_token"]))
        resp = client.post("/api/v1/sites", json={"name": "Usine Lyon"}, headers=auth_headers(admin["access_token"]))
        assert resp.status_code == 409

    def test_update_site(self, client: TestClient):
        admin = self._admin(client)
        site = client.post("/api/v1/sites", json={"name": "Usine Lyon"}, headers=auth_headers(admin["access_token"])).json()
        resp = client.patch(
            f"/api/v1/sites/{site['id']}",
            json={"location": "Vénissieux"},
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["location"] == "Vénissieux"

    def test_delete_site(self, client: TestClient):
        admin = self._admin(client)
        site = client.post("/api/v1/sites", json={"name": "Usine Lyon"}, headers=auth_headers(admin["access_token"])).json()
        resp = client.delete(f"/api/v1/sites/{site['id']}", headers=auth_headers(admin["access_token"]))
        assert resp.status_code == 204

    def test_tenant_isolation(self, client: TestClient):
        admin_a = self._admin(client)
        admin_b = register(client, email="admin@globex.com", company="Globex Corp")

        client.post("/api/v1/sites", json={"name": "Site A"}, headers=auth_headers(admin_a["access_token"]))
        client.post("/api/v1/sites", json={"name": "Site B"}, headers=auth_headers(admin_b["access_token"]))

        sites_a = client.get("/api/v1/sites", headers=auth_headers(admin_a["access_token"])).json()
        assert len(sites_a) == 1
        assert sites_a[0]["name"] == "Site A"

        other = client.post(
            "/api/v1/sites", json={"name": "Intrus"}, headers=auth_headers(admin_a["access_token"])
        ).json()
        assert client.get(f"/api/v1/sites/{other['id']}", headers=auth_headers(admin_b["access_token"])).status_code == 404

    def test_read_only_role_cannot_create(self, client: TestClient):
        admin = self._admin(client)
        member = client.post(
            "/api/v1/users",
            json={"email": "membre@acme.com", "full_name": "Membre", "password": "StrongPass!123", "role": "lecture_seule"},
            headers=auth_headers(admin["access_token"]),
        ).json()
        member_login = client.post(
            "/api/v1/auth/login", json={"email": "membre@acme.com", "password": "StrongPass!123"}
        ).json()

        resp = client.post(
            "/api/v1/sites", json={"name": "Usine"}, headers=auth_headers(member_login["access_token"])
        )
        assert resp.status_code == 403
