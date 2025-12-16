

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from services.database import get_db
from models.schemas import (
    ChatRequest, ChatResponse, ChatSessionCreate, ChatSessionResponse,
    ChatHistoryResponse, ChatMessageResponse
)
from services.chat_service import ChatService

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    try:
        chat_service: ChatService = getattr(request.app.state, 'chat_service', None)

        if not chat_service:
            raise HTTPException(
                status_code=503,
                detail="Chat service is currently unavailable. Please check server configuration."
            )

        response = await chat_service.generate_response(
            user_message=chat_request.message,
            session_id=chat_request.session_id,
            db=db
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    request: Request,
    db: Session = Depends(get_db)
):

    try:
        chat_service: ChatService = request.app.state.chat_service

        session = await chat_service.create_chat_session(
            session_name=session_data.session_name,
            db=db
        )

        return ChatSessionResponse.from_orm(session)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/chat/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db)
):

    try:
        chat_service: ChatService = request.app.state.chat_service

        from ..services.database import ChatSession
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = await chat_service.get_session_messages(session_id, db)

        message_responses = []
        for msg in messages:
            sources = []
            if msg.sources:
                import json
                try:
                    sources_data = json.loads(msg.sources)
                    from ..models.schemas import SourceDocument
                    sources = [SourceDocument(**source) for source in sources_data]
                except:
                    sources = []

            message_responses.append(ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                sources=sources,
                created_at=msg.created_at
            ))

        return ChatHistoryResponse(
            session=ChatSessionResponse.from_orm(session),
            messages=message_responses
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db)
):

    try:
        from ..services.database import ChatSession, ChatMessage

        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()

        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        db.delete(session)
        db.commit()

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))