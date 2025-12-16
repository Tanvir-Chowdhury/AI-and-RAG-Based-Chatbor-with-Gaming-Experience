

from typing import List, Dict, Any, Optional
import logging
import uuid
import json
import numpy as np
import re
from pathlib import Path
import os

from config import settings
from services.gemini_embeddings import GeminiEmbeddingService

logger = logging.getLogger(__name__)

class SimpleVectorStoreService:

    def __init__(self):

        self.embedding_service = GeminiEmbeddingService()
        self.vectors = {}
        self.dimension = settings.PINECONE_DIMENSION
        self.research_papers_loaded = False

    def _sync_initialize(self):

        logger.info("Simple vector store initialized")

    async def initialize(self):

        await self.embedding_service.initialize()

        if not self.research_papers_loaded:
            await self._load_research_papers()

        logger.info(f"Simple vector store initialized with {len(self.vectors)} documents")

    async def _load_research_papers(self):

        try:

            research_papers_dir = Path(__file__).parent.parent.parent / "research_papers"

            if not research_papers_dir.exists():
                logger.warning(f"Research papers directory not found: {research_papers_dir}")
                return

            logger.info(f"Loading research papers from: {research_papers_dir}")

            json_files = list(research_papers_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} research paper files")

            if not json_files:
                logger.warning("No JSON files found in research papers directory")
                return

            loaded_count = 0
            for json_file in json_files:
                try:

                    with open(json_file, 'r', encoding='utf-8') as f:
                        paper_data = json.load(f)

                    text_content = self._extract_text_from_paper(paper_data, json_file.stem)

                    doi = self._extract_doi_from_paper(paper_data)
                    images = self._extract_images_from_paper(paper_data)

                    if text_content.strip():

                        embedding_list = await self.embedding_service.embed_texts([text_content])

                        if embedding_list and len(embedding_list) > 0:

                            vector_id = json_file.stem

                            metadata = {
                                "source_file": json_file.name,
                                "content": text_content[:2000],
                                "chunk_id": f"{vector_id}_chunk_0",
                                "paper_data": paper_data
                            }

                            if doi:
                                metadata["doi"] = doi
                            if images:
                                metadata["images"] = images

                            self.vectors[vector_id] = {
                                "values": embedding_list[0],
                                "metadata": metadata
                            }
                            loaded_count += 1

                            if loaded_count % 50 == 0:
                                logger.info(f"Loaded {loaded_count} papers...")

                except Exception as e:
                    logger.error(f"Error loading paper {json_file}: {e}")
                    continue

            self.research_papers_loaded = True
            logger.info(f"Successfully loaded {loaded_count} research papers into vector store")

        except Exception as e:
            logger.error(f"Error loading research papers: {e}")

    def _extract_text_from_paper(self, paper_data: dict, filename: str) -> str:

        try:
            text_parts = []

            text_parts.append(f"Filename: {filename}")

            doi = self._extract_doi_from_paper(paper_data)
            if doi:
                text_parts.append(f"DOI: {doi}")

            if isinstance(paper_data, dict):

                text_fields = [
                    'title', 'abstract', 'content', 'text', 'body',
                    'summary', 'description', 'introduction', 'conclusion',
                    'results', 'methods', 'discussion', 'findings'
                ]

                for field in text_fields:
                    if field in paper_data and paper_data[field]:
                        if isinstance(paper_data[field], str):
                            text_parts.append(f"{field.title()}: {paper_data[field]}")
                        elif isinstance(paper_data[field], list):
                            text_parts.append(f"{field.title()}: {' '.join(str(item) for item in paper_data[field])}")

                if 'sections' in paper_data and isinstance(paper_data['sections'], list):
                    for section in paper_data['sections']:
                        if isinstance(section, dict) and 'content' in section:
                            text_parts.append(section['content'])

                self._extract_strings_recursive(paper_data, text_parts)

            full_text = "\n\n".join(text_parts)

            if len(full_text.strip()) < 100:
                full_text = json.dumps(paper_data, ensure_ascii=False)[:5000]

            return full_text

        except Exception as e:
            logger.error(f"Error extracting text from paper data: {e}")
            return f"Filename: {filename}"

    def _extract_strings_recursive(self, data: Any, text_parts: List[str], max_depth: int = 3) -> None:

        if max_depth <= 0:
            return

        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and len(value.strip()) > 10:
                        text_parts.append(f"{key}: {value}")
                    elif isinstance(value, (dict, list)):
                        self._extract_strings_recursive(value, text_parts, max_depth - 1)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, str) and len(item.strip()) > 10:
                        text_parts.append(item)
                    elif isinstance(item, (dict, list)):
                        self._extract_strings_recursive(item, text_parts, max_depth - 1)
        except Exception as e:
            logger.error(f"Error in recursive string extraction: {e}")

    def _extract_doi_from_paper(self, paper_data: dict) -> Optional[str]:

        try:

            doi_patterns = [
                r'doi:\s*(10\.\d+/[^\s\]]+)',
                r'DOI:\s*(10\.\d+/[^\s\]]+)',
                r'https?://doi\.org/(10\.\d+/[^\s\]]+)',
                r'https?://dx\.doi\.org/(10\.\d+/[^\s\]]+)',
                r'\b(10\.\d+/[^\s\]]+)\b'
            ]

            search_fields = ['doi', 'DOI', 'identifier', 'url', 'link', 'citation', 'reference']

            for field in search_fields:
                if field in paper_data and paper_data[field]:
                    value = str(paper_data[field])
                    for pattern in doi_patterns:
                        match = re.search(pattern, value, re.IGNORECASE)
                        if match:
                            return match.group(1)

            def search_recursive(data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str):
                            for pattern in doi_patterns:
                                match = re.search(pattern, value, re.IGNORECASE)
                                if match:
                                    return match.group(1)
                        elif isinstance(value, (dict, list)):
                            result = search_recursive(value)
                            if result:
                                return result
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            for pattern in doi_patterns:
                                match = re.search(pattern, item, re.IGNORECASE)
                                if match:
                                    return match.group(1)
                        elif isinstance(item, (dict, list)):
                            result = search_recursive(item)
                            if result:
                                return result
                return None

            return search_recursive(paper_data)

        except Exception as e:
            logger.error(f"Error extracting DOI: {e}")
            return None

    def _extract_images_from_paper(self, paper_data: dict) -> List[str]:

        try:
            images = []

            image_fields = ['images', 'figures', 'image_urls', 'figure_urls', 'media']

            for field in image_fields:
                if field in paper_data and paper_data[field]:
                    if isinstance(paper_data[field], list):
                        for item in paper_data[field]:
                            if isinstance(item, str):
                                images.append(item)
                            elif isinstance(item, dict) and 'url' in item:
                                images.append(item['url'])
                            elif isinstance(item, dict) and 'src' in item:
                                images.append(item['src'])
                    elif isinstance(paper_data[field], str):
                        images.append(paper_data[field])

            def search_images_recursive(data):
                found_images = []
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key.lower() in ['image', 'img', 'figure', 'fig', 'url', 'src'] and isinstance(value, str):
                            if any(ext in value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']):
                                found_images.append(value)
                        elif isinstance(value, (dict, list)):
                            found_images.extend(search_images_recursive(value))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, str) and any(ext in item.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']):
                            found_images.append(item)
                        elif isinstance(item, (dict, list)):
                            found_images.extend(search_images_recursive(item))
                return found_images

            images.extend(search_images_recursive(paper_data))

            return list(set(images))

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []

    def upsert_vectors(self, vectors: List[Dict[str, Any]]):

        try:
            for vector in vectors:
                vector_id = vector["id"]
                values = vector["values"]
                metadata = vector.get("metadata", {})

                self.vectors[vector_id] = {
                    "values": values,
                    "metadata": metadata
                }

            logger.info(f"Upserted {len(vectors)} vectors")

        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise

    def query(self, vector: List[float], top_k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:

        try:

            results = []

            for vector_id, stored_vector in self.vectors.items():
                stored_values = stored_vector["values"]
                metadata = stored_vector["metadata"]

                if filter_dict:
                    skip = False
                    for key, value in filter_dict.items():
                        if metadata.get(key) != value:
                            skip = True
                            break
                    if skip:
                        continue

                similarity = self._cosine_similarity(vector, stored_values)

                results.append({
                    "id": vector_id,
                    "score": similarity,
                    "metadata": metadata
                })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error querying vectors: {e}")
            raise

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0

        return dot_product / (norm_vec1 * norm_vec2)

    def get_stats(self) -> Dict[str, Any]:

        return {
            "total_vectors": len(self.vectors),
            "dimension": self.dimension
        }

    async def search(self, query_text: str, top_k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:

        try:

            query_embedding = await self.embedding_service.embed_query(query_text)

            results = self.query(query_embedding, top_k=top_k, filter_dict=filter_dict)

            return results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise

    async def similarity_search(self, query_text: str, k: int = 10) -> List[Dict]:

        try:

            results = await self.search(query_text, top_k=k)

            formatted_results = []
            for result in results:
                metadata = result.get('metadata', {})

                doc = {
                    'id': result.get('id', ''),
                    'score': result.get('score', 0.0),
                    'content': metadata.get('content', ''),
                    'source_file': metadata.get('source_file', 'unknown'),
                    'chunk_id': metadata.get('chunk_id', ''),
                    'metadata': metadata
                }

                formatted_results.append(doc)

            logger.info(f"Found {len(formatted_results)} similar documents for query: '{query_text[:50]}...'")
            return formatted_results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")

            return []

    def save_to_file(self, filepath: str):

        with open(filepath, 'w') as f:
            json.dump(self.vectors, f, indent=2)
        logger.info(f"Vector store saved to {filepath}")

    def load_from_file(self, filepath: str):

        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                self.vectors = json.load(f)
            logger.info(f"Vector store loaded from {filepath} with {len(self.vectors)} vectors")
        else:
            logger.warning(f"File {filepath} does not exist")

    async def close(self):

        logger.info("Simple vector store service closed")