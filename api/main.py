from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.auth import PasswordAuthMiddleware
from api.routers import (
    auth,
    chat,
    config,
    context,
    embedding,
    embedding_rebuild,
    episode_profiles,
    insights,
    models,
    notebooks,
    notes,
    podcasts,
    prompts,
    search,
    settings,
    source_chat,
    sources,
    speaker_profiles,
    transformations,
)
from api.routers import commands as commands_router
from open_notebook.database.async_migrate import AsyncMigrationManager

# Import commands to register them in the API process
try:

    logger.info("Commands imported in API process")
except Exception as e:
    logger.error(f"Failed to import commands in API process: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    Runs database migrations automatically on startup.
    """
    # Configure chat log rotation
    logger.add(
        "logs/chat_{time:YYYY-MM-DD}.log",
        rotation="00:00",                    # 每天午夜切換
        retention="30 days",                 # 保留 30 天後直接刪除
        filter=lambda record: "[CHAT]" in record["message"],  # 只記錄 CHAT log
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    )

    # Startup: Run database migrations
    logger.info("Starting API initialization...")

    try:
        migration_manager = AsyncMigrationManager()
        current_version = await migration_manager.get_current_version()
        logger.info(f"Current database version: {current_version}")

        if await migration_manager.needs_migration():
            logger.warning("Database migrations are pending. Running migrations...")
            await migration_manager.run_migration_up()
            new_version = await migration_manager.get_current_version()
            logger.success(f"Migrations completed successfully. Database is now at version {new_version}")
        else:
            logger.info("Database is already at the latest version. No migrations needed.")
    except Exception as e:
        logger.error(f"CRITICAL: Database migration failed: {str(e)}")
        logger.exception(e)
        # Fail fast - don't start the API with an outdated database schema
        raise RuntimeError(f"Failed to run database migrations: {str(e)}") from e

    logger.success("API initialization completed successfully")

    # Yield control to the application
    yield

    # Shutdown: cleanup if needed
    logger.info("API shutdown complete")


app = FastAPI(
    title="Open Notebook API | 開放筆記本 API",
    description="""
    ## Open Notebook - Research Assistant API

    這是一個功能強大的研究助理系統，提供以下核心功能：

    ### 核心功能 Core Features
    - 📔 **筆記本管理** Notebook Management - 組織和管理你的研究筆記本
    - 📄 **來源管理** Source Management - 匯入和管理各種類型的資料來源（PDF、網頁、影片等）
    - 📝 **筆記管理** Note Management - 創建和管理研究筆記
    - 🔍 **智能搜尋** Smart Search - 使用向量嵌入進行語義搜尋
    - 💬 **AI 對話** AI Chat - 與你的資料進行智能對話
    - 🎙️ **播客生成** Podcast Generation - 從研究內容生成播客
    - 🔄 **內容轉換** Content Transformation - 各種內容轉換工具

    ### API 分類 API Categories
    - **auth** - 認證相關 Authentication
    - **notebooks** - 筆記本管理 Notebook Management
    - **sources** - 來源管理 Source Management
    - **notes** - 筆記管理 Note Management
    - **chat** - AI 對話 AI Chat
    - **search** - 搜尋功能 Search
    - **embedding** - 向量嵌入 Embeddings
    - **podcasts** - 播客生成 Podcast Generation
    - **models** - AI 模型管理 Model Management
    - **settings** - 系統設定 Settings
    """,
    version="0.2.2",
    lifespan=lifespan,
)

# Add password authentication middleware first
# Exclude /api/auth/status and /api/config from authentication
app.add_middleware(PasswordAuthMiddleware, excluded_paths=["/", "/health", "/docs", "/openapi.json", "/redoc", "/api/auth/status", "/api/config"])

# Add CORS middleware last (so it processes first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(notebooks.router, prefix="/api", tags=["notebooks"])
app.include_router(prompts.router, prefix="/api", tags=["prompts"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(embedding.router, prefix="/api", tags=["embedding"])
app.include_router(embedding_rebuild.router, prefix="/api/embeddings", tags=["embeddings"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(context.router, prefix="/api", tags=["context"])
app.include_router(sources.router, prefix="/api", tags=["sources"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(commands_router.router, prefix="/api", tags=["commands"])
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(episode_profiles.router, prefix="/api", tags=["episode-profiles"])
app.include_router(speaker_profiles.router, prefix="/api", tags=["speaker-profiles"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(source_chat.router, prefix="/api", tags=["source-chat"])


@app.get("/")
async def root():
    return {"message": "Open Notebook API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
