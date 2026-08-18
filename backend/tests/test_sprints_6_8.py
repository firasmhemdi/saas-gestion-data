from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


class TestSprintsSixToEight:
    def _seed(self, client: TestClient) -> tuple[str, int, int]:
        admin = register(client, email="admin@acme.com", company="Acme SAS")
        token = admin["access_token"]
        headers = auth_headers(token)
        site = client.post("/api/v1/sites", json={"name": "Usine Tunis", "code": "TUN"}, headers=headers).json()
        indicator = client.post(
            "/api/v1/reference/indicators",
            json={"code": "ELEC", "name": "Consommation électrique", "unit": "kWh", "category": "energie"},
            headers=headers,
        ).json()
        client.post(
            "/api/v1/reference/emissions",
            json={"code": "ELEC_SCOPE2", "name": "Électricité réseau", "scope": "2", "factor": 0.43, "unit": "kgCO2e/kWh", "year": 2026},
            headers=headers,
        )
        return token, site["id"], indicator["id"]

    def test_quality_summary_and_normalization(self, client: TestClient):
        token, site_id, indicator_id = self._seed(client)
        headers = auth_headers(token)
        entry = client.post(
            "/api/v1/data",
            json={"site_id": site_id, "indicator_id": indicator_id, "entry_date": "2026-03-01", "value": 2, "unit": "MWh"},
            headers=headers,
        ).json()
        client.post(
            "/api/v1/data",
            json={"entry_date": "2026-03-01", "value": -5, "unit": "kWh"},
            headers=headers,
        )

        summary = client.get("/api/v1/quality/summary", headers=headers)
        assert summary.status_code == 200, summary.text
        body = summary.json()
        assert body["total_entries"] == 2
        assert any(alert["issue_type"] == "missing_reference" for alert in body["alerts"])
        assert any(alert["issue_type"] == "negative_value" for alert in body["alerts"])

        normalized = client.post(f"/api/v1/quality/data/{entry['id']}/normalize", headers=headers)
        assert normalized.status_code == 200, normalized.text
        assert normalized.json()["normalized_value"] == 2000
        assert normalized.json()["normalized_unit"] == "kWh"

    def test_analytics_summary(self, client: TestClient):
        token, site_id, indicator_id = self._seed(client)
        headers = auth_headers(token)
        entry = client.post(
            "/api/v1/data",
            json={"site_id": site_id, "indicator_id": indicator_id, "entry_date": "2026-04-01", "value": 100, "unit": "kWh"},
            headers=headers,
        ).json()
        client.post(f"/api/v1/data/{entry['id']}/validate", headers=headers)

        resp = client.get("/api/v1/analytics/summary", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["metrics"][0]["value"] == 100
        assert body["site_performance"][0]["site_name"] == "Usine Tunis"
        assert body["emissions_by_scope"][1]["value"] == 43

    def test_assistant_answer_and_history(self, client: TestClient):
        token, site_id, indicator_id = self._seed(client)
        headers = auth_headers(token)
        client.post(
            "/api/v1/data",
            json={"site_id": site_id, "indicator_id": indicator_id, "entry_date": "2026-05-01", "value": 420, "unit": "kWh"},
            headers=headers,
        )

        answer = client.post(
            "/api/v1/assistant/query",
            json={"question": "Quel site possède la consommation la plus élevée ?"},
            headers=headers,
        )
        assert answer.status_code == 201, answer.text
        assert "Usine Tunis" in answer.json()["answer"]
        assert answer.json()["sources"][0]["site"] == "Usine Tunis"

        history = client.get("/api/v1/assistant/history", headers=headers)
        assert history.status_code == 200
        assert len(history.json()) == 1
