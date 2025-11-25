import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from langchain_core.runnables import RunnableConfig
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import ChatSession, Note, Notebook, Source
from open_notebook.exceptions import (
    NotFoundError,
)
from open_notebook.graphs.chat import graph as chat_graph

router = APIRouter()

# Request/Response models
class CreateSessionRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID to create session for")
    title: Optional[str] = Field(None, description="Optional session title")
    model_override: Optional[str] = Field(
        None, description="Optional model override for this session"
    )


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, description="New session title")
    model_override: Optional[str] = Field(
        None, description="Model override for this session"
    )


class ChatMessage(BaseModel):
    id: str = Field(..., description="Message ID")
    type: str = Field(..., description="Message type (human|ai)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatSessionResponse(BaseModel):
    id: str = Field(..., description="Session ID")
    title: str = Field(..., description="Session title")
    notebook_id: Optional[str] = Field(None, description="Notebook ID")
    created: str = Field(..., description="Creation timestamp")
    updated: str = Field(..., description="Last update timestamp")
    message_count: Optional[int] = Field(
        None, description="Number of messages in session"
    )
    model_override: Optional[str] = Field(
        None, description="Model override for this session"
    )


class ChatSessionWithMessagesResponse(ChatSessionResponse):
    messages: List[ChatMessage] = Field(
        default_factory=list, description="Session messages"
    )


class ExecuteChatRequest(BaseModel):
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User message content")
    context: Dict[str, Any] = Field(
        ..., description="Chat context with sources and notes"
    )
    model_override: Optional[str] = Field(
        None, description="Optional model override for this message"
    )
    prompt_id: Optional[str] = Field(
        None, description="Optional system prompt ID to use for this message"
    )
    include_citations: bool = Field(
        False, description="Whether to include document citations in AI responses"
    )


class ExecuteChatResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    messages: List[ChatMessage] = Field(..., description="Updated message list")


class BuildContextRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID")
    context_config: Dict[str, Any] = Field(..., description="Context configuration")


class BuildContextResponse(BaseModel):
    context: Dict[str, Any] = Field(..., description="Built context data")
    token_count: int = Field(..., description="Estimated token count")
    char_count: int = Field(..., description="Character count")


class SuccessResponse(BaseModel):
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")


@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(notebook_id: str = Query(..., description="Notebook ID | 筆記本 ID")):
    """
    Get all chat sessions for a notebook.

    獲取筆記本的所有對話會話。

    - **notebook_id**: 筆記本的唯一識別碼
    """
    try:
        # Get notebook to verify it exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Get sessions for this notebook
        sessions = await notebook.get_chat_sessions()

        return [
            ChatSessionResponse(
                id=session.id or "",
                title=session.title or "Untitled Session",
                notebook_id=notebook_id,
                created=str(session.created),
                updated=str(session.updated),
                message_count=0,  # TODO: Add message count if needed
                model_override=getattr(session, "model_override", None),
            )
            for session in sessions
        ]
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Notebook not found")
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching chat sessions: {str(e)}"
        )


@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new chat session.

    創建新的對話會話。

    - **notebook_id**: 筆記本 ID
    - **title**: 會話標題（選填）
    - **model_override**: 覆蓋預設的 AI 模型（選填）
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(request.notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Create new session
        session = ChatSession(
            title=request.title or f"Chat Session {asyncio.get_event_loop().time():.0f}",
            model_override=request.model_override,
        )
        await session.save()

        # Relate session to notebook
        await session.relate_to_notebook(request.notebook_id)

        return ChatSessionResponse(
            id=session.id or "",
            title=session.title or "",
            notebook_id=request.notebook_id,
            created=str(session.created),
            updated=str(session.updated),
            message_count=0,
            model_override=session.model_override,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Notebook not found")
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating chat session: {str(e)}"
        )


@router.get(
    "/chat/sessions/{session_id}", response_model=ChatSessionWithMessagesResponse
)
async def get_session(session_id: str):
    """
    Get a specific session with its messages.

    獲取特定對話會話及其所有訊息。

    - **session_id**: 對話會話的唯一識別碼
    """
    try:
        # Get session
        # Ensure session_id has proper table prefix
        full_session_id = (
            session_id
            if session_id.startswith("chat_session:")
            else f"chat_session:{session_id}"
        )
        session = await ChatSession.get(full_session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get session state from LangGraph to retrieve messages
        thread_state = chat_graph.get_state(
            config=RunnableConfig(configurable={"thread_id": session_id})
        )

        # Extract messages from state
        messages: list[ChatMessage] = []
        if thread_state and thread_state.values and "messages" in thread_state.values:
            # Get current time in UTC+8
            utc_plus_8 = timezone(timedelta(hours=8))
            current_time = datetime.now(utc_plus_8).isoformat()

            for msg in thread_state.values["messages"]:
                messages.append(
                    ChatMessage(
                        id=getattr(msg, "id", f"msg_{len(messages)}"),
                        type=msg.type if hasattr(msg, "type") else "unknown",
                        content=msg.content if hasattr(msg, "content") else str(msg),
                        timestamp=current_time,
                    )
                )

        # Find notebook_id (we need to query the relationship)
        # Ensure session_id has proper table prefix
        full_session_id = (
            session_id
            if session_id.startswith("chat_session:")
            else f"chat_session:{session_id}"
        )

        notebook_query = await repo_query(
            "SELECT out FROM refers_to WHERE in = $session_id",
            {"session_id": ensure_record_id(full_session_id)},
        )

        notebook_id = notebook_query[0]["out"] if notebook_query else None

        if not notebook_id:
            # This might be an old session created before API migration
            logger.warning(
                f"No notebook relationship found for session {session_id} - may be an orphaned session"
            )

        return ChatSessionWithMessagesResponse(
            id=session.id or "",
            title=session.title or "Untitled Session",
            notebook_id=notebook_id,
            created=str(session.created),
            updated=str(session.updated),
            message_count=len(messages),
            messages=messages,
            model_override=getattr(session, "model_override", None),
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@router.put("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(session_id: str, request: UpdateSessionRequest):
    """
    Update session title.

    更新對話會話標題。

    - **session_id**: 對話會話 ID
    - **title**: 新的會話標題（選填）
    - **model_override**: 覆蓋的模型設定（選填）
    """
    try:
        # Ensure session_id has proper table prefix
        full_session_id = (
            session_id
            if session_id.startswith("chat_session:")
            else f"chat_session:{session_id}"
        )
        session = await ChatSession.get(full_session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        update_data = request.model_dump(exclude_unset=True)

        if "title" in update_data:
            session.title = update_data["title"]

        if "model_override" in update_data:
            session.model_override = update_data["model_override"]

        await session.save()

        # Find notebook_id
        # Ensure session_id has proper table prefix
        full_session_id = (
            session_id
            if session_id.startswith("chat_session:")
            else f"chat_session:{session_id}"
        )
        notebook_query = await repo_query(
            "SELECT out FROM refers_to WHERE in = $session_id",
            {"session_id": ensure_record_id(full_session_id)},
        )
        notebook_id = notebook_query[0]["out"] if notebook_query else None

        return ChatSessionResponse(
            id=session.id or "",
            title=session.title or "",
            notebook_id=notebook_id,
            created=str(session.created),
            updated=str(session.updated),
            message_count=0,
            model_override=session.model_override,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")


@router.delete("/chat/sessions/{session_id}", response_model=SuccessResponse)
async def delete_session(session_id: str):
    """
    Delete a chat session.

    刪除對話會話。

    - **session_id**: 要刪除的對話會話 ID
    """
    try:
        # Ensure session_id has proper table prefix
        full_session_id = (
            session_id
            if session_id.startswith("chat_session:")
            else f"chat_session:{session_id}"
        )
        session = await ChatSession.get(full_session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await session.delete()

        return SuccessResponse(success=True, message="Session deleted successfully")
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.post("/chat/execute", response_model=ExecuteChatResponse)
async def execute_chat(request: ExecuteChatRequest):
    """
    Execute a chat request and get AI response.

    執行對話請求並獲取 AI 回應。

    - **session_id**: 對話會話 ID
    - **message**: 使用者訊息內容
    - **notebook_id**: 筆記本 ID（用於上下文）
    """
    try:
        # Start total timing
        total_start = time.time()

        # Step 1: Get session
        step_start = time.time()
        # Ensure session_id has proper table prefix
        full_session_id = (
            request.session_id
            if request.session_id.startswith("chat_session:")
            else f"chat_session:{request.session_id}"
        )
        session = await ChatSession.get(full_session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        db_duration = (time.time() - step_start) * 1000

        # Step 2: Get notebook and prompt
        step_start = time.time()
        # Determine model override (per-request override takes precedence over session-level)
        model_override = (
            request.model_override
            if request.model_override is not None
            else getattr(session, "model_override", None)
        )

        # Get notebook_id from session to fetch custom_system_prompt
        notebook_query = await repo_query(
            "SELECT out FROM refers_to WHERE in = $session_id",
            {"session_id": ensure_record_id(full_session_id)},
        )
        notebook_id = notebook_query[0]["out"] if notebook_query else None

        # Get custom_system_prompt from notebook (not session)
        # Priority: request.prompt_id > active_prompt_id > custom_system_prompt
        custom_system_prompt = None
        if notebook_id:
            notebook = await Notebook.get(notebook_id)
            if notebook:
                logger.info(f"Notebook {notebook_id} - request.prompt_id: {request.prompt_id}, active_prompt_id: {notebook.active_prompt_id}")

                # First priority: prompt_id from request (user's explicit choice)
                if request.prompt_id:
                    from open_notebook.domain.notebook import SystemPrompt
                    try:
                        specified_prompt = await SystemPrompt.get(request.prompt_id)
                        custom_system_prompt = specified_prompt.content
                        logger.info(f"Using specified prompt from request: {specified_prompt.name} - {custom_system_prompt[:50]}...")
                    except Exception as e:
                        logger.warning(f"Failed to get specified prompt {request.prompt_id}: {e}")

                # Second priority: active prompt from notebook
                if not custom_system_prompt and notebook.active_prompt_id:
                    active_prompt = await notebook.get_active_prompt()
                    if active_prompt:
                        custom_system_prompt = active_prompt.content
                        logger.info(f"Using active prompt: {active_prompt.name} - {custom_system_prompt[:50]}...")

                # Third priority: custom_system_prompt field (legacy)
                if not custom_system_prompt and notebook.custom_system_prompt:
                    custom_system_prompt = notebook.custom_system_prompt
                    logger.info(f"Using notebook custom_system_prompt: {custom_system_prompt[:50]}...")

                if not custom_system_prompt:
                    logger.info("No system prompt set (all sources are empty)")
        db_duration += (time.time() - step_start) * 1000

        # Step 3: Get current state
        step_start = time.time()
        current_state = chat_graph.get_state(
            config=RunnableConfig(
                configurable={"thread_id": request.session_id}
            )
        )
        db_duration += (time.time() - step_start) * 1000

        # Step 4: Prepare context and state
        step_start = time.time()
        state_values = current_state.values if current_state else {}
        state_values["messages"] = state_values.get("messages", [])
        state_values["context"] = request.context
        state_values["model_override"] = model_override
        state_values["custom_system_prompt"] = custom_system_prompt
        state_values["include_citations"] = request.include_citations

        # Log context info
        sources_count = len(request.context.get("sources", []))
        notes_count = len(request.context.get("notes", []))
        logger.info(f"Chat context - sources: {sources_count}, notes: {notes_count}")
        logger.info(f"Include citations: {request.include_citations}")
        if sources_count > 0:
            logger.info(f"First source: {request.context['sources'][0].get('title', 'No title')[:50]}")
        if notes_count > 0:
            logger.info(f"First note: {str(request.context['notes'][0])[:100]}")

        # Add user message to state
        from langchain_core.messages import HumanMessage

        user_message = HumanMessage(content=request.message)
        state_values["messages"].append(user_message)

        # Execute LLM
        llm_start = time.time()
        result = chat_graph.invoke(
            input=state_values,  # type: ignore[arg-type]
            config=RunnableConfig(
                configurable={
                    "thread_id": request.session_id,
                    "model_id": model_override,
                }
            ),
        )
        llm_duration = (time.time() - llm_start) * 1000

        # Update session
        await session.save()

        # Convert messages to response
        messages: list[ChatMessage] = []
        # Get current time in UTC+8
        utc_plus_8 = timezone(timedelta(hours=8))
        current_time = datetime.now(utc_plus_8).isoformat()

        for msg in result.get("messages", []):
            messages.append(
                ChatMessage(
                    id=getattr(msg, "id", f"msg_{len(messages)}"),
                    type=msg.type if hasattr(msg, "type") else "unknown",
                    content=msg.content if hasattr(msg, "content") else str(msg),
                    timestamp=current_time,
                )
            )

        # Log summary with key metrics
        total_duration = (time.time() - total_start) * 1000

        # Get model name from model_override ID
        model_display = "default"
        if model_override:
            try:
                from open_notebook.domain.models import Model
                model_obj = await Model.get(model_override)
                if model_obj:
                    model_display = f"{model_override} ({model_obj.name})"
            except Exception:
                model_display = model_override  # Fallback to ID if lookup fails

        logger.info(
            f"[CHAT] session={request.session_id} | "
            f"model={model_display} | "
            f"total={total_duration:.0f}ms | "
            f"llm={llm_duration:.0f}ms | "
            f"db={db_duration:.0f}ms | "
            f"sources={sources_count} | "
            f"notes={notes_count} | "
            f"msg={request.message[:50]}"
        )

        return ExecuteChatResponse(session_id=request.session_id, messages=messages)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error executing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing chat: {str(e)}")


@router.post("/chat/context", response_model=BuildContextResponse)
async def build_context(request: BuildContextRequest):
    """
    Build context for a notebook based on context configuration.

    根據上下文配置為筆記本建立對話上下文。

    - **notebook_id**: 筆記本 ID
    - **query**: 查詢字串（用於檢索相關內容）
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(request.notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        context_data: dict[str, list[dict[str, str]]] = {"sources": [], "notes": []}
        total_content = ""

        # Process context configuration if provided
        if request.context_config:
            # Process sources
            sources_config = request.context_config.get("sources", {})

            for source_id, status in sources_config.items():
                if "not in" in status:
                    continue

                try:
                    # Add table prefix if not present
                    full_source_id = (
                        source_id
                        if source_id.startswith("source:")
                        else f"source:{source_id}"
                    )

                    try:
                        source = await Source.get(full_source_id)
                    except Exception:
                        continue

                    if "insights" in status:
                        source_context = await source.get_context(context_size="short")
                        context_data["sources"].append(source_context)
                        total_content += str(source_context)
                    elif "full content" in status:
                        source_context = await source.get_context(context_size="long")
                        context_data["sources"].append(source_context)
                        total_content += str(source_context)
                except Exception as e:
                    logger.warning(f"Error processing source {source_id}: {str(e)}")
                    continue

            # Process notes
            for note_id, status in request.context_config.get("notes", {}).items():
                if "not in" in status:
                    continue

                try:
                    # Add table prefix if not present
                    full_note_id = (
                        note_id if note_id.startswith("note:") else f"note:{note_id}"
                    )
                    note = await Note.get(full_note_id)
                    if not note:
                        continue

                    if "full content" in status:
                        note_context = note.get_context(context_size="long")
                        context_data["notes"].append(note_context)
                        total_content += str(note_context)
                except Exception as e:
                    logger.warning(f"Error processing note {note_id}: {str(e)}")
                    continue
        else:
            # Default behavior - include all sources and notes with short context
            sources = await notebook.get_sources()
            for source in sources:
                try:
                    source_context = await source.get_context(context_size="short")
                    context_data["sources"].append(source_context)
                    total_content += str(source_context)
                except Exception as e:
                    logger.warning(f"Error processing source {source.id}: {str(e)}")
                    continue

            notes = await notebook.get_notes()
            for note in notes:
                try:
                    note_context = note.get_context(context_size="short")
                    context_data["notes"].append(note_context)
                    total_content += str(note_context)
                except Exception as e:
                    logger.warning(f"Error processing note {note.id}: {str(e)}")
                    continue

        # Calculate character and token counts
        char_count = len(total_content)
        # Use token count utility if available
        try:
            from open_notebook.utils import token_count

            estimated_tokens = token_count(total_content) if total_content else 0
        except ImportError:
            # Fallback to simple estimation
            estimated_tokens = char_count // 4

        return BuildContextResponse(
            context=context_data, token_count=estimated_tokens, char_count=char_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error building context: {str(e)}")
