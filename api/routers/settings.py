from fastapi import APIRouter, HTTPException
from loguru import logger

from api.models import SettingsResponse, SettingsUpdate
from open_notebook.domain.content_settings import ContentSettings
from open_notebook.exceptions import InvalidInputError

router = APIRouter()


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """
    Get all application settings.

    獲取所有應用程式設定。

    包括：
    - 文檔處理引擎設定
    - URL 處理引擎設定
    - 向量嵌入選項
    - 自動刪除檔案設定
    - YouTube 偏好語言
    """
    try:
        settings: ContentSettings = await ContentSettings.get_instance()  # type: ignore[assignment]

        return SettingsResponse(
            default_content_processing_engine_doc=settings.default_content_processing_engine_doc,
            default_content_processing_engine_url=settings.default_content_processing_engine_url,
            default_embedding_option=settings.default_embedding_option,
            auto_delete_files=settings.auto_delete_files,
            youtube_preferred_languages=settings.youtube_preferred_languages,
        )
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching settings: {str(e)}")


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(settings_update: SettingsUpdate):
    """
    Update application settings.

    更新應用程式設定。

    - **default_content_processing_engine_doc**: 文檔處理引擎（auto, docling, simple）
    - **default_content_processing_engine_url**: URL 處理引擎（auto, firecrawl, jina, simple）
    - **default_embedding_option**: 嵌入選項（ask, always, never）
    - **auto_delete_files**: 自動刪除檔案（yes, no）
    - **youtube_preferred_languages**: YouTube 偏好語言列表
    """
    try:
        settings: ContentSettings = await ContentSettings.get_instance()  # type: ignore[assignment]

        # Update only provided fields
        if settings_update.default_content_processing_engine_doc is not None:
            # Cast to proper literal type
            from typing import Literal, cast
            settings.default_content_processing_engine_doc = cast(
                Literal["auto", "docling", "simple"],
                settings_update.default_content_processing_engine_doc
            )
        if settings_update.default_content_processing_engine_url is not None:
            from typing import Literal, cast
            settings.default_content_processing_engine_url = cast(
                Literal["auto", "firecrawl", "jina", "simple"],
                settings_update.default_content_processing_engine_url
            )
        if settings_update.default_embedding_option is not None:
            from typing import Literal, cast
            settings.default_embedding_option = cast(
                Literal["ask", "always", "never"],
                settings_update.default_embedding_option
            )
        if settings_update.auto_delete_files is not None:
            from typing import Literal, cast
            settings.auto_delete_files = cast(
                Literal["yes", "no"],
                settings_update.auto_delete_files
            )
        if settings_update.youtube_preferred_languages is not None:
            settings.youtube_preferred_languages = settings_update.youtube_preferred_languages

        await settings.update()

        return SettingsResponse(
            default_content_processing_engine_doc=settings.default_content_processing_engine_doc,
            default_content_processing_engine_url=settings.default_content_processing_engine_url,
            default_embedding_option=settings.default_embedding_option,
            auto_delete_files=settings.auto_delete_files,
            youtube_preferred_languages=settings.youtube_preferred_languages,
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")