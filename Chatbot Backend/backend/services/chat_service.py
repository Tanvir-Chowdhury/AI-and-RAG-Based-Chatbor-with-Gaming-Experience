

from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai
import json
import uuid
import logging
from datetime import datetime

from config import settings
from services.database import get_db, ChatSession, ChatMessage
from services.vector_store import VectorStoreService
from services.nasa_osdr_service import NASAOSDRService
from services.topic_extraction_service import TopicExtractionService
from models.schemas import ChatResponse, SourceDocument

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self, vector_service: VectorStoreService):

        self.vector_service = vector_service
        self.nasa_service = NASAOSDRService()
        self.topic_extractor = TopicExtractionService()

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        self.generation_config = genai.types.GenerationConfig(
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
            top_p=0.8,
            top_k=40
        )

    async def create_chat_session(self, session_name: str, db: Session) -> ChatSession:

        try:
            session = ChatSession(
                session_name=session_name
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"Created new chat session: {session_name}")
            return session

        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            db.rollback()
            raise

    async def get_sessions(self, db: Session) -> List[ChatSession]:

        return db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

    async def get_session_messages(self, session_id: str, db: Session) -> List[ChatMessage]:

        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()

    async def save_message(self, session_id: str, role: str, content: str, sources: List[Dict] = None, db: Session = None) -> ChatMessage:

        try:
            sources_json = json.dumps(sources) if sources else None

            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                sources=sources_json
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()
                db.commit()

            return message

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            db.rollback()
            raise

    async def get_chat_history_for_context(self, session_id: str, db: Session) -> List[Dict[str, str]]:

        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(settings.MAX_CHAT_HISTORY).all()

            gemini_messages = []
            for msg in reversed(messages):
                if msg.role == "user":
                    gemini_messages.append({"role": "user", "parts": [msg.content]})
                elif msg.role == "assistant":
                    gemini_messages.append({"role": "model", "parts": [msg.content]})

            return gemini_messages

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    async def generate_response(self, user_message: str, session_id: str = None, db: Session = None) -> ChatResponse:

        try:

            if not session_id:
                session = await self.create_chat_session("New Chat", db)
                session_id = session.id

            await self.save_message(session_id, "user", user_message, None, db)

            logger.info(f" DUAL SEARCH INITIATED for query: '{user_message}'")
            logger.info(" Searching Pinecone vector database...")

            pinecone_docs = await self.vector_service.similarity_search(user_message, k=settings.RETRIEVAL_K)
            logger.info(f" Pinecone search complete: Found {len(pinecone_docs)} documents")

            logger.info("Extracting topics from user query...")
            search_topics = self.topic_extractor.extract_search_terms(user_message)
            logger.info(f" Extracted topics for NASA OSDR: '{search_topics}'")

            logger.info(" Searching NASA OSDR API with extracted topics...")
            nasa_results = await self.nasa_service.comprehensive_search(search_topics)
            nasa_studies_count = len(nasa_results.get('studies', []))
            nasa_experiments_count = len(nasa_results.get('experiments', []))
            nasa_missions_count = len(nasa_results.get('missions', []))
            logger.info(f" NASA OSDR search complete: {nasa_studies_count} studies, {nasa_experiments_count} experiments, {nasa_missions_count} missions")

            context_parts = []
            source_documents = []
            all_related_images = []

            for i, doc in enumerate(pinecone_docs, 1):
                source = doc.get('source_file', 'unknown')
                content = doc.get('content', '').strip()
                chunk_id = doc.get('chunk_id', '')
                metadata = doc.get('metadata', {}) or {}

                related_images = metadata.get('related_images') or metadata.get('images') or []
                if isinstance(related_images, str):

                    related_images = [img.strip() for img in related_images.split(',') if img.strip()]
                if related_images:
                    all_related_images.extend(related_images)
                context_parts.append(f"Research Paper {i} ({source}):\n{content}")
                source_documents.append(SourceDocument(
                    content=content,
                    source_file=f"Research Paper: {source}",
                    chunk_id=chunk_id,
                    metadata={**metadata, "source_type": "pinecone"},
                    related_images=related_images
                ))

            nasa_context_count = len(pinecone_docs)
            for study in nasa_results.get('studies', []):
                nasa_context_count += 1

                study_title = study.get('enhanced_title', study.get('title', 'Unknown Study'))
                study_description = study.get('enhanced_description', study.get('description', ''))
                study_id = study.get('id', '')
                study_url = f"https://osdr.nasa.gov/bio/repo/data/studies/{study_id}" if study_id else ""

                nasa_content_parts = [f"Title: {study_title}"]

                if study_description:
                    nasa_content_parts.append(f"Description: {study_description}")

                detailed_metadata = study.get('detailed_metadata', {})
                if detailed_metadata:

                    organisms = detailed_metadata.get('organisms', [])
                    if organisms:
                        org_names = [org.get('name', str(org)) if isinstance(org, dict) else str(org) for org in organisms]
                        nasa_content_parts.append(f"Organisms: {', '.join(org_names[:3])}")

                    factors = detailed_metadata.get('factors', [])
                    if factors:
                        factor_names = [f.get('name', str(f)) if isinstance(f, dict) else str(f) for f in factors[:3]]
                        nasa_content_parts.append(f"Study Factors: {', '.join(factor_names)}")

                    protocols = detailed_metadata.get('protocols', [])
                    if protocols:
                        protocol_names = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in protocols[:2]]
                        nasa_content_parts.append(f"Protocols: {', '.join(protocol_names)}")

                    space_program = detailed_metadata.get('space_program', '')
                    flight_program = detailed_metadata.get('flight_program', '')
                    if space_program:
                        nasa_content_parts.append(f"Space Program: {space_program}")
                    if flight_program:
                        nasa_content_parts.append(f"Flight Program: {flight_program}")

                    managing_center = detailed_metadata.get('managing_center', '')
                    if managing_center:
                        nasa_content_parts.append(f"Managing NASA Center: {managing_center}")

                    publications = detailed_metadata.get('publications', [])
                    if publications:
                        pub_titles = [p.get('title', str(p)) if isinstance(p, dict) else str(p) for p in publications[:2]]
                        nasa_content_parts.append(f"Related Publications: {', '.join(pub_titles)}")

                if study_url:
                    nasa_content_parts.append(f"Study URL: {study_url}")

                nasa_content = "\n".join(nasa_content_parts)

                context_parts.append(f"NASA OSDR Study {nasa_context_count} ({study_title}):\n{nasa_content}")
                source_documents.append(SourceDocument(
                    content=nasa_content,
                    source_file=f"NASA OSDR: {study_title}",
                    chunk_id=study_id,
                    metadata={
                        "source_type": "nasa_osdr",
                        "study_id": study_id,
                        "study_url": study_url,
                        "has_detailed_metadata": bool(detailed_metadata),
                        "organisms": detailed_metadata.get('organisms', []) if detailed_metadata else [],
                        "factors": detailed_metadata.get('factors', []) if detailed_metadata else [],
                        "space_program": detailed_metadata.get('space_program', '') if detailed_metadata else '',
                        "flight_program": detailed_metadata.get('flight_program', '') if detailed_metadata else '',
                        **{k: v for k, v in study.items() if k not in ['enhanced_title', 'enhanced_description', 'detailed_metadata']}
                    },
                    related_images=[]
                ))

            for experiment in nasa_results.get('experiments', [])[:2]:
                nasa_context_count += 1
                exp_title = experiment.get('title', 'Unknown Experiment')
                exp_description = experiment.get('description', 'No description available')

                nasa_content = f"Title: {exp_title}\nDescription: {exp_description}"
                context_parts.append(f"NASA OSDR Experiment {nasa_context_count} ({exp_title}):\n{nasa_content}")
                source_documents.append(SourceDocument(
                    content=nasa_content,
                    source_file=f"NASA OSDR Experiment: {exp_title}",
                    chunk_id=experiment.get('id', ''),
                    metadata={
                        "source_type": "nasa_osdr_experiment",
                        **{k: v for k, v in experiment.items() if k not in ['title', 'description']}
                    },
                    related_images=[]
                ))

            formatted_context = "\n\n---\n\n".join(context_parts)

            chat_history = await self.get_chat_history_for_context(session_id, db)

            response_content = await self._generate_gemini_response(user_message, formatted_context, chat_history)

            sources_dict = [doc.dict() for doc in source_documents]
            message = await self.save_message(session_id, "assistant", response_content, sources_dict, db)

            unique_related_images = list(dict.fromkeys(all_related_images))

            logger.info(f" Response generated with {len(source_documents)} total sources:")
            logger.info(f"    Pinecone sources: {len(pinecone_docs)}")
            logger.info(f"    NASA OSDR sources: {len(source_documents) - len(pinecone_docs)}")
            logger.info(f"     Related images: {len(unique_related_images)}")

            return ChatResponse(
                message=response_content,
                sources=source_documents,
                related_images=unique_related_images,
                session_id=session_id,
                message_id=message.id,
                timestamp=message.created_at
            )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _generate_gemini_response(self, user_message: str, context: str, chat_history: List[Dict[str, str]]) -> str:

        try:

            system_prompt = f"""You are an expert NASA Research Assistant with access to comprehensive space research data and current NASA mission information.

INSTRUCTIONS:
1. Use the provided RESEARCH CONTEXT to answer questions accurately
2. Reference sources naturally without mentioning internal search methods, databases, or technical infrastructure
3. If context is relevant, reference it as "according to NASA research" or "based on current NASA studies"
4. If context doesn't contain relevant info, say so and provide general knowledge
5. Be detailed and technical when appropriate
6. For greetings, respond warmly and explain your expertise in NASA and space research
7. Maintain conversation flow using chat history
8. NEVER mention Pinecone, vector databases, web scraping, OSDR, APIs, or any technical search methods

RESPONSE STYLE:
- Professional yet friendly
- Use specific examples from research and current NASA activities when available
- Cite sources naturally (e.g., "According to NASA research..." or "Current NASA studies show...")
- Provide step-by-step explanations for complex topics
- Present information as if it comes from your comprehensive knowledge base

RESEARCH CONTEXT:
{context}

USER QUESTION: {user_message}

Please provide a detailed answer using the research context above, presenting the information as part of your expertise without revealing any technical search methods or database details."""

            if chat_history:
                chat = self.model.start_chat(history=chat_history)
                response = chat.send_message(system_prompt, generation_config=self.generation_config)
            else:
                response = self.model.generate_content(system_prompt, generation_config=self.generation_config)

            return response.text

        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"I apologize, but I encountered an error while generating a response: {str(e)}. Please try again."