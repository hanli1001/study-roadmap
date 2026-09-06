from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["api"] == "中医方剂查询系统"

def test_list_prescriptions():
    response = client.get("/prescriptions")
    assert response.status_code == 200
    assert len(response.json()) == 8

def test_get_one():
    response = client.get("/prescriptions/1")
    assert response.status_code == 200
    assert response.json()["name"] == "麻黄汤"

def test_get_not_found():
    response = client.get("/prescriptions/999")
    assert response.status_code == 404

def test_list_herbs():
    response = client.get("/herbs")
    assert response.status_code == 200
    assert response.json()[0]["id"] == 10

def test_create():
    response = client.post("/prescriptions",
                           json={"name":"001","category":"002","source":"0","symptoms":"003","herbs":[]})
    assert response.status_code == 201
    new_id = response.json()["id"]
    cleanup = client.delete(f"/prescriptions/{new_id}")
    assert cleanup.status_code == 200

