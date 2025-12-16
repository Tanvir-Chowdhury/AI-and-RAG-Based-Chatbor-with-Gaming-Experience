

import asyncio
import logging
from typing import List, Optional
import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingService:

    def __init__(self):

        self.api_key = settings.GEMINI_API_KEY
        self.model_name = "models/text-embedding-004"
        self.output_dimensionality = 768

        self._sync_initialize()

    def _sync_initialize(self):

        try:
            genai.configure(api_key=self.api_key)
            logger.info("Gemini embedding service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embedding service: {e}")
            raise

    async def initialize(self):

        try:
            genai.configure(api_key=self.api_key)
            logger.info("Gemini embedding service initialized successfully (async)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embedding service (async): {e}")
            raise

    def embed_text(self, text: str) -> List[float]:

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type='retrieval_document'
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:

        try:
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type='retrieval_document'
                )
                embeddings.append(result['embedding'])
            return embeddings
        except Exception as e:
            logger.error(f"Error generating text embeddings: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type='retrieval_query'
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def get_dimension(self) -> int:

        return settings.PINECONE_DIMENSION

    def get_embedding(self, text: str) -> List[float]:

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                output_dimensionality=self.output_dimensionality,
                task_type='retrieval_document'
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            raise