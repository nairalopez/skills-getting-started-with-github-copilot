import pytest
from fastapi.testclient import TestClient
from copy import deepcopy

from src.app import app, activities

# Create test client
client = TestClient(app)


# ============================================================================
# FIXTURES - Test setup and isolation
# ============================================================================

@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset activities state before and after each test to ensure test isolation.
    Uses autouse=True to apply to all tests automatically.
    """
    # Arrange: Save original state
    original_state = deepcopy(activities)
    
    # Let test run
    yield
    
    # Cleanup: Restore original state
    activities.clear()
    activities.update(original_state)


@pytest.fixture
def sample_email():
    """Fixture providing a test email."""
    return "student@example.com"


@pytest.fixture
def duplicate_email():
    """Fixture providing an email for duplicate tests."""
    return "duplicate@example.com"


@pytest.fixture
def activity_with_capacity():
    """Fixture providing an activity name for capacity tests."""
    return "Basketball Team"


# ============================================================================
# TESTS - Root Endpoint
# ============================================================================

class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_index(self):
        """Test that GET / redirects to /static/index.html."""
        # Arrange
        # (No setup needed)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ============================================================================
# TESTS - Get Activities Endpoint
# ============================================================================

class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_200(self):
        """Test GET /activities returns HTTP 200."""
        # Arrange
        # (No setup needed)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test GET /activities returns a dictionary."""
        # Arrange
        # (No setup needed)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_has_all_activities(self):
        """Test GET /activities returns all 9 activities."""
        # Arrange
        expected_activities = [
            "Basketball Team", "Soccer Club", "Art Club", "Drama Club",
            "Debate Club", "Science Club", "Chess Club", "Programming Class", "Gym Class"
        ]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert len(data) == 9
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_has_correct_structure(self):
        """Test that each activity has required fields."""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing '{field}' in {activity_name}"
                
    def test_get_activities_participants_is_list(self):
        """Test that participants field is always a list."""
        # Arrange
        # (No setup needed)

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_data in data.values():
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_max_participants_is_positive_int(self):
        """Test that max_participants is a positive integer."""
        # Arrange
        # (No setup needed)

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_data in data.values():
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0


# ============================================================================
# TESTS - Signup Endpoint
# ============================================================================

class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, sample_email, activity_with_capacity):
        """Test successful signup for an activity."""
        # Arrange
        activity_name = activity_with_capacity
        email = sample_email

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_to_participants(self, sample_email, activity_with_capacity):
        """Test that signup adds email to activity participants."""
        # Arrange
        activity_name = activity_with_capacity
        email = sample_email

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data[activity_name]["participants"]

    def test_signup_nonexistent_activity(self, sample_email):
        """Test signup for non-existent activity returns 404."""
        # Arrange
        activity_name = "NonExistent Club"
        email = sample_email

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_returns_400(self, activity_with_capacity):
        """Test duplicate signup for same activity returns 400."""
        # Arrange
        activity_name = activity_with_capacity
        email = "duplicate@example.com"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_multiple_different_activities(self, sample_email):
        """Test student can sign up for multiple different activities."""
        # Arrange
        email = sample_email
        activity_list = ["Art Club", "Drama Club"]

        # Act
        for activity in activity_list:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200

        # Assert
        activities_response = client.get("/activities")
        data = activities_response.json()
        for activity in activity_list:
            assert email in data[activity]["participants"]

    def test_signup_participants_isolated_by_activity(self):
        """Test that participant lists are isolated between activities."""
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

    @pytest.mark.parametrize("activity_name", [
        "Basketball Team",
        "Soccer Club",
        "Art Club",
        "Drama Club",
        "Debate Club",
        "Science Club",
        "Chess Club",
        "Programming Class",
        "Gym Class"
    ])
    def test_signup_valid_activities(self, activity_name):
        """Test signup succeeds for all valid activities."""
        # Arrange
        email = f"test@{activity_name.lower().replace(' ', '')}.com"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200

    def test_signup_case_sensitive_activity_name(self, sample_email):
        """Test that activity names are case-sensitive."""
        # Arrange
        email = sample_email
        wrong_case_activity = "basketball team"  # lowercase instead of title case

        # Act
        response = client.post(f"/activities/{wrong_case_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404