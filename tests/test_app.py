"""
Tests for the Mergington High School API

Tests cover all endpoints including activity retrieval, signups, and unregistration.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestActivityEndpoints:
    """Tests for activity retrieval endpoints"""

    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Soccer Team" in data

    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_single_activity(self, client):
        """Test getting a single activity by name"""
        response = client.get("/activities/Chess Club")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" not in data  # Activity name is in the response as a value
        assert "description" in data
        assert "Learn strategies and compete in chess tournaments" in data["description"]

    def test_get_nonexistent_activity(self, client):
        """Test getting an activity that doesn't exist"""
        response = client.get("/activities/NonExistent Club")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestSignupEndpoints:
    """Tests for signup and unregistration endpoints"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_duplicate(self, client):
        """Test that duplicate signups are rejected"""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]

    def test_unregister_not_registered(self, client):
        """Test unregistration for an activity the student is not in"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistration from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestActivityParticipants:
    """Tests for verifying participant counts and lists"""

    def test_get_participants_after_signup(self, client):
        """Test that participants list is updated after signup"""
        email = "participant@mergington.edu"
        
        # Get initial participant count
        response_before = client.get("/activities/Math Club")
        participants_before = len(response_before.json()["participants"])
        
        # Sign up
        client.post(
            "/activities/Math Club/signup",
            params={"email": email}
        )
        
        # Get updated participant count
        response_after = client.get("/activities/Math Club")
        participants_after = len(response_after.json()["participants"])
        assert participants_after == participants_before + 1
        assert email in response_after.json()["participants"]

    def test_get_participants_after_unregister(self, client):
        """Test that participants list is updated after unregistration"""
        email = "emma@mergington.edu"
        
        # Sign up first
        client.post(
            "/activities/Debate Team/signup",
            params={"email": email}
        )
        
        # Get participant count after signup
        response_with = client.get("/activities/Debate Team")
        participants_with = len(response_with.json()["participants"])
        
        # Unregister
        client.post(
            "/activities/Debate Team/unregister",
            params={"email": email}
        )
        
        # Get updated participant count
        response_without = client.get("/activities/Debate Team")
        participants_without = len(response_without.json()["participants"])
        assert participants_without == participants_with - 1
        assert email not in response_without.json()["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
