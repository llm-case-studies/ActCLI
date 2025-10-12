"""Tests for facilitator service."""

import pytest
from fastapi.testclient import TestClient

from actcli.facilitator.service import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_create_session(client):
    """Test creating a new session."""
    response = client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Test description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["name"] == "Test Session"
    assert "created_at" in data


def test_list_sessions_empty(client):
    """Test listing sessions when none exist."""
    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) == 0


def test_list_sessions_after_create(client):
    """Test listing sessions after creating one."""
    # Create a session
    client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Test"}
    )

    # List sessions
    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["name"] == "Test Session"


def test_get_session_not_found(client):
    """Test getting a session that doesn't exist."""
    response = client.get("/sessions/nonexistent")
    assert response.status_code == 404


def test_get_session(client):
    """Test getting a session by ID."""
    # Create session
    create_resp = client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Test"}
    )
    session_id = create_resp.json()["session_id"]

    # Get session
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["name"] == "Test Session"
    assert "participants" in data
    assert len(data["participants"]) == 0


def test_join_session(client):
    """Test joining a session as a participant."""
    # Create session
    create_resp = client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Test"}
    )
    session_id = create_resp.json()["session_id"]

    # Join session
    join_resp = client.post(
        f"/sessions/{session_id}/join",
        json={
            "session_id": session_id,
            "name": "TestBot",
            "type": "ai",
            "provider": "test",
            "model": "test-model"
        }
    )
    assert join_resp.status_code == 200
    data = join_resp.json()
    assert "participant_id" in data
    assert data["session_id"] == session_id

    # Verify participant was added
    session_resp = client.get(f"/sessions/{session_id}")
    session_data = session_resp.json()
    assert len(session_data["participants"]) == 1
    assert session_data["participants"][0]["name"] == "TestBot"
    assert session_data["participants"][0]["provider"] == "test"


def test_join_nonexistent_session(client):
    """Test joining a session that doesn't exist."""
    response = client.post(
        "/sessions/nonexistent/join",
        json={
            "session_id": "nonexistent",
            "name": "TestBot",
            "type": "ai"
        }
    )
    assert response.status_code == 404


def test_multiple_participants(client):
    """Test multiple participants joining a session."""
    # Create session
    create_resp = client.post(
        "/sessions",
        json={"name": "Multi-Participant Session", "description": "Test"}
    )
    session_id = create_resp.json()["session_id"]

    # Join as first participant
    client.post(
        f"/sessions/{session_id}/join",
        json={
            "session_id": session_id,
            "name": "Bot1",
            "type": "ai",
        }
    )

    # Join as second participant
    client.post(
        f"/sessions/{session_id}/join",
        json={
            "session_id": session_id,
            "name": "Bot2",
            "type": "ai",
        }
    )

    # Verify both participants
    session_resp = client.get(f"/sessions/{session_id}")
    session_data = session_resp.json()
    assert len(session_data["participants"]) == 2
    names = {p["name"] for p in session_data["participants"]}
    assert names == {"Bot1", "Bot2"}


def test_message_includes_from_name(client):
    """Test that messages include from_name field."""
    # Create session
    create_resp = client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Test"}
    )
    session_id = create_resp.json()["session_id"]

    # Join as participant
    join_resp = client.post(
        f"/sessions/{session_id}/join",
        json={
            "session_id": session_id,
            "name": "TestBot",
            "type": "ai",
        }
    )
    participant_id = join_resp.json()["participant_id"]

    # Send a message via HTTP endpoint
    msg_resp = client.post(
        "/messages",
        json={
            "session_id": session_id,
            "from_id": participant_id,
            "to_id": "all",
            "content": "Test message",
            "type": "chat"
        }
    )
    assert msg_resp.status_code == 200

    # Get session to verify message was stored
    session_resp = client.get(f"/sessions/{session_id}")
    session_data = session_resp.json()
    assert session_data["message_count"] >= 1
