
import logging
import google.generativeai as genai
from typing import List
from config import settings

logger = logging.getLogger(__name__)

class TopicExtractionService:

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=100,
            top_p=0.8,
            top_k=10
        )

    def extract_topics(self, query: str, max_topics: int = 5) -> List[str]:
        try:
            prompt = f"""Extract the key scientific and space research topics from this user query. 
Focus on the most important terms that would be useful for searching NASA space research databases.

User Query: "{query}"

Instructions:
- Extract 3-5 key topics/keywords
- Focus on scientific terms, space-related concepts, biological terms, physics concepts
- Avoid common words like "what", "how", "tell me", "about"
- Return ONLY the essential search terms as a comma-separated list, nothing else

Examples:
Query: "What are the effects of microgravity on bone density in astronauts?"
Topics: microgravity, bone density, astronauts, space physiology

Query: "How does radiation affect DNA repair in space?"
Topics: radiation, DNA repair, space biology, genetic effects

Extract topics from the query above:"""

            response = self.model.generate_content(prompt)
            
            if response and response.text:
                topics_text = response.text.strip()
                logger.info(f"Raw Gemini topics response: '{topics_text}'")
                
                # Clean the response - handle various formats
                lines = topics_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (',' in line or ' ' in line) and not line.startswith('*') and not line.lower().startswith('topics'):
                        # This looks like the actual topics
                        if ',' in line:
                            # Comma-separated format
                            topics = [topic.strip() for topic in line.split(',') if topic.strip()]
                        else:
                            # Space-separated format  
                            topics = [topic.strip() for topic in line.split() if topic.strip()]
                        
                        filtered_topics = []
                        for topic in topics[:max_topics]:
                            topic = topic.lower().strip('.,!?*')
                            if len(topic) > 2 and topic not in ['topics', 'keywords']:
                                filtered_topics.append(topic)
                        
                        if filtered_topics:
                            logger.info(f"Gemini extracted topics from '{query}': {filtered_topics}")
                            return filtered_topics
                
                # If no clean format found, fallback
                return self._fallback_extraction(query, max_topics)
            
            logger.warning("No valid response from Gemini API")
            return self._fallback_extraction(query, max_topics)
            
        except Exception as e:
            logger.error(f"Error with Gemini topic extraction: {e}")
            return self._fallback_extraction(query, max_topics)

    def extract_search_terms(self, query: str) -> str:
        try:
            prompt = f"""Convert this user query into optimal search terms for NASA's Open Science Data Repository (OSDR).

User Query: "{query}"

Instructions:
- Extract the most important scientific keywords
- Focus on space research, biology, physics, chemistry terms
- Remove conversational words and filler
- Keep technical and scientific terminology
- Limit to 3-5 key terms
- Return ONLY the terms separated by spaces, nothing else

Examples:
Input: "Can you tell me about the effects of microgravity on human bone density during long spaceflight missions?"
Output: microgravity bone density spaceflight

Input: "What research has been done on plant growth experiments in space stations?"
Output: plant growth space station experiments

Input: "How do astronauts adapt to weightlessness and what changes occur?"
Output: astronaut adaptation weightlessness physiological

Convert the query above to search terms:"""

            response = self.model.generate_content(prompt)
            
            if response and response.text:
                search_terms = response.text.strip()
                logger.info(f"Raw Gemini response: '{search_terms}'")
                
                # Clean the response - remove any markdown formatting or extra text
                lines = search_terms.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('*') and not line.startswith('#') and not line.lower().startswith('output'):
                        # This looks like the actual search terms
                        cleaned_terms = []
                        for term in line.split():
                            term = term.lower().strip('.,!?*')
                            if len(term) > 2:
                                cleaned_terms.append(term)
                        
                        if cleaned_terms:
                            result = ' '.join(cleaned_terms[:5])
                            logger.info(f"Gemini generated search terms from '{query}': '{result}'")
                            return result
                
                # If no clean line found, fallback
                return self._fallback_search_terms(query)
            
            logger.warning("No valid response from Gemini API")
            return self._fallback_search_terms(query)
            
        except Exception as e:
            logger.error(f"Error with Gemini search term extraction: {e}")
            return self._fallback_search_terms(query)

    def _fallback_extraction(self, query: str, max_topics: int) -> List[str]:
        space_keywords = {
            'microgravity', 'weightlessness', 'astronaut', 'spaceflight', 'spacecraft',
            'radiation', 'cosmic', 'orbital', 'gravity', 'mars', 'moon', 'iss',
            'space', 'nasa', 'spacex', 'rocket', 'launch', 'mission', 'satellite',
            'biology', 'experiment', 'research', 'study', 'gene', 'protein', 'cell',
            'tissue', 'organ', 'muscle', 'bone', 'blood', 'brain', 'heart',
            'physiology', 'psychology', 'behavior', 'stress', 'adaptation',
            'metabolism', 'immune', 'cardiovascular', 'neural', 'respiratory'
        }
        
        stop_words = {
            'what', 'how', 'why', 'when', 'where', 'tell', 'me', 'about', 'the',
            'can', 'you', 'please', 'explain', 'describe', 'i', 'would', 'like',
            'to', 'understand', 'of', 'on', 'in', 'at', 'by', 'for', 'with',
            'during', 'and', 'or', 'but', 'if', 'as', 'are', 'is', 'was', 'were'
        }
        
        words = query.lower().split()
        topics = []
        
        for word in words:
            clean_word = word.strip('.,?!')
            if clean_word in space_keywords:
                topics.append(clean_word)
            elif len(clean_word) > 3 and clean_word not in stop_words:
                topics.append(clean_word)
        
        return topics[:max_topics]

    def _fallback_search_terms(self, query: str) -> str:
        fallback_topics = self._fallback_extraction(query, 5)
        return ' '.join(fallback_topics) if fallback_topics else query