

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
import google.generativeai as genai

from config import settings
from services.database import get_db, ChatSession, ChatMessage
from services.simple_vector_store import SimpleVectorStoreService
from models.schemas import ChatResponse, SourceDocument

logger = logging.getLogger(__name__)

class SimpleChatService:

    def __init__(self, vector_service: SimpleVectorStoreService):

        self.vector_service = vector_service

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def call_gemini_api(self, messages: List[Dict[str, str]]) -> str:

        try:
            logger.info(f"Calling Gemini API with {len(messages)} messages")

            conversation_parts = []

            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')

                if role == 'system':

                    conversation_parts.append(f"Instructions: {content}")
                elif role == 'user':
                    conversation_parts.append(f"User: {content}")
                elif role == 'assistant':
                    conversation_parts.append(f"Assistant: {content}")

            full_prompt = "\n\n".join(conversation_parts)

            full_prompt +=

            response = self.model.generate_content(full_prompt)

            if response and response.text:
                logger.info("Successfully received response from Gemini")

                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()

                return response_text
            else:
                logger.error("Empty response from Gemini")
                return json.dumps({
                    "response_type": "research",
                    "messages": [{"message_id": 1, "content": "I'm experiencing technical difficulties. Please try again later.", "type": "text"}],
                    "sources": [],
                    "summary": "Technical error occurred"
                })

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return json.dumps({
                "response_type": "research",
                "messages": [{"message_id": 1, "content": "I'm experiencing technical difficulties. Please try again later.", "type": "text"}],
                "sources": [],
                "summary": "Technical error occurred"
            })

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

            chat_messages = []
            for msg in reversed(messages):
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            return chat_messages

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    async def generate_response(self, user_message: str, session_id: str = None, db: Session = None) -> ChatResponse:

        try:

            if not session_id:
                session = await self.create_chat_session("New Chat", db)
                session_id = session.id

            await self.save_message(session_id, "user", user_message, None, db)

            context_docs = await self.vector_service.similarity_search(user_message, k=settings.RETRIEVAL_K)

            context_parts = []
            source_documents = []

            for i, doc in enumerate(context_docs, 1):
                source = doc.get('source_file', 'unknown')
                content = doc.get('content', '').strip()
                chunk_id = doc.get('chunk_id', '')
                metadata = doc.get('metadata', {})

                doi = metadata.get('doi', 'Unknown DOI')
                display_source = f"{doi}" if doi != 'Unknown DOI' else source

                context_parts.append(f"Document {i} (DOI: {doi}):\n{content}")

                source_documents.append(SourceDocument(
                    content=content,
                    source_file=source,
                    chunk_id=chunk_id,
                    metadata=metadata
                ))

            formatted_context = "\n\n---\n\n".join(context_parts)

            chat_history = await self.get_chat_history_for_context(session_id, db)

            messages = self.create_prompt(user_message, formatted_context, chat_history)

            response_content = self.call_gemini_api(messages)

            try:

                json_response = json.loads(response_content)

                if self._validate_json_response(json_response):

                    json_response = self._enhance_json_with_sources(json_response, source_documents, user_message)
                    final_response = json.dumps(json_response, indent=2)
                else:

                    final_response = self._create_fallback_json_response(response_content, source_documents, user_message)

            except json.JSONDecodeError:

                final_response = self._create_fallback_json_response(response_content, source_documents, user_message)

            sources_dict = [doc.dict() for doc in source_documents]
            message = await self.save_message(session_id, "assistant", final_response, sources_dict, db)

            return ChatResponse(
                message=final_response,
                sources=source_documents,
                session_id=session_id,
                message_id=message.id,
                timestamp=message.created_at
            )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def create_prompt(self, question: str, context: str, chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:

        system_msg =

        messages = [{"role": "system", "content": system_msg}]

        if chat_history:
            messages.extend(chat_history[-8:])

        current_message = f

        messages.append({"role": "user", "content": current_message})

        return messages

    def _validate_json_response(self, json_response: dict) -> bool:

        try:
            required_fields = ['response_type', 'messages', 'sources', 'summary']

            for field in required_fields:
                if field not in json_response:
                    logger.warning(f"Missing required field: {field}")
                    return False

            messages = json_response.get('messages', [])
            if not isinstance(messages, list) or len(messages) == 0:
                logger.warning("Messages field is not a valid list or is empty")
                return False

            for i, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    logger.warning(f"Message {i} is not a dictionary")
                    return False
                if 'message_id' not in msg or 'content' not in msg or 'type' not in msg:
                    logger.warning(f"Message {i} missing required fields")
                    return False

                msg_type = msg.get('type')
                content = msg.get('content')

                if msg_type == 'data' and isinstance(content, dict):

                    if 'table_data' in content:
                        table_data = content['table_data']
                        if not isinstance(table_data, dict) or 'headers' not in table_data or 'rows' not in table_data:
                            logger.warning(f"Message {i} has invalid table_data structure")
                            return False

                elif msg_type == 'technical' and isinstance(content, dict):

                    if 'experimental_results' in content:
                        exp_results = content['experimental_results']
                        if not isinstance(exp_results, dict):
                            logger.warning(f"Message {i} has invalid experimental_results structure")
                            return False

            sources = json_response.get('sources', [])
            if not isinstance(sources, list):
                logger.warning("Sources field is not a list")
                return False

            for i, source in enumerate(sources):
                if not isinstance(source, dict):
                    logger.warning(f"Source {i} is not a dictionary")
                    return False
                required_source_fields = ['source_id', 'title', 'relevance']
                for field in required_source_fields:
                    if field not in source:
                        logger.warning(f"Source {i} missing required field: {field}")
                        return False

            if json_response.get('response_type') not in ['research', 'conversational']:
                logger.warning("Invalid response_type")
                return False

            logger.info("JSON response validation successful")
            return True

        except Exception as e:
            logger.error(f"Error validating JSON response: {e}")
            return False

            sources = json_response.get('sources', [])
            if not isinstance(sources, list):
                return False

            return True

        except Exception:
            return False

    def _filter_relevant_images(self, user_query: str, all_images: List[str], source_documents: List[SourceDocument]) -> List[str]:

        try:

            query_lower = user_query.lower()

            image_keywords = {
                'bone': ['bone', 'osteo', 'skeletal', 'calcium', 'mineral'],
                'muscle': ['muscle', 'muscular', 'myofiber', 'atrophy', 'sarcopenia'],
                'heart': ['heart', 'cardiac', 'cardiovascular', 'ecg', 'rhythm'],
                'brain': ['brain', 'neural', 'neuro', 'cognitive', 'cerebral'],
                'liver': ['liver', 'hepatic', 'metabolism', 'lipid'],
                'cell': ['cell', 'cellular', 'mitochondria', 'nucleus', 'membrane'],
                'gene': ['gene', 'dna', 'rna', 'expression', 'transcription', 'genomic'],
                'protein': ['protein', 'enzyme', 'amino', 'peptide'],
                'experiment': ['experiment', 'assay', 'test', 'analysis', 'method'],
                'data': ['graph', 'chart', 'plot', 'figure', 'diagram', 'table'],
                'space': ['space', 'microgravity', 'flight', 'astronaut', 'iss', 'mission'],
                'mouse': ['mouse', 'mice', 'rodent', 'animal', 'specimen']
            }

            relevant_categories = []
            for category, keywords in image_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    relevant_categories.append(category)

            if not relevant_categories:
                relevant_categories = ['experiment', 'data', 'space']

            relevant_images = []
            max_images_per_source = 3

            for doc in source_documents:
                if hasattr(doc, 'metadata') and doc.metadata and "images" in doc.metadata:
                    doc_images = doc.metadata["images"]
                    doc_content_lower = doc.content.lower()

                    image_scores = []

                    for img_url in doc_images:
                        score = 0
                        img_lower = img_url.lower()

                        if any(skip in img_lower for skip in ['logo', 'banner', 'header']):
                            continue

                        for category in relevant_categories:
                            category_keywords = image_keywords[category]

                            if any(keyword in img_lower for keyword in category_keywords):
                                score += 3

                            if any(keyword in doc_content_lower for keyword in category_keywords):
                                score += 2

                        if 'fig' in img_lower and any(char.isdigit() for char in img_lower):
                            score += 2

                        if any(term in img_lower for term in ['graph', 'chart', 'plot', 'data', 'result']):
                            score += 1

                        if score > 0:
                            image_scores.append((img_url, score))

                    image_scores.sort(key=lambda x: x[1], reverse=True)
                    relevant_images.extend([img for img, score in image_scores[:max_images_per_source]])

            seen = set()
            filtered_images = []
            for img in relevant_images:
                if img not in seen:
                    seen.add(img)
                    filtered_images.append(img)

            max_total_images = 10
            final_images = filtered_images[:max_total_images]

            logger.info(f"Filtered images: {len(all_images)} -> {len(final_images)} (Query: {user_query[:50]}...)")

            return final_images

        except Exception as e:
            logger.error(f"Error filtering relevant images: {e}")

            filtered = [img for img in all_images if not any(skip in img.lower() for skip in ['logo', 'banner'])]
            return filtered[:5]

    def _enhance_json_with_sources(self, json_response: dict, source_documents: List[SourceDocument], user_query: str = "") -> dict:

        try:

            sources = []
            all_images = []

            for i, doc in enumerate(source_documents, 1):

                doi = "Not available"
                images = []
                title = doc.source_file

                if hasattr(doc, 'metadata') and doc.metadata:

                    if "doi" in doc.metadata:
                        doi = f"doi: {doc.metadata['doi']}"

                    if "images" in doc.metadata:
                        images = doc.metadata["images"]
                        all_images.extend(images)

                    if "paper_data" in doc.metadata and isinstance(doc.metadata["paper_data"], dict):
                        paper_data = doc.metadata["paper_data"]
                        if "title" in paper_data:
                            title = paper_data["title"]

                source_entry = {
                    "source_id": i,
                    "title": title,
                    "authors": "Not specified",
                    "publication_year": "Unknown",
                    "journal": "Unknown",
                    "doi": doi,
                    "relevance": "Referenced in response context",
                    "data_extracted": f"Topic: {title}, {doc.content[:100]}..."
                }

                if images:
                    source_entry["images"] = images

                sources.append(source_entry)

            json_response["sources"] = sources

            if all_images and user_query:
                relevant_images = self._filter_relevant_images(user_query, all_images, source_documents)
                if relevant_images:
                    json_response["images"] = relevant_images
            elif all_images:

                filtered = [img for img in all_images if not any(skip in img.lower() for skip in ['logo', 'banner'])]
                json_response["images"] = list(set(filtered[:5]))

            if "metadata" not in json_response:
                json_response["metadata"] = {}

            json_response["metadata"]["sources_consulted"] = len(source_documents)
            json_response["metadata"]["total_images_available"] = len(all_images)
            if "images" in json_response:
                json_response["metadata"]["relevant_images_selected"] = len(json_response["images"])

            return json_response

        except Exception as e:
            logger.error(f"Error enhancing JSON with sources: {e}")
            return json_response

    def _create_fallback_json_response(self, response_text: str, source_documents: List[SourceDocument], user_query: str = "") -> str:

        try:

            response_type = "conversational" if any(word in response_text.lower()
                                                 for word in ["hello", "hi", "greeting", "help"]) else "research"

            parts = response_text.split('\n\n')
            messages = []

            for i, part in enumerate(parts, 1):
                if part.strip():
                    messages.append({
                        "message_id": i,
                        "content": part.strip(),
                        "type": "text"
                    })

            sources = []
            all_images = []

            for i, doc in enumerate(source_documents, 1):
                doi = "Not available"
                images = []
                title = doc.source_file

                if hasattr(doc, 'metadata') and doc.metadata:

                    if "doi" in doc.metadata:
                        doi = f"doi: {doc.metadata['doi']}"

                    if "images" in doc.metadata:
                        images = doc.metadata["images"]
                        all_images.extend(images)

                    if "paper_data" in doc.metadata and isinstance(doc.metadata["paper_data"], dict):
                        paper_data = doc.metadata["paper_data"]
                        if "title" in paper_data:
                            title = paper_data["title"]

                source_entry = {
                    "source_id": i,
                    "title": title,
                    "authors": "Not specified",
                    "publication_year": "Unknown",
                    "journal": "Unknown",
                    "doi": doi,
                    "relevance": "Referenced in response context",
                    "data_extracted": "Content used for response generation"
                }

                if images:
                    source_entry["images"] = images

                sources.append(source_entry)

            fallback_response = {
                "response_type": response_type,
                "messages": messages if messages else [{"message_id": 1, "content": response_text, "type": "text"}],
                "sources": sources,
                "metadata": {
                    "total_sources_consulted": len(source_documents),
                    "confidence_level": "medium",
                    "response_completeness": "partial",
                    "total_images_available": len(all_images)
                },
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }

            if all_images and user_query:
                relevant_images = self._filter_relevant_images(user_query, all_images, source_documents)
                if relevant_images:
                    fallback_response["images"] = relevant_images
                    fallback_response["metadata"]["relevant_images_selected"] = len(relevant_images)
            elif all_images:

                filtered = [img for img in all_images if not any(skip in img.lower() for skip in ['logo', 'banner'])]
                fallback_response["images"] = list(set(filtered[:5]))
                if fallback_response.get("images"):
                    fallback_response["metadata"]["relevant_images_selected"] = len(fallback_response["images"])

            return json.dumps(fallback_response, indent=2)

        except Exception as e:
            logger.error(f"Error creating fallback JSON response: {e}")

            return json.dumps({
                "response_type": "research",
                "messages": [{"message_id": 1, "content": response_text, "type": "text"}],
                "sources": [],
                "metadata": {
                    "total_sources_consulted": 0,
                    "confidence_level": "low",
                    "response_completeness": "limited"
                },
                "summary": "Response generated with technical difficulties"
            })