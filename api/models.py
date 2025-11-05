from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Notebook models
class NotebookCreate(BaseModel):
    name: str = Field(..., description="Name of the notebook | 筆記本名稱")
    description: str = Field(default="", description="Description of the notebook | 筆記本描述")
    custom_system_prompt: Optional[str] = Field(None, description="Custom system prompt for AI interactions | AI 對話的自訂系統提示詞")


class NotebookUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the notebook | 筆記本名稱")
    description: Optional[str] = Field(None, description="Description of the notebook | 筆記本描述")
    archived: Optional[bool] = Field(
        None, description="Whether the notebook is archived | 筆記本是否已封存"
    )
    custom_system_prompt: Optional[str] = Field(None, description="Custom system prompt for AI interactions | AI 對話的自訂系統提示詞")


class NotebookResponse(BaseModel):
    id: str
    name: str
    description: str
    archived: bool
    created: str
    updated: str
    source_count: int
    note_count: int
    custom_system_prompt: Optional[str] = Field(None, description="Custom system prompt for AI interactions in this notebook's chat sessions | 此筆記本聊天對話中 AI 互動的自訂系統提示詞")


# Search models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query | 搜尋查詢字串")
    type: Literal["text", "vector"] = Field("text", description="Search type | 搜尋類型")
    limit: int = Field(100, description="Maximum number of results | 最大回傳結果數", le=1000)
    search_sources: bool = Field(True, description="Include sources in search | 搜尋時是否包含來源")
    search_notes: bool = Field(True, description="Include notes in search | 搜尋時是否包含筆記")
    minimum_score: float = Field(
        0.2, description="Minimum score for vector search | 向量搜尋的最低分數", ge=0, le=1
    )


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results | 搜尋結果")
    total_count: int = Field(..., description="Total number of results | 結果總數")
    search_type: str = Field(..., description="Type of search performed | 執行的搜尋類型")


class AskRequest(BaseModel):
    question: str = Field(..., description="Question to ask the knowledge base | 要詢問知識庫的問題")
    strategy_model: str = Field(..., description="Model ID for query strategy | 查詢策略使用的模型 ID")
    answer_model: str = Field(..., description="Model ID for individual answers | 個別回答使用的模型 ID")
    final_answer_model: str = Field(..., description="Model ID for final answer | 最終答案使用的模型 ID")


class AskResponse(BaseModel):
    answer: str = Field(..., description="Final answer from the knowledge base | 知識庫提供的最終答案")
    question: str = Field(..., description="Original question | 原始問題")


# Models API models
class ModelCreate(BaseModel):
    name: str = Field(..., description="Model name (e.g., gpt-5-mini, claude, gemini) | 模型名稱（例如 gpt-5-mini、claude、gemini）")
    provider: str = Field(
        ..., description="Provider name (e.g., openai, anthropic, gemini) | 供應商名稱（例如 openai、anthropic、gemini）"
    )
    type: str = Field(
        ...,
        description="Model type (language, embedding, text_to_speech, speech_to_text) | 模型類型（language、embedding、text_to_speech、speech_to_text）",
    )


class ModelResponse(BaseModel):
    id: str
    name: str
    provider: str
    type: str
    created: str
    updated: str


class DefaultModelsResponse(BaseModel):
    default_chat_model: Optional[str] = None
    default_transformation_model: Optional[str] = None
    large_context_model: Optional[str] = None
    default_text_to_speech_model: Optional[str] = None
    default_speech_to_text_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    default_tools_model: Optional[str] = None


class ProviderAvailabilityResponse(BaseModel):
    available: List[str] = Field(..., description="List of available providers | 可用供應商清單")
    unavailable: List[str] = Field(..., description="List of unavailable providers | 不可用供應商清單")
    supported_types: Dict[str, List[str]] = Field(
        ..., description="Provider to supported model types mapping | 供應商與支援模型類型對應"
    )


# Transformations API models
class TransformationCreate(BaseModel):
    name: str = Field(..., description="Transformation name | 轉換名稱")
    title: str = Field(..., description="Display title for the transformation | 轉換顯示標題")
    description: str = Field(
        ..., description="Description of what this transformation does | 此轉換的用途說明"
    )
    prompt: str = Field(..., description="The transformation prompt | 轉換提示詞")
    apply_default: bool = Field(
        False, description="Whether to apply this transformation by default | 是否預設套用此轉換"
    )


class TransformationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Transformation name | 轉換名稱")
    title: Optional[str] = Field(
        None, description="Display title for the transformation | 轉換顯示標題"
    )
    description: Optional[str] = Field(
        None, description="Description of what this transformation does | 此轉換的用途說明"
    )
    prompt: Optional[str] = Field(None, description="The transformation prompt | 轉換提示詞")
    apply_default: Optional[bool] = Field(
        None, description="Whether to apply this transformation by default | 是否預設套用此轉換"
    )


class TransformationResponse(BaseModel):
    id: str
    name: str
    title: str
    description: str
    prompt: str
    apply_default: bool
    created: str
    updated: str


class TransformationExecuteRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transformation_id: str = Field(
        ..., description="ID of the transformation to execute | 要執行的轉換 ID"
    )
    input_text: str = Field(..., description="Text to transform | 要轉換的文字")
    model_id: str = Field(..., description="Model ID to use for the transformation | 轉換使用的模型 ID")


class TransformationExecuteResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    output: str = Field(..., description="Transformed text | 轉換後的文字")
    transformation_id: str = Field(..., description="ID of the transformation used | 使用的轉換 ID")
    model_id: str = Field(..., description="Model ID used | 已使用的模型 ID")


# Default Prompt API models
class DefaultPromptResponse(BaseModel):
    transformation_instructions: str = Field(
        ..., description="Default transformation instructions | 預設轉換指令"
    )


class DefaultPromptUpdate(BaseModel):
    transformation_instructions: str = Field(
        ..., description="Default transformation instructions | 預設轉換指令"
    )


# Notes API models
class NoteCreate(BaseModel):
    title: Optional[str] = Field(None, description="Note title | 筆記標題")
    content: str = Field(..., description="Note content | 筆記內容")
    note_type: Optional[str] = Field("human", description="Type of note (human, ai) | 筆記類型（human、ai）")
    notebook_id: Optional[str] = Field(
        None, description="Notebook ID to add the note to | 要新增筆記的筆記本 ID"
    )


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Note title | 筆記標題")
    content: Optional[str] = Field(None, description="Note content | 筆記內容")
    note_type: Optional[str] = Field(None, description="Type of note (human, ai) | 筆記類型（human、ai）")


class NoteResponse(BaseModel):
    id: str
    title: Optional[str]
    content: Optional[str]
    note_type: Optional[str]
    created: str
    updated: str


# Embedding API models
class EmbedRequest(BaseModel):
    item_id: str = Field(..., description="ID of the item to embed | 要嵌入項目的 ID")
    item_type: str = Field(..., description="Type of item (source, note) | 項目類型（source、note）")
    async_processing: bool = Field(
        False, description="Process asynchronously in background | 是否在背景進行非同步處理"
    )


class EmbedResponse(BaseModel):
    success: bool = Field(..., description="Whether embedding was successful | 是否嵌入成功")
    message: str = Field(..., description="Result message | 結果訊息")
    item_id: str = Field(..., description="ID of the item that was embedded | 已嵌入項目的 ID")
    item_type: str = Field(..., description="Type of item that was embedded | 已嵌入項目的類型")
    command_id: Optional[str] = Field(
        None, description="Command ID for async processing | 非同步處理的指令識別碼"
    )


# Rebuild request/response models
class RebuildRequest(BaseModel):
    mode: Literal["existing", "all"] = Field(
        ...,
        description="Rebuild mode: 'existing' only re-embeds items with embeddings, 'all' embeds everything | 重建模式：'existing' 只重新嵌入已有嵌入的項目，'all' 會嵌入所有項目",
    )
    include_sources: bool = Field(True, description="Include sources in rebuild | 重建時是否包含來源")
    include_notes: bool = Field(True, description="Include notes in rebuild | 重建時是否包含筆記")
    include_insights: bool = Field(True, description="Include insights in rebuild | 重建時是否包含洞察資料")


class RebuildResponse(BaseModel):
    command_id: str = Field(..., description="Command ID to track progress | 用於追蹤進度的指令識別碼")
    total_items: int = Field(..., description="Estimated number of items to process | 預估需要處理的項目數")
    message: str = Field(..., description="Status message | 狀態訊息")


class RebuildProgress(BaseModel):
    processed: int = Field(..., description="Number of items processed | 已處理的項目數")
    total: int = Field(..., description="Total items to process | 需處理的項目總數")
    percentage: float = Field(..., description="Progress percentage | 進度百分比")


class RebuildStats(BaseModel):
    sources: int = Field(0, description="Sources processed | 已處理的來源數")
    notes: int = Field(0, description="Notes processed | 已處理的筆記數")
    insights: int = Field(0, description="Insights processed | 已處理的洞察數")
    failed: int = Field(0, description="Failed items | 失敗項目數")


class RebuildStatusResponse(BaseModel):
    command_id: str = Field(..., description="Command ID | 指令識別碼")
    status: str = Field(..., description="Status: queued, running, completed, failed | 狀態：queued、running、completed、failed")
    progress: Optional[RebuildProgress] = None
    stats: Optional[RebuildStats] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


# Settings API models
class SettingsResponse(BaseModel):
    default_content_processing_engine_doc: Optional[str] = None
    default_content_processing_engine_url: Optional[str] = None
    default_embedding_option: Optional[str] = None
    auto_delete_files: Optional[str] = None
    youtube_preferred_languages: Optional[List[str]] = None


class SettingsUpdate(BaseModel):
    default_content_processing_engine_doc: Optional[str] = None
    default_content_processing_engine_url: Optional[str] = None
    default_embedding_option: Optional[str] = None
    auto_delete_files: Optional[str] = None
    youtube_preferred_languages: Optional[List[str]] = None


# Sources API models
class AssetModel(BaseModel):
    file_path: Optional[str] = None
    url: Optional[str] = None


class SourceCreate(BaseModel):
    # Backward compatibility: support old single notebook_id
    notebook_id: Optional[str] = Field(
        None, description="Notebook ID to add the source to (deprecated, use notebooks) | 要加入來源的筆記本 ID（已棄用，請改用 notebooks）"
    )
    # New multi-notebook support
    notebooks: Optional[List[str]] = Field(
        None, description="List of notebook IDs to add the source to | 要將來源加入的筆記本 ID 清單"
    )
    # Required fields
    type: str = Field(..., description="Source type: link, upload, or text | 來源類型：連結、上傳或純文字")
    url: Optional[str] = Field(None, description="URL for link type | 連結類型的 URL")
    file_path: Optional[str] = Field(None, description="File path for upload type | 上傳類型的檔案路徑")
    content: Optional[str] = Field(None, description="Text content for text type | 純文字類型的內容")
    title: Optional[str] = Field(None, description="Source title | 來源標題")
    transformations: Optional[List[str]] = Field(
        default_factory=list, description="Transformation IDs to apply | 要套用的轉換 ID"
    )
    embed: bool = Field(False, description="Whether to embed content for vector search | 是否將內容嵌入以供向量搜尋")
    delete_source: bool = Field(
        False, description="Whether to delete uploaded file after processing | 處理後是否刪除上傳檔案"
    )
    # New async processing support
    async_processing: bool = Field(
        False, description="Whether to process source asynchronously | 是否以非同步方式處理來源"
    )

    @model_validator(mode="after")
    def validate_notebook_fields(self):
        # Ensure only one of notebook_id or notebooks is provided
        if self.notebook_id is not None and self.notebooks is not None:
            raise ValueError(
                "Cannot specify both 'notebook_id' and 'notebooks'. Use 'notebooks' for multi-notebook support."
            )

        # Convert single notebook_id to notebooks array for internal processing
        if self.notebook_id is not None:
            self.notebooks = [self.notebook_id]
            # Keep notebook_id for backward compatibility in response

        # Set empty array if no notebooks specified (allow sources without notebooks)
        if self.notebooks is None:
            self.notebooks = []

        return self


class SourceUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Source title | 來源標題")
    topics: Optional[List[str]] = Field(None, description="Source topics | 來源主題")


class SourceResponse(BaseModel):
    id: str
    title: Optional[str]
    topics: Optional[List[str]]
    asset: Optional[AssetModel]
    full_text: Optional[str]
    embedded: bool
    embedded_chunks: int
    file_available: Optional[bool] = None
    created: str
    updated: str
    # New fields for async processing
    command_id: Optional[str] = None
    status: Optional[str] = None
    processing_info: Optional[Dict] = None
    # Notebook associations
    notebooks: Optional[List[str]] = None


class SourceListResponse(BaseModel):
    id: str
    title: Optional[str]
    topics: Optional[List[str]]
    asset: Optional[AssetModel]
    embedded: bool  # Boolean flag indicating if source has embeddings
    embedded_chunks: int  # Number of embedded chunks
    insights_count: int
    created: str
    updated: str
    file_available: Optional[bool] = None
    # Status fields for async processing
    command_id: Optional[str] = None
    status: Optional[str] = None
    processing_info: Optional[Dict[str, Any]] = None


# Context API models
class ContextConfig(BaseModel):
    sources: Dict[str, str] = Field(
        default_factory=dict, description="Source inclusion config {source_id: level} | 來源納入設定 {source_id: level}"
    )
    notes: Dict[str, str] = Field(
        default_factory=dict, description="Note inclusion config {note_id: level} | 筆記納入設定 {note_id: level}"
    )


class ContextRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID to get context for | 要取得上下文的筆記本 ID")
    context_config: Optional[ContextConfig] = Field(
        None, description="Context configuration | 上下文配置"
    )


class ContextResponse(BaseModel):
    notebook_id: str
    sources: List[Dict[str, Any]] = Field(..., description="Source context data | 來源上下文資料")
    notes: List[Dict[str, Any]] = Field(..., description="Note context data | 筆記上下文資料")
    total_tokens: Optional[int] = Field(None, description="Estimated token count | 預估 token 數")


# Insights API models
class SourceInsightResponse(BaseModel):
    id: str
    source_id: str
    insight_type: str
    content: str
    created: str
    updated: str


class SaveAsNoteRequest(BaseModel):
    notebook_id: Optional[str] = Field(None, description="Notebook ID to add note to | 要新增筆記的筆記本 ID")


class CreateSourceInsightRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transformation_id: str = Field(..., description="ID of transformation to apply | 要套用的轉換 ID")
    model_id: Optional[str] = Field(
        None, description="Model ID (uses default if not provided) | 模型 ID（未提供時使用預設值）"
    )


# Source status response
class SourceStatusResponse(BaseModel):
    status: Optional[str] = Field(None, description="Processing status | 處理狀態")
    message: str = Field(..., description="Descriptive message about the status | 狀態說明訊息")
    processing_info: Optional[Dict[str, Any]] = Field(
        None, description="Detailed processing information | 詳細處理資訊"
    )
    command_id: Optional[str] = Field(None, description="Command ID if available | 如有則提供的指令識別碼")


# Error response
class ErrorResponse(BaseModel):
    error: str
    message: str
