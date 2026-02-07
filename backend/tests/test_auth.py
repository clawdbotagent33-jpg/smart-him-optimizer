"""인증 API 테스트"""

import pytest


class TestAuthAPI:
    """인증 API 테스트 클래스"""

    def test_login_success(self, client):
        """로그인 성공 테스트"""
        response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "tokenType" in data
        assert "user" in data
        assert data["user"]["username"] == "admin"

    def test_login_invalid_credentials(self, client):
        """잘못된 인증 정보로 로그인 테스트"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자로 로그인 테스트"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )

        assert response.status_code == 401

    def test_get_me_success(self, client):
        """사용자 정보 조회 성공 테스트"""
        # 먼저 로그인
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["accessToken"]

        # 사용자 정보 조회
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "role" in data
        assert "name" in data

    def test_get_me_without_token(self, client):
        """토큰 없이 사용자 정보 조회 테스트"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_get_me_invalid_token(self, client):
        """유효하지 않은 토큰으로 사용자 정보 조회 테스트"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_logout_success(self, client):
        """로그아웃 성공 테스트"""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
