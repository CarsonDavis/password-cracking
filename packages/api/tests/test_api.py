"""Tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from crack_time_api.app import app

client = TestClient(app)


class TestEstimate:
    def test_basic_estimate(self):
        resp = client.post("/api/estimate", json={
            "password": "test",
            "algorithm": "bcrypt_cost12",
            "hardware_tier": "consumer",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["password"] == "test"
        assert data["hash_algorithm"] == "bcrypt_cost12"
        assert data["hardware_tier"] == "consumer"
        assert data["rating"] >= 0
        assert data["rating_label"]
        assert data["crack_time_display"]

    def test_estimate_invalid_algorithm(self):
        resp = client.post("/api/estimate", json={
            "password": "test",
            "algorithm": "fake_algo",
            "hardware_tier": "consumer",
        })
        assert resp.status_code == 400

    def test_estimate_invalid_tier(self):
        resp = client.post("/api/estimate", json={
            "password": "test",
            "algorithm": "bcrypt_cost12",
            "hardware_tier": "fake_tier",
        })
        assert resp.status_code == 400

    def test_estimate_empty_password(self):
        resp = client.post("/api/estimate", json={
            "password": "",
            "algorithm": "bcrypt_cost12",
            "hardware_tier": "consumer",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["rating"] == 0

    def test_estimate_defaults(self):
        resp = client.post("/api/estimate", json={"password": "hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["hash_algorithm"] == "bcrypt_cost12"
        assert data["hardware_tier"] == "consumer"


class TestBatch:
    def test_batch_basic(self):
        resp = client.post("/api/batch", json={
            "passwords": ["password", "test123", "Tr0ub4dor&3"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_passwords"] == 3
        assert "summary" in data
        assert len(data["passwords"]) == 3

    def test_batch_empty_list(self):
        resp = client.post("/api/batch", json={"passwords": []})
        assert resp.status_code == 400


class TestCompare:
    def test_compare_passwords(self):
        resp = client.post("/api/compare/passwords", json={
            "passwords": ["password", "Tr0ub4dor&3"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_compare_algorithms(self):
        resp = client.post("/api/compare/algorithms", json={
            "password": "test",
            "algorithms": ["md5", "bcrypt_cost12"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["hash_algorithm"] == "md5"
        assert data[1]["hash_algorithm"] == "bcrypt_cost12"

    def test_compare_attackers(self):
        resp = client.post("/api/compare/attackers", json={
            "password": "test",
            "algorithm": "bcrypt_cost12",
            "hardware_tiers": ["consumer", "nation_state"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_compare_passwords_too_few(self):
        resp = client.post("/api/compare/passwords", json={
            "passwords": ["solo"],
        })
        assert resp.status_code == 400


class TestMetadata:
    def test_metadata(self):
        resp = client.get("/api/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert "algorithms" in data
        assert "hardware_tiers" in data
        assert len(data["algorithms"]) > 0
        assert len(data["hardware_tiers"]) > 0

    def test_metadata_has_bcrypt(self):
        resp = client.get("/api/metadata")
        data = resp.json()
        algo_names = [a["name"] for a in data["algorithms"]]
        assert "bcrypt_cost12" in algo_names

    def test_metadata_has_consumer_tier(self):
        resp = client.get("/api/metadata")
        data = resp.json()
        tier_names = [t["name"] for t in data["hardware_tiers"]]
        assert "consumer" in tier_names


class TestTargeted:
    def test_targeted_no_context(self):
        resp = client.post("/api/targeted", json={
            "password": "test",
        })
        assert resp.status_code == 200

    def test_targeted_with_matching_context(self):
        resp = client.post("/api/targeted", json={
            "password": "john2024",
            "context": ["john", "2024"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "targeted" in data["winning_attack"]
