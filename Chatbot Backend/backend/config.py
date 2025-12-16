

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

    HOST: str = Field(default="0.0.0.0", description="Host to bind the application")
    PORT: int = Field(default=8000, description="Port to bind the application")
    DEBUG: bool = Field(default=False, description="Debug mode")

    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    GEMINI_API_KEY: str = Field(default="AIzaSyBVtnTuyA832Xcmvskxvj6j_sQ7XqcyHDs", description="Google Gemini API key")
    PINECONE_API_KEY: str = Field(default="pcsk_7EoxRh_B6VbERarf1YntjRZEnvqYgk9NqA7xWPuseVkBF1hApntfpZMe2cNciHyYqu2msL", description="Pinecone API key")

    PINECONE_INDEX_NAME: str = Field(default="nasa-spacex-chatbot", description="Pinecone index name")
    PINECONE_DIMENSION: int = Field(default=768, description="Pinecone vector dimension for Gemini embeddings (768 recommended)")

    DATABASE_URL: str = Field(default="sqlite:///./chatbot.db", description="Database URL")

    MAX_CHAT_HISTORY: int = Field(default=10, description="Maximum chat history length per user")
    RETRIEVAL_K: int = Field(default=4, description="Number of documents to retrieve")

    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    LLM_TEMPERATURE: float = Field(default=0.7, description="LLM temperature")
    LLM_MAX_TOKENS: int = Field(default=1500, description="LLM max tokens")

    GEMINI_EMBEDDING_MODEL: str = Field(default="models/text-embedding-004", description="Gemini embedding model")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def __init__(self, **kwargs):

        if 'PORT' in os.environ:
            kwargs['PORT'] = int(os.environ['PORT'])
        super().__init__(**kwargs)

settings = Settings()

print(f"Config loaded - GEMINI_API_KEY: {settings.GEMINI_API_KEY[:20]}...")
print(f"Config loaded - PINECONE_API_KEY: {settings.PINECONE_API_KEY[:20]}...")
print(f"Config loaded - PINECONE_INDEX_NAME: {settings.PINECONE_INDEX_NAME}")