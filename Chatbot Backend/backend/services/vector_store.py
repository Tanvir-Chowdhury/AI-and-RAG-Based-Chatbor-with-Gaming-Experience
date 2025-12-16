

from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Tuple, Optional
import logging
import uuid
import json
import os
import time

from config import settings
from services.gemini_embeddings import GeminiEmbeddingService

logger = logging.getLogger(__name__)

class VectorStoreService:

    def __init__(self):

        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = settings.PINECONE_DIMENSION
        self.pc = None
        self.index = None
        self.embedding_service = GeminiEmbeddingService()

        logger.info(f"VectorStoreService created with index: {self.index_name}")

    def _sync_initialize(self):

        try:
            logger.info(f"Starting Pinecone initialization with API key: {self.api_key[:20]}...")

            self.pc = Pinecone(api_key=self.api_key)

            logger.info(f"Connecting to Pinecone index: {self.index_name}")
            self.index = self.pc.Index(self.index_name)

            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone service: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def initialize(self):

        try:

            logger.info("Initializing embedding service...")
            await self.embedding_service.initialize()

            logger.info("Calling sync Pinecone initialization...")
            self._sync_initialize()

        except Exception as e:
            logger.error(f"Failed to initialize vector store service: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:

        try:
            vectors_to_upsert = []
            document_ids = []

            for doc in documents:

                embedding = self.embedding_service.embed_text(doc['content'])

                doc_id = str(uuid.uuid4())
                document_ids.append(doc_id)

                metadata = {
                    'content': doc['content'],
                    'source_file': doc.get('source_file', ''),
                    'chunk_id': doc.get('chunk_id', ''),
                    **doc.get('metadata', {})
                }

                vectors_to_upsert.append({
                    'id': doc_id,
                    'values': embedding,
                    'metadata': metadata
                })

            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Added {len(document_ids)} documents to Pinecone")
            return document_ids

        except Exception as e:
            logger.error(f"Error adding documents to Pinecone: {e}")
            raise

    def upsert_vectors(self, vectors: List[Dict[str, Any]]):

        try:

            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")

        except Exception as e:
            logger.error(f"Error upserting vectors to Pinecone: {e}")
            raise

    async def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:

        try:

            query_embedding = self.embedding_service.embed_query(query)

            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True
            )

            documents = []
            for match in results['matches']:
                doc = {
                    'id': match['id'],
                    'score': match['score'],
                    'content': match['metadata'].get('content', ''),
                    'source_file': match['metadata'].get('source_file', ''),
                    'chunk_id': match['metadata'].get('chunk_id', ''),
                    'metadata': match['metadata']
                }
                documents.append(doc)

            logger.info(f"Retrieved {len(documents)} documents for query")
            return documents

        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            raise

    async def delete_documents(self, document_ids: List[str]) -> bool:

        try:
            self.index.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents from Pinecone: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:

        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', self.dimension),
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {'total_vector_count': 0, 'dimension': self.dimension}

    async def close(self):

        logger.info("Closing Pinecone vector store service")