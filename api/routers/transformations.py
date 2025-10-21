from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.models import (
    DefaultPromptResponse,
    DefaultPromptUpdate,
    TransformationCreate,
    TransformationExecuteRequest,
    TransformationExecuteResponse,
    TransformationResponse,
    TransformationUpdate,
)
from open_notebook.domain.models import Model
from open_notebook.domain.transformation import DefaultPrompts, Transformation
from open_notebook.exceptions import InvalidInputError
from open_notebook.graphs.transformation import graph as transformation_graph

router = APIRouter()


@router.get("/transformations", response_model=List[TransformationResponse])
async def get_transformations():
    """
    Get all transformations.

    獲取所有內容轉換模板。

    轉換模板用於對來源內容進行自動化處理，例如摘要、翻譯、重寫等。
    """
    try:
        transformations = await Transformation.get_all(order_by="name asc")

        return [
            TransformationResponse(
                id=transformation.id or "",
                name=transformation.name,
                title=transformation.title,
                description=transformation.description,
                prompt=transformation.prompt,
                apply_default=transformation.apply_default,
                created=str(transformation.created),
                updated=str(transformation.updated),
            )
            for transformation in transformations
        ]
    except Exception as e:
        logger.error(f"Error fetching transformations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching transformations: {str(e)}"
        )


@router.post("/transformations", response_model=TransformationResponse)
async def create_transformation(transformation_data: TransformationCreate):
    """
    Create a new transformation.

    創建新的內容轉換模板。

    - **name**: 轉換名稱（唯一識別碼）
    - **title**: 轉換標題
    - **description**: 轉換描述
    - **prompt**: 轉換提示詞（用於 AI 處理）
    - **apply_default**: 是否預設套用（選填）
    """
    try:
        new_transformation = Transformation(
            name=transformation_data.name,
            title=transformation_data.title,
            description=transformation_data.description,
            prompt=transformation_data.prompt,
            apply_default=transformation_data.apply_default,
        )
        await new_transformation.save()

        return TransformationResponse(
            id=new_transformation.id or "",
            name=new_transformation.name,
            title=new_transformation.title,
            description=new_transformation.description,
            prompt=new_transformation.prompt,
            apply_default=new_transformation.apply_default,
            created=str(new_transformation.created),
            updated=str(new_transformation.updated),
        )
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating transformation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating transformation: {str(e)}"
        )


@router.get(
    "/transformations/{transformation_id}", response_model=TransformationResponse
)
async def get_transformation(transformation_id: str):
    """
    Get a specific transformation by ID.

    根據 ID 獲取特定的轉換模板。

    - **transformation_id**: 轉換模板的唯一識別碼
    """
    try:
        transformation = await Transformation.get(transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        return TransformationResponse(
            id=transformation.id or "",
            name=transformation.name,
            title=transformation.title,
            description=transformation.description,
            prompt=transformation.prompt,
            apply_default=transformation.apply_default,
            created=str(transformation.created),
            updated=str(transformation.updated),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transformation {transformation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching transformation: {str(e)}"
        )


@router.put(
    "/transformations/{transformation_id}", response_model=TransformationResponse
)
async def update_transformation(
    transformation_id: str, transformation_update: TransformationUpdate
):
    """
    Update a transformation.

    更新轉換模板。

    - **transformation_id**: 轉換模板的唯一識別碼
    - **name**: 新的轉換名稱（選填）
    - **title**: 新的轉換標題（選填）
    - **description**: 新的轉換描述（選填）
    - **prompt**: 新的轉換提示詞（選填）
    - **apply_default**: 是否預設套用（選填）
    """
    try:
        transformation = await Transformation.get(transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        # Update only provided fields
        if transformation_update.name is not None:
            transformation.name = transformation_update.name
        if transformation_update.title is not None:
            transformation.title = transformation_update.title
        if transformation_update.description is not None:
            transformation.description = transformation_update.description
        if transformation_update.prompt is not None:
            transformation.prompt = transformation_update.prompt
        if transformation_update.apply_default is not None:
            transformation.apply_default = transformation_update.apply_default

        await transformation.save()

        return TransformationResponse(
            id=transformation.id or "",
            name=transformation.name,
            title=transformation.title,
            description=transformation.description,
            prompt=transformation.prompt,
            apply_default=transformation.apply_default,
            created=str(transformation.created),
            updated=str(transformation.updated),
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating transformation {transformation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating transformation: {str(e)}"
        )


@router.delete("/transformations/{transformation_id}")
async def delete_transformation(transformation_id: str):
    """
    Delete a transformation.

    刪除轉換模板。

    - **transformation_id**: 要刪除的轉換模板 ID
    """
    try:
        transformation = await Transformation.get(transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        await transformation.delete()

        return {"message": "Transformation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transformation {transformation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting transformation: {str(e)}"
        )


@router.post("/transformations/execute", response_model=TransformationExecuteResponse)
async def execute_transformation(execute_request: TransformationExecuteRequest):
    """
    Execute a transformation on input text.

    對輸入文字執行轉換。

    - **transformation_id**: 要使用的轉換模板 ID
    - **model_id**: 要使用的模型 ID
    - **input_text**: 要轉換的輸入文字
    """
    try:
        # Validate transformation exists
        transformation = await Transformation.get(execute_request.transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        # Validate model exists
        model = await Model.get(execute_request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Execute the transformation
        result = await transformation_graph.ainvoke(
            dict(  # type: ignore[arg-type]
                input_text=execute_request.input_text,
                transformation=transformation,
            ),
            config=dict(configurable={"model_id": execute_request.model_id}),
        )

        return TransformationExecuteResponse(
            output=result["output"],
            transformation_id=execute_request.transformation_id,
            model_id=execute_request.model_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing transformation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error executing transformation: {str(e)}"
        )


@router.get("/transformations/default-prompt", response_model=DefaultPromptResponse)
async def get_default_prompt():
    """
    Get the default transformation prompt.

    獲取預設的轉換提示詞。

    返回全域預設的轉換指令模板。
    """
    try:
        default_prompts: DefaultPrompts = await DefaultPrompts.get_instance()  # type: ignore[assignment]

        return DefaultPromptResponse(
            transformation_instructions=default_prompts.transformation_instructions or ""
        )
    except Exception as e:
        logger.error(f"Error fetching default prompt: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching default prompt: {str(e)}"
        )


@router.put("/transformations/default-prompt", response_model=DefaultPromptResponse)
async def update_default_prompt(prompt_update: DefaultPromptUpdate):
    """
    Update the default transformation prompt.

    更新預設的轉換提示詞。

    - **transformation_instructions**: 新的預設轉換指令
    """
    try:
        default_prompts: DefaultPrompts = await DefaultPrompts.get_instance()  # type: ignore[assignment]

        default_prompts.transformation_instructions = prompt_update.transformation_instructions
        await default_prompts.update()

        return DefaultPromptResponse(
            transformation_instructions=default_prompts.transformation_instructions
        )
    except Exception as e:
        logger.error(f"Error updating default prompt: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating default prompt: {str(e)}"
        )
