from fastapi.testclient import TestClient


def register(
    client: TestClient,
    email: str = "admin@acme.com",
    password: str = "StrongPass!123",
    company: str = "Acme SAS",
) -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Admin Acme", "password": password, "company_name": company},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def login(client: TestClient, email: str = "admin@acme.com", password: str = "StrongPass!123") -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
