"""
Tests for SAMVAD Authentication and Session Management
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_signup_and_login_flow(client: TestClient):
    email = f"researcher.{uuid.uuid4().hex[:8]}@samvad.ai"
    password = "StrongPassword@123"
    name = "Dr. Vikram"

    # 1. Signup
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={"name": name, "email": email, "password": password},
    )
    assert signup_res.status_code == 201
    signup_data = signup_res.json()
    assert "token" in signup_data
    assert signup_data["user"]["email"] == email
    assert signup_data["user"]["name"] == name
    assert signup_data["user"]["plan"] == "free"
    token = signup_data["token"]

    # 2. Duplicate signup rejected
    dup_res = client.post(
        "/api/v1/auth/signup",
        json={"name": name, "email": email, "password": password},
    )
    assert dup_res.status_code == 400

    # 3. Verify /me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == email

    # 4. Login with correct password
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "token" in login_data
    assert login_data["user"]["name"] == name

    # 5. Login with invalid password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 6. Update profile name succeeds
    patch_res = client.patch(
        "/api/v1/auth/profile",
        json={"name": "Dr. Vikram Sarabhai"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["user"]["name"] == "Dr. Vikram Sarabhai"
    assert patch_data["user"]["plan"] == "free"

    # 6b. Attempting to set pro plan is rejected (all users are free during upcoming rollout)
    pro_attempt = client.patch(
        "/api/v1/auth/profile",
        json={"plan": "pro"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pro_attempt.status_code == 400
    assert "upcoming" in pro_attempt.json()["detail"].lower()

    # 7. Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # 8. Token should now be revoked
    revoked_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_me.status_code == 401


def test_auth_google_flow(client: TestClient):
    google_id = "goog_987654321"
    email = "google.user@example.com"
    name = "Ananya Sharma"
    avatar = "https://lh3.googleusercontent.com/a/test-avatar"

    res = client.post(
        "/api/v1/auth/google",
        json={
            "google_id": google_id,
            "email": email,
            "name": name,
            "avatar_url": avatar,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["user"]["email"] == email
    assert data["user"]["provider"] == "google"
    assert data["user"]["google_id"] == google_id
    assert data["user"]["avatar_url"] == avatar

    # Subsequent login with same Google account preserves/updates account
    token = data["token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["name"] == name


def test_pro_waitlist_registration_and_status(client: TestClient):
    test_email = f"waitlist.{uuid.uuid4().hex[:8]}@samvad.ai"

    # 1. Initially not on waitlist
    status_before = client.get(f"/api/v1/auth/waitlist/status?email={test_email}")
    assert status_before.status_code == 200
    assert status_before.json()["on_waitlist"] is False

    # 2. Join waitlist
    join_res = client.post(
        "/api/v1/auth/waitlist",
        json={"email": test_email, "name": "Dr. C.V. Raman"},
    )
    assert join_res.status_code == 200
    join_data = join_res.json()
    assert join_data["status"] == "joined"
    assert join_data["email"] == test_email
    assert join_data["position"] >= 1
    assert "SAMVAD Pro waitlist" in join_data["message"]

    # 3. Check status is now on waitlist
    status_after = client.get(f"/api/v1/auth/waitlist/status?email={test_email}")
    assert status_after.status_code == 200
    assert status_after.json()["on_waitlist"] is True
    assert status_after.json()["position"] == join_data["position"]

    # 4. Duplicate join returns already_joined idempotently
    dup_join = client.post(
        "/api/v1/auth/waitlist",
        json={"email": test_email, "name": "Dr. C.V. Raman"},
    )
    assert dup_join.status_code == 200
    assert dup_join.json()["status"] == "already_joined"
