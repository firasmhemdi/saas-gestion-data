from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


class TestSprints3To5:
    def _admin(self, client: TestClient) -> dict:
        return register(client, email="admin@acme.com", company="Acme SAS")

    def _indicator(self, client: TestClient, token: str) -> int:
        resp = client.post(
            "/api/v1/reference/indicators",
            json={"code": "ELEC_CONS", "name": "Consommation électrique", "unit": "kWh", "category": "energie"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def test_csv_preview_and_commit_creates_environmental_data(self, client: TestClient):
        admin = self._admin(client)
        indicator_id = self._indicator(client, admin["access_token"])

        preview = client.post(
            "/api/v1/imports/preview",
            json={
                "filename": "energie.csv",
                "content": "date;valeur;unite\n2026-01-15;1234.5;kWh\n2026-01-16;980;kWh",
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert preview.status_code == 201, preview.text
        job = preview.json()
        assert job["row_count"] == 2
        assert job["mapping"]["entry_date"] == "date"
        assert job["mapping"]["value"] == "valeur"

        committed = client.post(
            f"/api/v1/imports/{job['id']}/commit",
            json={"mapping": job["mapping"], "indicator_id": indicator_id},
            headers=auth_headers(admin["access_token"]),
        )
        assert committed.status_code == 200, committed.text
        assert committed.json()["status"] == "success"
        assert committed.json()["imported_count"] == 2

        entries = client.get("/api/v1/data", headers=auth_headers(admin["access_token"])).json()
        assert len(entries) == 2
        assert entries[0]["unit"] == "kWh"

    def test_mapping_schedule_and_sync_are_traced(self, client: TestClient):
        admin = self._admin(client)
        source = client.post(
            "/api/v1/data-sources",
            json={
                "name": "ERP Odoo",
                "source_type": "erp",
                "config": {"base_url": "https://odoo.example", "sample_records": [{"product_qty": 10, "uom": "kWh"}]},
            },
            headers=auth_headers(admin["access_token"]),
        ).json()

        mapping = client.post(
            "/api/v1/mappings",
            json={"name": "Odoo énergie", "source_id": source["id"], "rules": {"product_qty": "value"}},
            headers=auth_headers(admin["access_token"]),
        )
        assert mapping.status_code == 201, mapping.text

        schedule = client.post(
            "/api/v1/sync-schedules",
            json={"source_id": source["id"], "frequency": "daily", "window_start": "22:00", "window_end": "23:00"},
            headers=auth_headers(admin["access_token"]),
        )
        assert schedule.status_code == 201, schedule.text

        sync = client.post(f"/api/v1/data-sources/{source['id']}/sync", headers=auth_headers(admin["access_token"]))
        assert sync.status_code == 200, sync.text
        assert sync.json()["ok"] is True

        imports = client.get("/api/v1/imports", headers=auth_headers(admin["access_token"])).json()
        assert imports[0]["source_id"] == source["id"]

    def test_document_extraction_and_validation(self, client: TestClient):
        admin = self._admin(client)
        indicator_id = self._indicator(client, admin["access_token"])

        created = client.post(
            "/api/v1/documents",
            json={
                "filename": "facture-steg.txt",
                "raw_text": "Facture énergie Fournisseur: STEG Date: 2026-02-15 Total: 450.25 Consommation: 1240 kWh",
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert created.status_code == 201, created.text
        document = created.json()
        assert document["document_type"] == "facture_energie"
        assert document["extracted_data"]["fields"]["quantity"] == 1240

        validated = client.post(
            f"/api/v1/documents/{document['id']}/validate",
            json={"fields": document["extracted_data"]["fields"], "indicator_id": indicator_id},
            headers=auth_headers(admin["access_token"]),
        )
        assert validated.status_code == 200, validated.text
        assert validated.json()["status"] == "validated"

        entries = client.get("/api/v1/data", headers=auth_headers(admin["access_token"])).json()
        assert len(entries) == 1
        assert entries[0]["value"] == 1240
