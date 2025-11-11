from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from api.models import NotebookCreate, NotebookResponse, NotebookUpdate
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import Notebook, Source
from open_notebook.exceptions import InvalidInputError

router = APIRouter()


@router.get("/notebooks", response_model=List[NotebookResponse])
async def get_notebooks(
    archived: Optional[bool] = Query(None, description="Filter by archived status | 依封存狀態篩選"),
    order_by: str = Query("updated desc", description="Order by field and direction | 排序欄位和方向"),
):
    """
    Get all notebooks with optional filtering and ordering.

    獲取所有筆記本，支援篩選和排序。

    - **archived**: 篩選封存狀態 (true/false/null)
    - **order_by**: 排序方式，例如 "updated desc" 或 "created asc"
    """
    try:
        # Build the query with counts
        query = f"""
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM notebook
            ORDER BY {order_by}
        """

        result = await repo_query(query)

        # Filter by archived status if specified
        if archived is not None:
            result = [nb for nb in result if nb.get("archived") == archived]

        return [
            NotebookResponse(
                id=str(nb.get("id", "")),
                name=nb.get("name", ""),
                description=nb.get("description", ""),
                archived=nb.get("archived", False),
                created=str(nb.get("created", "")),
                updated=str(nb.get("updated", "")),
                source_count=nb.get("source_count", 0),
                note_count=nb.get("note_count", 0),
                custom_system_prompt=nb.get("custom_system_prompt"),
                active_prompt_id=nb.get("active_prompt_id"),
            )
            for nb in result
        ]
    except Exception as e:
        logger.error(f"Error fetching notebooks: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching notebooks: {str(e)}"
        )


@router.post("/notebooks", response_model=NotebookResponse)
async def create_notebook(notebook: NotebookCreate):
    """
    Create a new notebook.

    創建新的筆記本。

    - **name**: 筆記本名稱（必填）
    - **description**: 筆記本描述（選填）
    """
    try:
        new_notebook = Notebook(
            name=notebook.name,
            description=notebook.description,
            custom_system_prompt=notebook.custom_system_prompt,
        )
        await new_notebook.save()

        return NotebookResponse(
            id=new_notebook.id or "",
            name=new_notebook.name,
            description=new_notebook.description,
            archived=new_notebook.archived or False,
            created=str(new_notebook.created),
            updated=str(new_notebook.updated),
            source_count=0,  # New notebook has no sources
            note_count=0,  # New notebook has no notes
            custom_system_prompt=new_notebook.custom_system_prompt,
        )
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating notebook: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating notebook: {str(e)}"
        )


@router.get("/notebooks/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(notebook_id: str):
    """
    Get a specific notebook by ID.

    根據 ID 獲取特定筆記本的詳細資訊。

    - **notebook_id**: 筆記本的唯一識別碼
    """
    try:
        # Query with counts for single notebook
        query = """
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM $notebook_id
        """
        result = await repo_query(query, {"notebook_id": ensure_record_id(notebook_id)})

        if not result:
            raise HTTPException(status_code=404, detail="Notebook not found")

        nb = result[0]
        return NotebookResponse(
            id=str(nb.get("id", "")),
            name=nb.get("name", ""),
            description=nb.get("description", ""),
            archived=nb.get("archived", False),
            created=str(nb.get("created", "")),
            updated=str(nb.get("updated", "")),
            source_count=nb.get("source_count", 0),
            note_count=nb.get("note_count", 0),
            custom_system_prompt=nb.get("custom_system_prompt"),
            active_prompt_id=nb.get("active_prompt_id"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching notebook: {str(e)}"
        )


@router.put("/notebooks/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(notebook_id: str, notebook_update: NotebookUpdate):
    """
    Update a notebook.

    更新筆記本資訊。

    - **notebook_id**: 筆記本的唯一識別碼
    - **name**: 新的筆記本名稱（選填）
    - **description**: 新的筆記本描述（選填）
    - **archived**: 封存狀態（選填）
    """
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Update only provided fields, allowing explicit null values
        update_data = notebook_update.model_dump(exclude_unset=True)

        if "name" in update_data:
            notebook.name = update_data["name"]
        if "description" in update_data:
            notebook.description = update_data["description"]
        if "archived" in update_data:
            notebook.archived = update_data["archived"]
        if "custom_system_prompt" in update_data:
            notebook.custom_system_prompt = update_data["custom_system_prompt"]

        await notebook.save()

        # Get counts separately to avoid issues with SELECT * and aggregation
        count_query = """
            SELECT
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM $notebook_id
        """
        count_result = await repo_query(count_query, {"notebook_id": ensure_record_id(notebook_id)})

        source_count = count_result[0].get("source_count", 0) if count_result else 0
        note_count = count_result[0].get("note_count", 0) if count_result else 0

        # Return the updated notebook object directly
        return NotebookResponse(
            id=notebook.id or "",
            name=notebook.name,
            description=notebook.description,
            archived=notebook.archived or False,
            created=str(notebook.created),
            updated=str(notebook.updated),
            source_count=source_count,
            note_count=note_count,
            custom_system_prompt=notebook.custom_system_prompt,
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating notebook: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/sources/{source_id}")
async def add_source_to_notebook(notebook_id: str, source_id: str):
    """
    Add an existing source to a notebook.

    將現有來源添加到筆記本中。

    - **notebook_id**: 筆記本的唯一識別碼
    - **source_id**: 來源的唯一識別碼
    """
    try:
        # Check if notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Check if source exists
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Check if reference already exists (idempotency)
        existing_ref = await repo_query(
            "SELECT * FROM reference WHERE out = $source_id AND in = $notebook_id",
            {
                "notebook_id": ensure_record_id(notebook_id),
                "source_id": ensure_record_id(source_id),
            },
        )

        # If reference doesn't exist, create it
        if not existing_ref:
            await repo_query(
                "RELATE $source_id->reference->$notebook_id",
                {
                    "notebook_id": ensure_record_id(notebook_id),
                    "source_id": ensure_record_id(source_id),
                },
            )

        return {"message": "Source linked to notebook successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error linking source {source_id} to notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error linking source to notebook: {str(e)}"
        )


@router.delete("/notebooks/{notebook_id}/sources/{source_id}")
async def remove_source_from_notebook(notebook_id: str, source_id: str):
    """
    Remove a source from a notebook.

    從筆記本中移除來源。

    - **notebook_id**: 筆記本的唯一識別碼
    - **source_id**: 來源的唯一識別碼
    """
    try:
        # Check if notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Delete the reference record linking source to notebook
        await repo_query(
            "DELETE FROM reference WHERE out = $notebook_id AND in = $source_id",
            {
                "notebook_id": ensure_record_id(notebook_id),
                "source_id": ensure_record_id(source_id),
            },
        )

        return {"message": "Source removed from notebook successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error removing source {source_id} from notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error removing source from notebook: {str(e)}"
        )


@router.delete("/notebooks/{notebook_id}")
async def delete_notebook(notebook_id: str):
    """
    Delete a notebook.

    刪除筆記本。

    - **notebook_id**: 要刪除的筆記本唯一識別碼
    """
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        await notebook.delete()

        return {"message": "Notebook deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting notebook: {str(e)}"
        )
