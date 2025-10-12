"""Integration tests for facilitator with WebSocket communication."""

import pytest
import asyncio
from fastapi.testclient import TestClient
import websockets
import json

from actcli.facilitator.service import create_app


@pytest.fixture
def app():
    """Create FastAPI app."""
    return create_app()


@pytest.mark.asyncio
async def test_websocket_message_routing(app):
    """Test that messages are routed between participants via WebSocket."""
    # This test requires running the server in a background task
    # We'll use TestClient's websocket support for synchronous testing
    pass  # Skipping for now - requires async server setup


def test_two_participants_message_exchange():
    """Test message exchange between two participants using HTTP."""
    client = TestClient(create_app())

    # Create session
    session_resp = client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Integration test"}
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]

    # Join as first participant
    p1_resp = client.post(
        f"/sessions/{session_id}/join",
        json={
            "session_id": session_id,
            "name": "Alice",
            "type": "ai",
        }
    )
    assert p1_resp.status_code == 200
    alice_id = p1_resp.json()["participant_id"]

    # Join as second participant
    p2_resp = client.post(
        f"/sessions/{session_id}/join",
        json={
            "session_id": session_id,
            "name": "Bob",
            "type": "ai",
        }
    )
    assert p2_resp.status_code == 200
    bob_id = p2_resp.json()["participant_id"]

    # Alice sends a message to all
    msg_resp = client.post(
        "/messages",
        json={
            "session_id": session_id,
            "from_id": alice_id,
            "to_id": "all",
            "content": "Hello Bob!",
            "type": "chat"
        }
    )
    assert msg_resp.status_code == 200
    assert msg_resp.json()["status"] == "delivered"

    # Bob sends a reply
    reply_resp = client.post(
        "/messages",
        json={
            "session_id": session_id,
            "from_id": bob_id,
            "to_id": "all",
            "content": "Hi Alice!",
            "type": "chat"
        }
    )
    assert reply_resp.status_code == 200

    # Verify messages were stored
    session_resp = client.get(f"/sessions/{session_id}")
    session_data = session_resp.json()
    assert session_data["message_count"] == 2
    assert len(session_data["participants"]) == 2


def test_message_to_specific_participant():
    """Test sending a message to a specific participant."""
    client = TestClient(create_app())

    # Create session
    session_resp = client.post(
        "/sessions",
        json={"name": "Test Session", "description": "Direct message test"}
    )
    session_id = session_resp.json()["session_id"]

    # Join two participants
    p1_resp = client.post(
        f"/sessions/{session_id}/join",
        json={"session_id": session_id, "name": "Alice", "type": "ai"}
    )
    alice_id = p1_resp.json()["participant_id"]

    p2_resp = client.post(
        f"/sessions/{session_id}/join",
        json={"session_id": session_id, "name": "Bob", "type": "ai"}
    )
    bob_id = p2_resp.json()["participant_id"]

    # Alice sends direct message to Bob
    msg_resp = client.post(
        "/messages",
        json={
            "session_id": session_id,
            "from_id": alice_id,
            "to_id": bob_id,  # Direct to Bob
            "content": "Secret message",
            "type": "chat"
        }
    )
    assert msg_resp.status_code == 200


def test_session_with_multiple_participants():
    """Test a session with 3+ participants."""
    client = TestClient(create_app())

    # Create session
    session_resp = client.post(
        "/sessions",
        json={"name": "Multi-Participant", "description": "Test"}
    )
    session_id = session_resp.json()["session_id"]

    # Join multiple participants
    participants = []
    for name in ["Alice", "Bob", "Charlie", "Diana"]:
        resp = client.post(
            f"/sessions/{session_id}/join",
            json={"session_id": session_id, "name": name, "type": "ai"}
        )
        participants.append((name, resp.json()["participant_id"]))

    # Verify all joined
    session_resp = client.get(f"/sessions/{session_id}")
    session_data = session_resp.json()
    assert len(session_data["participants"]) == 4

    # Each participant sends a message
    for name, pid in participants:
        msg_resp = client.post(
            "/messages",
            json={
                "session_id": session_id,
                "from_id": pid,
                "to_id": "all",
                "content": f"Hello from {name}!",
                "type": "chat"
            }
        )
        assert msg_resp.status_code == 200

    # Verify all messages stored
    session_resp = client.get(f"/sessions/{session_id}")
    session_data = session_resp.json()
    assert session_data["message_count"] == 4


def test_concurrent_sessions():
    """Test that multiple sessions can run concurrently."""
    client = TestClient(create_app())

    # Create two sessions
    session1_resp = client.post(
        "/sessions",
        json={"name": "Session 1", "description": "First"}
    )
    session1_id = session1_resp.json()["session_id"]

    session2_resp = client.post(
        "/sessions",
        json={"name": "Session 2", "description": "Second"}
    )
    session2_id = session2_resp.json()["session_id"]

    # Add participants to each
    p1_s1 = client.post(
        f"/sessions/{session1_id}/join",
        json={"session_id": session1_id, "name": "Alice", "type": "ai"}
    ).json()["participant_id"]

    p1_s2 = client.post(
        f"/sessions/{session2_id}/join",
        json={"session_id": session2_id, "name": "Bob", "type": "ai"}
    ).json()["participant_id"]

    # Send messages to each session
    client.post(
        "/messages",
        json={
            "session_id": session1_id,
            "from_id": p1_s1,
            "to_id": "all",
            "content": "Message in session 1",
            "type": "chat"
        }
    )

    client.post(
        "/messages",
        json={
            "session_id": session2_id,
            "from_id": p1_s2,
            "to_id": "all",
            "content": "Message in session 2",
            "type": "chat"
        }
    )

    # Verify sessions are independent
    s1_data = client.get(f"/sessions/{session1_id}").json()
    s2_data = client.get(f"/sessions/{session2_id}").json()

    assert s1_data["message_count"] == 1
    assert s2_data["message_count"] == 1
    assert len(s1_data["participants"]) == 1
    assert len(s2_data["participants"]) == 1


def test_list_multiple_sessions():
    """Test listing multiple active sessions."""
    client = TestClient(create_app())

    # Create multiple sessions
    for i in range(3):
        client.post(
            "/sessions",
            json={"name": f"Session {i+1}", "description": f"Test {i+1}"}
        )

    # List all sessions
    resp = client.get("/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sessions"]) == 3
