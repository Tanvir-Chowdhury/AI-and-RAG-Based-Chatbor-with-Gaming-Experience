

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import uuid
import logging
from datetime import datetime
import asyncio

try:
    from groq import Groq
except ImportError:
    print("Installing groq...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "groq"], check=True)
    from groq import Groq

from config import settings
from database import get_db, User, ChatSession, ChatMessage
from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self):

        self.vector_service = VectorStoreService()
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

    async def create_user(self, username: str, db: Session) -> User:

        try:

            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:

                existing_user.last_active = datetime.utcnow()
                db.commit()
                db.refresh(existing_user)
                return existing_user

            user = User(username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.rollback()
            raise

    async def chat(self, message: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:

        try:

            db = next(get_db())

            user = await self.create_user(user_id, db)

            if not session_id:
                session_id = str(uuid.uuid4())

            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user.id
            ).first()

            if not session:
                session = ChatSession(
                    session_id=session_id,
                    user_id=user.id,
                    title=message[:50] + "..." if len(message) > 50 else message
                )
                db.add(session)
                db.commit()
                db.refresh(session)

            user_message = ChatMessage(
                session_id=session.id,
                message=message,
                is_user=True
            )
            db.add(user_message)

            search_results = await self.vector_service.search(message, top_k=5)

            context_chunks = []
            sources = []

            for result in search_results:
                if 'metadata' in result and 'text' in result['metadata']:
                    context_chunks.append(result['metadata']['text'])
                    sources.append({
                        'file_id': result['metadata'].get('file_id', 'unknown'),
                        'chunk_id': result['metadata'].get('chunk_id', 'unknown'),
                        'relevance_score': result.get('score', 0.0)
                    })

            context = "\n\n".join(context_chunks[:3])

            recent_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.timestamp.desc()).limit(settings.MAX_CHAT_HISTORY).all()

            history = []
            for msg in reversed(recent_messages):
                role = "user" if msg.is_user else "assistant"
                history.append({"role": role, "content": msg.message})

            system_prompt =

            messages = [
                {"role": "system", "content": system_prompt.format(context=context)}
            ]

            messages.extend(history[-6:])

            messages.append({"role": "user", "content": message})

            try:
                completion = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=messages,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS
                )

                ai_response = completion.choices[0].message.content

            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")
                ai_response = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

            ai_message = ChatMessage(
                session_id=session.id,
                message=ai_response,
                is_user=False
            )
            db.add(ai_message)
            db.commit()

            return {
                "message": ai_response,
                "sources": sources[:3],
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "message": "I apologize, but I encountered an error while processing your request. Please try again.",
                "sources": [],
                "session_id": session_id or str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            if 'db' in locals():
                db.close()

    async def get_chat_history(self, user_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:

        try:
            db = next(get_db())

            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return []

            query = db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.user_id == user.id
            )

            if session_id:
                query = query.filter(ChatSession.session_id == session_id)

            messages = query.order_by(ChatMessage.timestamp.asc()).all()

            return [
                {
                    "message": msg.message,
                    "is_user": msg.is_user,
                    "timestamp": msg.timestamp.isoformat(),
                    "session_id": msg.chat_session.session_id
                }
                for msg in messages
            ]

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()

    async def clear_history(self, user_id: str, session_id: Optional[str] = None) -> bool:

        try:
            db = next(get_db())

            user = db.query(User).filter(User.username == user_id).first()
            if not user:
                return False

            if session_id:

                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id,
                    ChatSession.user_id == user.id
                ).first()

                if session:
                    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
                    db.delete(session)
            else:

                sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
                for session in sessions:
                    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
                    db.delete(session)

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            db.rollback()
            return False
        finally:
            if 'db' in locals():
                db.close()