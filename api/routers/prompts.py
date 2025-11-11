from typing import List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.domain.notebook import Notebook, SystemPrompt
from open_notebook.exceptions import NotFoundError

router = APIRouter()


# Request/Response models
class CreatePromptRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID")
    name: str = Field(..., description="Prompt name")
    content: str = Field(..., description="Prompt content")


class UpdatePromptRequest(BaseModel):
    name: Optional[str] = Field(None, description="Prompt name")
    content: Optional[str] = Field(None, description="Prompt content")


class PromptResponse(BaseModel):
    id: str = Field(..., description="Prompt ID")
    name: str = Field(..., description="Prompt name")
    content: str = Field(..., description="Prompt content")
    created: str = Field(..., description="Creation timestamp")
    updated: str = Field(..., description="Last update timestamp")


class SetActivePromptRequest(BaseModel):
    prompt_id: Optional[str] = Field(None, description="Prompt ID (null to unset)")


@router.get("/notebooks/{notebook_id}/prompts", response_model=List[PromptResponse])
async def get_notebook_prompts(notebook_id: str):
    """
    Get all prompts for a notebook.

    獲取筆記本的所有 prompt。

    - **notebook_id**: 筆記本 ID
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Get all prompts
        prompts = await notebook.get_prompts()

        return [
            PromptResponse(
                id=prompt.id or "",
                name=prompt.name,
                content=prompt.content,
                created=str(prompt.created),
                updated=str(prompt.updated),
            )
            for prompt in prompts
        ]
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Notebook not found")
    except Exception as e:
        logger.error(f"Error fetching prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching prompts: {str(e)}")


@router.post("/notebooks/{notebook_id}/prompts", response_model=PromptResponse)
async def create_prompt(notebook_id: str, request: CreatePromptRequest):
    """
    Create a new prompt for a notebook.

    為筆記本建立新的 prompt。

    - **notebook_id**: 筆記本 ID
    - **name**: Prompt 名稱
    - **content**: Prompt 內容
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(request.notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Create prompt
        prompt = SystemPrompt(name=request.name, content=request.content)
        await prompt.save()

        # Relate to notebook
        await prompt.relate_to_notebook(request.notebook_id)

        return PromptResponse(
            id=prompt.id or "",
            name=prompt.name,
            content=prompt.content,
            created=str(prompt.created),
            updated=str(prompt.updated),
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Notebook not found")
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating prompt: {str(e)}")


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """
    Get a specific prompt.

    獲取特定的 prompt。

    - **prompt_id**: Prompt ID
    """
    try:
        # Ensure prompt_id has proper table prefix
        full_prompt_id = (
            prompt_id
            if prompt_id.startswith("system_prompt:")
            else f"system_prompt:{prompt_id}"
        )
        prompt = await SystemPrompt.get(full_prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        return PromptResponse(
            id=prompt.id or "",
            name=prompt.name,
            content=prompt.content,
            created=str(prompt.created),
            updated=str(prompt.updated),
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Prompt not found")
    except Exception as e:
        logger.error(f"Error fetching prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching prompt: {str(e)}")


@router.put("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: str, request: UpdatePromptRequest):
    """
    Update a prompt.

    更新 prompt。

    - **prompt_id**: Prompt ID
    - **name**: 新的名稱（選填）
    - **content**: 新的內容（選填）
    """
    try:
        # Ensure prompt_id has proper table prefix
        full_prompt_id = (
            prompt_id
            if prompt_id.startswith("system_prompt:")
            else f"system_prompt:{prompt_id}"
        )
        prompt = await SystemPrompt.get(full_prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        if "name" in update_data:
            prompt.name = update_data["name"]
        if "content" in update_data:
            prompt.content = update_data["content"]

        await prompt.save()

        return PromptResponse(
            id=prompt.id or "",
            name=prompt.name,
            content=prompt.content,
            created=str(prompt.created),
            updated=str(prompt.updated),
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Prompt not found")
    except Exception as e:
        logger.error(f"Error updating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating prompt: {str(e)}")


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """
    Delete a prompt.

    刪除 prompt。

    - **prompt_id**: Prompt ID
    """
    try:
        # Ensure prompt_id has proper table prefix
        full_prompt_id = (
            prompt_id
            if prompt_id.startswith("system_prompt:")
            else f"system_prompt:{prompt_id}"
        )
        prompt = await SystemPrompt.get(full_prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        await prompt.delete()

        return {"message": "Prompt deleted successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Prompt not found")
    except Exception as e:
        logger.error(f"Error deleting prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting prompt: {str(e)}")


@router.put("/notebooks/{notebook_id}/active-prompt")
async def set_active_prompt(notebook_id: str, request: SetActivePromptRequest):
    """
    Set the active prompt for a notebook.

    設定筆記本的啟用 prompt。

    - **notebook_id**: 筆記本 ID
    - **prompt_id**: Prompt ID（null 表示取消設定）
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # If setting a prompt, verify it exists
        if request.prompt_id:
            full_prompt_id = (
                request.prompt_id
                if request.prompt_id.startswith("system_prompt:")
                else f"system_prompt:{request.prompt_id}"
            )
            prompt = await SystemPrompt.get(full_prompt_id)
            if not prompt:
                raise HTTPException(status_code=404, detail="Prompt not found")

            await notebook.set_active_prompt(full_prompt_id)
        else:
            await notebook.set_active_prompt(None)

        # Reload notebook to get updated active_prompt_id
        notebook = await Notebook.get(notebook_id)
        return {"message": "Active prompt updated successfully", "active_prompt_id": notebook.active_prompt_id}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting active prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting active prompt: {str(e)}")


@router.get("/notebooks/{notebook_id}/active-prompt", response_model=Optional[PromptResponse])
async def get_active_prompt(notebook_id: str):
    """
    Get the active prompt for a notebook.

    獲取筆記本的啟用 prompt。

    - **notebook_id**: 筆記本 ID
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Get active prompt - handle case where prompt was deleted
        try:
            prompt = await notebook.get_active_prompt()
            if not prompt:
                return None
        except Exception as e:
            logger.error(f"Error fetching active prompt for notebook {notebook_id}: {str(e)}")
            # If active_prompt_id points to non-existent prompt, clear it
            if notebook.active_prompt_id:
                logger.info(f"Clearing invalid active_prompt_id {notebook.active_prompt_id} for notebook {notebook_id}")
                await notebook.set_active_prompt(None)
            return None

        return PromptResponse(
            id=prompt.id or "",
            name=prompt.name,
            content=prompt.content,
            created=str(prompt.created),
            updated=str(prompt.updated),
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Notebook not found")
    except Exception as e:
        logger.error(f"Error fetching active prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching active prompt: {str(e)}")
