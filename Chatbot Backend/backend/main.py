

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging

from config import settings
from routers import chat, health
from services.database import init_db
from services.vector_store import VectorStoreService
from services.chat_service import ChatService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vector_service = None
chat_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):

    global vector_service, chat_service

    try:

        logger.info("Initializing database...")
        init_db()

        logger.info("Initializing vector store service...")
        try:
            logger.info("Creating VectorStoreService instance...")
            vector_service = VectorStoreService()
            logger.info("Calling vector_service.initialize()...")
            await vector_service.initialize()
            logger.info("Vector store service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            vector_service = None

        logger.info("Initializing chat service...")
        if vector_service:
            chat_service = ChatService(vector_service)
            logger.info("Chat service initialized with vector store")
        else:

            chat_service = None
            logger.warning("Chat service not initialized - vector store unavailable")

        app.state.vector_service = vector_service
        app.state.chat_service = chat_service

        logger.info("Application startup complete!")
        yield

    except Exception as e:
        logger.error(f"Critical error during application initialization: {e}")

        app.state.vector_service = None
        app.state.chat_service = None
        logger.warning("Application started with degraded functionality")
        yield
    finally:

        logger.info("Application shutdown...")
        if vector_service:
            try:
                await vector_service.close()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

app = FastAPI(
    title="NASA SpaceX Chatbot API",
    description="AI-powered chatbot with access to space research database",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):

    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/")
async def root():

    return {
        "message": "NASA SpaceX Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )