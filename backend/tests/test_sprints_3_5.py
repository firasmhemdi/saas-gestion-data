from fastapi.testclient import TestClient

from app.services.ingestion import extract_document_fields
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
        source = client.post(
            "/api/v1/data-sources",
            json={"name": "CSV énergie", "source_type": "csv", "config": {"delimiter": ";"}},
            headers=auth_headers(admin["access_token"]),
        ).json()

        preview = client.post(
            "/api/v1/imports/preview",
            json={
                "filename": "energie.csv",
                "content": "date;valeur;unite\n2026-01-15;1234.5;kWh\n2026-01-16;980;kWh",
                "source_id": source["id"],
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert preview.status_code == 201, preview.text
        job = preview.json()
        assert job["row_count"] == 2
        assert job["source_type"] == "csv"
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
        assert entries[0]["source"] == "csv"

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

    def test_steg_invoice_uses_meter_indexes_and_real_totals(self):
        text = """
        Société Tunisienne de l'Electricité et du Gaz
        Facture sur relevé du 2025-12-01 au 2026-03-30
        Montant HT 37.312 P.U. 0.176 Quantité 212 Index nouveau 72866 ancien 72654
        Total Electricité 56.912
        Gaz naturel Montant 12.012 P.U. 0.231 Quantité 52 Index nouveau 3922 ancien 3870
        Total Gaz 15.012
        Total Consommation & Services 71.924
        MONTANT TOTAL (16) 85.352
        Arriérés 902.085
        987.000 Montant à payer
        """

        fields, confidence = extract_document_fields(text)

        assert fields["provider"] == "STEG"
        assert fields["period_start"] == "2025-12-01"
        assert fields["period_end"] == "2026-03-30"
        assert fields["amount"] == 85.352
        assert fields["amount_due"] == 987.0
        assert fields["quantity"] == 212
        assert fields["unit"] == "kWh"
        assert fields["gas_quantity"] == 52
        assert fields["gas_unit"] == "m3"
        assert confidence >= 85

    def test_document_can_be_reanalyzed_with_latest_rules(self, client: TestClient):
        admin = self._admin(client)
        created = client.post(
            "/api/v1/documents",
            json={
                "filename": "facture-steg-photo.txt",
                "raw_text": "STEG Facture 2025-12-01 2026-03-30 Index nouveau 72866 ancien 72654 Gaz Index nouveau 3922 ancien 3870 987.000 Montant a payer",
            },
            headers=auth_headers(admin["access_token"]),
        )
        assert created.status_code == 201, created.text

        reanalyzed = client.post(
            f"/api/v1/documents/{created.json()['id']}/reanalyze",
            headers=auth_headers(admin["access_token"]),
        )

        assert reanalyzed.status_code == 200, reanalyzed.text
        fields = reanalyzed.json()["extracted_data"]["fields"]
        assert fields["quantity"] == 212
        assert fields["gas_quantity"] == 52
        assert fields["amount_due"] == 987

    def test_steg_invoice_calculates_missing_quantities_from_unit_prices(self):
        text = """
        STEG Facture sur relevé 2025-12-01 2026-03-30
        Electricité Eclairage Montant HT 37.312 Prix unitaire 0.176
        Redevances fixes électricité 19.600 Prix unitaire 0.700
        Gaz naturel Montant HT 12.012 Prix unitaire 0.231
        Redevances fixes gaz 3.000 Prix unitaire 0.150
        Montant total 85.352
        987.000 Montant a payer
        """

        fields, confidence = extract_document_fields(text)

        assert fields["quantity"] == 212
        assert fields["unit"] == "kWh"
        assert fields["gas_quantity"] == 52
        assert fields["gas_unit"] == "m3"
        assert fields["amount"] == 85.352
        assert fields["amount_due"] == 987
        assert confidence >= 85

    def test_noisy_steg_photo_extracts_key_fields_from_lines(self):
        text = """
        Societe Tunisienne de l Electricite et du Gaz
        F a c t u r e   s u r   r e l e v e
        du 2025.12.01 au 2026.03.30
        CONSOMMATION & SERVICES
        Electricite 704493 ECLAIRAGE 37.312 0.176 212 72866 72654 4 7
        Total Electricite 56.912
        Gaz 87021 GAZ-NATUR 12.012 0.231 52 3922 3870 4 5
        Total Gaz 15.012
        Total Consommation & Services 71.924
        MONTANT TOTAL 85.352
        987.000 Montant a payer
        """

        fields, confidence = extract_document_fields(text)

        assert fields["provider"] == "STEG"
        assert fields["period_start"] == "2025-12-01"
        assert fields["period_end"] == "2026-03-30"
        assert fields["amount"] == 85.352
        assert fields["amount_due"] == 987
        assert fields["quantity"] == 212
        assert fields["unit"] == "kWh"
        assert fields["gas_quantity"] == 52
        assert fields["gas_unit"] == "m3"
        assert confidence >= 85

    def test_sonede_water_invoice_extracts_required_fields(self):
        text = """
        الشركة الوطنية لاستغلال وتوزيع المياه
        SONEDE Facture eau
        Ancien index 42495 Nouveau index 42541
        consommation eau 46 م3
        periode du 2026/01/17 au 2026/04/17
        montant total 57.100
        المبلغ المطلوب للدفع 57.100
        """

        fields, confidence = extract_document_fields(text, "facture-sonede.jpg")

        assert fields["provider"] == "SONEDE"
        assert fields["period_start"] == "2026-01-17"
        assert fields["period_end"] == "2026-04-17"
        assert fields["amount_due"] == 57.1
        assert fields["quantity"] == 46
        assert fields["unit"] == "m3"
        assert confidence >= 75

    def test_sonede_noisy_number_cloud_uses_meter_difference(self):
        text = """
        الشركة الوطنية لاستغلال وتوزيع المياه
        71.510 100 الاسم العنوان
        42495 17
        257580 550 46 17900
        19800 3560 057
        44990 315 46
        7880
        33640
        مجموع معلوم الماء 3500
        57.100
        """

        fields, confidence = extract_document_fields(text, "facture-sonede.jpg")

        assert fields["provider"] == "SONEDE"
        assert fields["amount_due"] == 57.1
        assert fields["quantity"] == 46
        assert fields["unit"] == "m3"
        assert fields["document_date"]
        assert confidence >= 65

    def test_sonede_ignores_tiny_noise_and_reads_spaced_amount(self):
        text = """
        الشركة الوطنية لاستغلال وتوزيع المياه
        SONEDE
        رقم الفاتورة 2
        42495 17
        257580 550 46 17900
        44990 315 46
        المبلغ المطلوب للدفع
        57 100
        """

        fields, confidence = extract_document_fields(text, "facture-sonede.jpg")

        assert fields["invoice_kind"] == "water"
        assert fields["provider"] == "SONEDE"
        assert fields["amount_due"] == 57.1
        assert fields["quantity"] == 46
        assert fields["unit"] == "m3"
        assert confidence >= 65

    def test_sonede_prefers_repeated_table_quantity_over_index_difference(self):
        text = """
        الشركة الوطنية لاستغلال وتوزيع المياه
        كشف استهلاك الماء
        71٫510 100
        42495 17
        44990 44855 135
        الكمية 46
        معلوم الماء 46
        المبلغ المطلوب للاستخلاص
        57٫100
        """

        fields, confidence = extract_document_fields(text, "facture-sonede.jpg")

        assert fields["invoice_kind"] == "water"
        assert fields["provider"] == "SONEDE"
        assert fields["amount_due"] == 57.1
        assert fields["quantity"] == 46
        assert fields["unit"] == "m3"
        assert confidence >= 65

    def test_telecom_invoice_extracts_provider_service_and_amount_without_energy_fields(self):
        text = """
        Ooredoo Tunisie
        Facture internet fibre
        Date facture 2026-08-20
        Periode du 2026-08-01 au 2026-08-31
        Total TTC 59.900
        Net a payer 59.900
        """

        fields, confidence = extract_document_fields(text, "facture-ooredoo.pdf")

        assert fields["invoice_kind"] == "telecom"
        assert fields["provider"] == "Ooredoo"
        assert fields["service"] == "Internet fibre"
        assert fields["document_date"] == "2026-08-20"
        assert fields["period_start"] == "2026-08-01"
        assert fields["period_end"] == "2026-08-31"
        assert fields["amount_due"] == 59.9
        assert "gas_quantity" not in fields
        assert confidence >= 75
