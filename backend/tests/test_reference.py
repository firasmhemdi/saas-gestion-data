from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


class TestReference:
    def _admin(self, client: TestClient) -> dict:
        return register(client, email="admin@acme.com", company="Acme SAS")

    def test_create_and_list_indicator(self, client: TestClient):
        admin = self._admin(client)
        resp = client.post(
            "/api/v1/reference/indicators",
            json={"code": "ELEC_CONS", "name": "Consommation électrique", "unit": "kWh", "category": "energie"},
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["category"] == "energie"

        listed = client.get("/api/v1/reference/indicators", headers=auth_headers(admin["access_token"])).json()
        assert len(listed) == 1
        assert listed[0]["code"] == "ELEC_CONS"

    def test_duplicate_indicator_code_conflict(self, client: TestClient):
        admin = self._admin(client)
        payload = {"code": "ELEC_CONS", "name": "Consommation électrique", "unit": "kWh", "category": "energie"}
        client.post("/api/v1/reference/indicators", json=payload, headers=auth_headers(admin["access_token"]))
        resp = client.post("/api/v1/reference/indicators", json=payload, headers=auth_headers(admin["access_token"]))
        assert resp.status_code == 409

    def test_create_and_list_emission(self, client: TestClient):
        admin = self._admin(client)
        resp = client.post(
            "/api/v1/reference/emissions",
            json={
                "code": "FE_ELEC_FR",
                "name": "Facteur d'émission électricité France",
                "scope": "2",
                "source": "ADEME",
                "factor": 0.052,
                "unit": "kgCO2e/kWh",
                "year": 2023,
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["scope"] == "2"

        listed = client.get("/api/v1/reference/emissions", headers=auth_headers(admin["access_token"])).json()
        assert len(listed) == 1

    def test_reference_scoped_to_tenant(self, client: TestClient):
        admin_a = self._admin(client)
        admin_b = register(client, email="admin@globex.com", company="Globex Corp")
        client.post(
            "/api/v1/reference/indicators",
            json={"code": "ELEC_CONS", "name": "Conso", "unit": "kWh", "category": "energie"},
            headers=auth_headers(admin_a["access_token"]),
        )
        listed_b = client.get("/api/v1/reference/indicators", headers=auth_headers(admin_b["access_token"])).json()
        assert listed_b == []

    def test_lecture_seule_can_read_but_not_create(self, client: TestClient):
        admin = self._admin(client)
        member = client.post(
            "/api/v1/users",
            json={"email": "membre@acme.com", "full_name": "Membre", "password": "StrongPass!123", "role": "lecture_seule"},
            headers=auth_headers(admin["access_token"]),
        ).json()
        member_login = client.post(
            "/api/v1/auth/login", json={"email": "membre@acme.com", "password": "StrongPass!123"}
        ).json()

        assert client.get("/api/v1/reference/indicators", headers=auth_headers(member_login["access_token"])).status_code == 200
        resp = client.post(
            "/api/v1/reference/indicators",
            json={"code": "X", "name": "X", "unit": "u", "category": "eau"},
            headers=auth_headers(member_login["access_token"]),
        )
        assert resp.status_code == 403
