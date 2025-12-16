

from google import genai
from google.genai import types
import numpy as np
from typing import List, Union
import logging

from config import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingService:

    def __init__(self):

        self.api_key = settings.GEMINI_API_KEY
        self.model_name = "gemini-embedding-001"
        self.output_dimensionality = 768
        self._client = None

    def _get_client(self):

        if self._client is None:
            try:

                genai.configure(api_key=self.api_key)
                self._client = genai.Client()
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        return self._client

    def get_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:

        try:
            client = self._get_client()

            if not text or not text.strip():
                logger.warning("Empty text provided, returning zero vector")
                return [0.0] * self.output_dimensionality

            text = text.strip()

            if len(text) > 8000:
                text = text[:8000]
                logger.warning(f"Text truncated to 8000 characters")

            result = client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.output_dimensionality
                )
            )

            if result.embeddings and len(result.embeddings) > 0:
                embedding_values = result.embeddings[0].values

                embedding_np = np.array(embedding_values)

                normalized_embedding = embedding_np / np.linalg.norm(embedding_np)

                return normalized_embedding.tolist()
            else:
                logger.error("No embeddings returned from Gemini API")
                return [0.0] * self.output_dimensionality

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")

            if "quota" in str(e).lower() or "429" in str(e):
                logger.error("Gemini API quota exceeded. Please check your billing or wait for reset.")
                raise Exception("Gemini API quota exceeded. Please upgrade your plan or wait for daily reset.")

            return [0.0] * self.output_dimensionality

    def get_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:

        try:
            client = self._get_client()

            if not texts:
                return []

            cleaned_texts = []
            for text in texts:
                if not text or not text.strip():
                    cleaned_texts.append("empty")
                else:
                    text = text.strip()
                    if len(text) > 8000:
                        text = text[:8000]
                    cleaned_texts.append(text)

            result = client.models.embed_content(
                model=self.model_name,
                contents=cleaned_texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.output_dimensionality
                )
            )

            embeddings = []
            for embedding_obj in result.embeddings:
                embedding_values = embedding_obj.values

                embedding_np = np.array(embedding_values)
                normalized_embedding = embedding_np / np.linalg.norm(embedding_np)

                embeddings.append(normalized_embedding.tolist())

            return embeddings

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")

            if "quota" in str(e).lower() or "429" in str(e):
                logger.error("Gemini API quota exceeded. Please check your billing or wait for reset.")
                raise Exception("Gemini API quota exceeded. Please upgrade your plan or wait for daily reset.")

            return [[0.0] * self.output_dimensionality] * len(texts)

    def get_query_embedding(self, query: str) -> List[float]:

        return self.get_embedding(query, task_type="RETRIEVAL_QUERY")

    def get_similarity(self, text1: str, text2: str) -> float:

        try:

            embeddings = self.get_embeddings([text1, text2], task_type="SEMANTIC_SIMILARITY")

            if len(embeddings) == 2:

                emb1 = np.array(embeddings[0])
                emb2 = np.array(embeddings[1])

                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                return float(similarity)
            else:
                logger.error("Failed to get embeddings for similarity calculation")
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    async def embed_text(self, text: str) -> List[float]:

        return self.get_embedding(text)

    async def embed_query(self, query: str) -> List[float]:

        return self.get_query_embedding(query)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:

        return self.get_embeddings(texts)