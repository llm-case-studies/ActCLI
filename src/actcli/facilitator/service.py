"""Facilitator service - FastAPI server for AI communication."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .session import Session, Participant, Message, ParticipantType, ParticipantStatus


# Pydantic models for API
class CreateSessionRequest(BaseModel):
    name: str
    description: str = ""


class JoinSessionRequest(BaseModel):
    session_id: str
    name: str
    type: str = "ai"
    provider: Optional[str] = None
    model: Optional[str] = None


class SendMessageRequest(BaseModel):
    session_id: str
    from_id: str
    to_id: str  # or "all"
    content: str
    type: str = "chat"
    metadata: Dict = {}


class FacilitatorService:
    """Smart facilitator service for multi-AI communication."""

    def __init__(self):
        self.app = FastAPI(title="AI Facilitator Service")
        self.sessions: Dict[str, Session] = {}
        self.websockets: Dict[str, WebSocket] = {}  # participant_id -> websocket

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post("/sessions")
        async def create_session(req: CreateSessionRequest):
            """Create a new session."""
            session = Session(name=req.name, description=req.description)
            self.sessions[session.id] = session
            return {
                "session_id": session.id,
                "name": session.name,
                "created_at": session.created_at.isoformat(),
            }

        @self.app.get("/sessions")
        async def list_sessions():
            """List all sessions."""
            return {
                "sessions": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "participant_count": len(s.participants),
                        "message_count": len(s.messages),
                        "is_broadcasting": s.is_broadcasting,
                        "viewer_count": s.viewer_count,
                    }
                    for s in self.sessions.values()
                ]
            }

        @self.app.get("/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get session details."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            return {
                "id": session.id,
                "name": session.name,
                "description": session.description,
                "participants": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "type": p.type.value,
                        "status": p.status.value,
                        "provider": p.provider,
                        "model": p.model,
                    }
                    for p in session.participants.values()
                ],
                "message_count": len(session.messages),
                "is_broadcasting": session.is_broadcasting,
            }

        @self.app.post("/sessions/{session_id}/join")
        async def join_session(session_id: str, req: JoinSessionRequest):
            """Join a session as a participant."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            participant = Participant(
                name=req.name,
                type=ParticipantType(req.type),
                provider=req.provider,
                model=req.model,
            )
            session.add_participant(participant)

            return {
                "participant_id": participant.id,
                "session_id": session.id,
            }

        @self.app.post("/messages")
        async def send_message(req: SendMessageRequest):
            """Send a message in a session."""
            session = self.sessions.get(req.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            message = Message(
                session_id=req.session_id,
                from_id=req.from_id,
                to_id=req.to_id,
                type=req.type,
                content=req.content,
                metadata=req.metadata,
            )

            # Check if sender is rate limited
            sender = session.get_participant(req.from_id)
            if sender and sender.status == ParticipantStatus.RATE_LIMITED:
                session.queue_message(message)
                return {
                    "message_id": message.id,
                    "status": "queued",
                    "reason": "rate_limited",
                }

            # Route the message
            await self._route_message(session, message)

            return {
                "message_id": message.id,
                "status": "delivered",
            }

        @self.app.websocket("/ws/{session_id}/{participant_id}")
        async def websocket_endpoint(
            websocket: WebSocket,
            session_id: str,
            participant_id: str,
        ):
            """WebSocket endpoint for real-time communication."""
            await websocket.accept()

            session = self.sessions.get(session_id)
            if not session:
                await websocket.close(code=1008, reason="Session not found")
                return

            participant = session.get_participant(participant_id)
            if not participant:
                await websocket.close(code=1008, reason="Participant not found")
                return

            # Register websocket
            self.websockets[participant_id] = websocket
            participant.websocket_id = participant_id

            try:
                # Send queued messages
                queued = session.get_queued_messages_for(participant_id)
                for msg in queued:
                    await websocket.send_json(self._message_to_dict(msg))
                    session.message_queue.remove(msg)

                # Listen for messages
                while True:
                    data = await websocket.receive_json()
                    await self._handle_websocket_message(
                        session, participant, data
                    )

            except WebSocketDisconnect:
                del self.websockets[participant_id]
                participant.status = ParticipantStatus.DISCONNECTED

        @self.app.websocket("/broadcast/{session_id}")
        async def broadcast_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket endpoint for viewers (broadcast mode)."""
            await websocket.accept()

            session = self.sessions.get(session_id)
            if not session:
                await websocket.close(code=1008, reason="Session not found")
                return

            session.viewer_count += 1

            try:
                # Send session history
                for msg in session.messages[-50:]:  # Last 50 messages
                    await websocket.send_json(self._message_to_dict(msg))

                # Keep connection alive and stream new messages
                while True:
                    await asyncio.sleep(1)
                    # Real-time messages will be pushed via broadcast

            except WebSocketDisconnect:
                session.viewer_count -= 1

    async def _route_message(self, session: Session, message: Message):
        """Route a message to appropriate recipient(s)."""
        session.add_message(message)

        # Broadcast to all if target is "all"
        if message.to_id == "all":
            for p in session.get_active_participants():
                if p.id != message.from_id:  # Don't echo back
                    await self._deliver_to_participant(p, message)
        else:
            # Send to specific participant
            recipient = session.get_participant(message.to_id)
            if recipient and recipient.is_available():
                await self._deliver_to_participant(recipient, message)
            elif recipient:
                # Queue if recipient not available
                session.queue_message(message)

        # Broadcast to viewers if session is broadcasting
        if session.is_broadcasting:
            await self._broadcast_to_viewers(session, message)

    async def _deliver_to_participant(
        self, participant: Participant, message: Message
    ):
        """Deliver a message to a participant via WebSocket."""
        if participant.websocket_id in self.websockets:
            ws = self.websockets[participant.websocket_id]
            try:
                await ws.send_json(self._message_to_dict(message))
                message.delivered = True
            except Exception:
                # WebSocket closed, queue the message
                message.queued = True

    async def _broadcast_to_viewers(self, session: Session, message: Message):
        """Broadcast a message to all viewers."""
        # TODO: Implement viewer websocket tracking
        pass

    async def _handle_websocket_message(
        self, session: Session, participant: Participant, data: dict
    ):
        """Handle incoming WebSocket message."""
        msg_type = data.get("type", "chat")

        if msg_type == "chat":
            message = Message(
                session_id=session.id,
                from_id=participant.id,
                to_id=data.get("to", "all"),
                content=data.get("content", ""),
                metadata=data.get("metadata", {}),
            )
            await self._route_message(session, message)

        elif msg_type == "status":
            # Update participant status
            new_status = data.get("status")
            if new_status:
                participant.status = ParticipantStatus(new_status)

    def _message_to_dict(self, message: Message) -> dict:
        """Convert message to dict for JSON serialization."""
        return {
            "id": message.id,
            "session_id": message.session_id,
            "from": message.from_id,
            "to": message.to_id,
            "type": message.type,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
        }


def create_app() -> FastAPI:
    """Create and return the FastAPI app."""
    service = FacilitatorService()
    return service.app
