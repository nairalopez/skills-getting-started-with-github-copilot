import pytest
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_get_activities():
    """Test GET /activities returns all activities with correct structure."""
    # Arrange - TestClient is already set up

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Should have 9 activities

    # Check that all expected activities are present
    expected_activities = [
        "Basketball Team", "Soccer Club", "Art Club", "Drama Club",
        "Debate Club", "Science Club", "Chess Club", "Programming Class", "Gym Class"
    ]
    for activity in expected_activities:
        assert activity in data
        assert "description" in data[activity]
        assert "schedule" in data[activity]
        assert "max_participants" in data[activity]
        assert "participants" in data[activity]
        assert isinstance(data[activity]["participants"], list)


def test_signup_success():
    """Test successful signup adds email to activity participants."""
    # Arrange
    activity_name = "Basketball Team"
    email = "student@example.com"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Signed up" in data["message"]
    assert email in data["message"]
    assert activity_name in data["message"]

    # Verify email was added to participants
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity_name]["participants"]


def test_signup_nonexistent_activity():
    """Test signup for non-existent activity returns 404."""
    # Arrange
    activity_name = "NonExistent Club"
    email = "student@example.com"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_signup_duplicate_email():
    """Test duplicate signup for same activity returns 400."""
    # Arrange
    activity_name = "Soccer Club"
    email = "duplicate@example.com"

    # First signup
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Act - Second signup with same email
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_multiple_signups_different_activities():
    """Test student can sign up for multiple different activities."""
    # Arrange
    email = "multi@example.com"
    activities = ["Art Club", "Drama Club"]

    # Act
    for activity in activities:
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

    # Assert
    activities_response = client.get("/activities")
    data = activities_response.json()
    for activity in activities:
        assert email in data[activity]["participants"]


def test_activities_remain_separate():
    """Test that participant lists for different activities are maintained separately."""
    # Arrange
    email1 = "student1@example.com"
    email2 = "student2@example.com"
    activity1 = "Debate Club"
    activity2 = "Science Club"

    # Act
    client.post(f"/activities/{activity1}/signup?email={email1}")
    client.post(f"/activities/{activity2}/signup?email={email2}")

    # Assert
    activities_response = client.get("/activities")
    data = activities_response.json()
    assert email1 in data[activity1]["participants"]
    assert email1 not in data[activity2]["participants"]
    assert email2 in data[activity2]["participants"]
    assert email2 not in data[activity1]["participants"]