from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from surreal_commands import registry

from api.command_service import CommandService

router = APIRouter()

class CommandExecutionRequest(BaseModel):
    command: str = Field(..., description="Command function name (e.g., 'process_text')")
    app: str = Field(..., description="Application name (e.g., 'open_notebook')")
    input: Dict[str, Any] = Field(..., description="Arguments to pass to the command")

class CommandJobResponse(BaseModel):
    job_id: str
    status: str
    message: str

class CommandJobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None

@router.post("/commands/jobs", response_model=CommandJobResponse)
async def execute_command(request: CommandExecutionRequest):
    """
    Submit a command for background processing.
    Returns immediately with job ID for status tracking.

    提交指令進行背景處理。
    立即返回任務 ID 以供狀態追蹤。

    Example request:
    {
        "command": "process_text",
        "app": "open_notebook",
        "input": {
            "text": "Hello world",
            "operation": "uppercase"
        }
    }

    - **command**: 指令函數名稱（例如：'process_text'）
    - **app**: 應用程式名稱（例如：'open_notebook'）
    - **input**: 傳遞給指令的參數
    """
    try:
        # Submit command using app name (not module name)
        job_id = await CommandService.submit_command_job(
            module_name=request.app,  # This should be "open_notebook"
            command_name=request.command,
            command_args=request.input
        )
        
        return CommandJobResponse(
            job_id=job_id,
            status="submitted",
            message=f"Command '{request.command}' submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting command: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit command: {str(e)}"
        )

@router.get("/commands/jobs/{job_id}", response_model=CommandJobStatusResponse)
async def get_command_job_status(job_id: str):
    """
    Get the status of a specific command job.

    獲取特定指令任務的狀態。

    - **job_id**: 任務的唯一識別碼
    """
    try:
        status_data = await CommandService.get_command_status(job_id)
        return CommandJobStatusResponse(**status_data)
        
    except Exception as e:
        logger.error(f"Error fetching job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch job status: {str(e)}"
        )

@router.get("/commands/jobs", response_model=List[Dict[str, Any]])
async def list_command_jobs(
    command_filter: Optional[str] = Query(None, description="Filter by command name | 依指令名稱篩選"),
    status_filter: Optional[str] = Query(None, description="Filter by status | 依狀態篩選"),
    limit: int = Query(50, description="Maximum number of jobs to return | 返回的任務數量上限")
):
    """
    List command jobs with optional filtering.

    列出指令任務，可選擇性篩選。

    - **command_filter**: 依指令名稱篩選（選填）
    - **status_filter**: 依狀態篩選（選填）
    - **limit**: 返回的任務數量上限（預設 50）
    """
    try:
        jobs = await CommandService.list_command_jobs(
            command_filter=command_filter,
            status_filter=status_filter,
            limit=limit
        )
        return jobs
        
    except Exception as e:
        logger.error(f"Error listing command jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list command jobs: {str(e)}"
        )

@router.delete("/commands/jobs/{job_id}")
async def cancel_command_job(job_id: str):
    """
    Cancel a running command job.

    取消執行中的指令任務。

    - **job_id**: 要取消的任務 ID
    """
    try:
        success = await CommandService.cancel_command_job(job_id)
        return {"job_id": job_id, "cancelled": success}
        
    except Exception as e:
        logger.error(f"Error cancelling command job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel command job: {str(e)}"
        )

@router.get("/commands/registry/debug")
async def debug_registry():
    """
    Debug endpoint to see what commands are registered.

    除錯端點，查看已註冊的指令清單。

    返回所有已註冊的指令及其所屬應用程式的詳細資訊。
    """
    try:
        # Get all registered commands
        all_items = registry.get_all_commands()
        
        # Create JSON-serializable data
        command_items = []
        for item in all_items:
            try:
                command_items.append({
                    "app_id": item.app_id,
                    "name": item.name,
                    "full_id": f"{item.app_id}.{item.name}"
                })
            except Exception as item_error:
                logger.error(f"Error processing item: {item_error}")
        
        # Get the basic command structure
        try:
            commands_dict: dict[str, list[str]] = {}
            for item in all_items:
                if item.app_id not in commands_dict:
                    commands_dict[item.app_id] = []
                commands_dict[item.app_id].append(item.name)
        except Exception:
            commands_dict = {}
        
        return {
            "total_commands": len(all_items),
            "commands_by_app": commands_dict,
            "command_items": command_items
        }
        
    except Exception as e:
        logger.error(f"Error debugging registry: {str(e)}")
        return {
            "error": str(e),
            "total_commands": 0,
            "commands_by_app": {},
            "command_items": []
        }