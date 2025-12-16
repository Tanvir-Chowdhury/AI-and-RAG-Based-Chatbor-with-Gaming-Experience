

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MockVectorStoreService:

    def __init__(self):

        self.sample_documents = [
            {
                'id': 'doc1',
                'score': 0.9,
                'content': 'Microgravity affects biological systems by causing bone density loss, muscle atrophy, and cardiovascular deconditioning. Studies show astronauts lose 1-2% bone density per month in space.',
                'source_file': 'microgravity_biology_study.pdf',
                'chunk_id': 'chunk_1',
                'metadata': {'type': 'research_paper', 'topic': 'microgravity'}
            },
            {
                'id': 'doc2',
                'score': 0.85,
                'content': 'SpaceX Falcon Heavy is a partially reusable heavy-lift launch vehicle with payload capacity of 63,800 kg to LEO and 16,800 kg to Mars. First successful flight was February 6, 2018.',
                'source_file': 'falcon_heavy_specs.pdf',
                'chunk_id': 'chunk_2',
                'metadata': {'type': 'technical_spec', 'topic': 'spacex'}
            },
            {
                'id': 'doc3',
                'score': 0.8,
                'content': 'Space radiation protection requires advanced shielding materials, pharmaceutical countermeasures, and magnetic field generation. Astronauts face GCRs and solar particle events.',
                'source_file': 'radiation_protection.pdf',
                'chunk_id': 'chunk_3',
                'metadata': {'type': 'review_paper', 'topic': 'radiation'}
            }
        ]

    async def initialize(self):

        logger.info("Mock vector store service initialized")

    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:

        logger.info(f"Mock: Would add {len(documents)} documents")
        return [f"mock_id_{i}" for i in range(len(documents))]

    async def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:

        logger.info(f"Mock search for: {query}")

        query_lower = query.lower()
        results = []

        for doc in self.sample_documents:
            if any(word in doc['content'].lower() for word in query_lower.split()):
                results.append(doc)

        return results[:k]

    async def get_index_stats(self) -> Dict[str, Any]:

        return {
            'total_vector_count': len(self.sample_documents),
            'dimension': 768,
            'index_fullness': 0.1
        }

    async def close(self):

        logger.info("Mock vector store service closed")