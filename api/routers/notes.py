from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from api.models import NoteCreate, NoteResponse, NoteUpdate
from open_notebook.domain.notebook import Note
from open_notebook.exceptions import InvalidInputError

router = APIRouter()


@router.get("/notes", response_model=List[NoteResponse])
async def get_notes(
    notebook_id: Optional[str] = Query(None, description="Filter by notebook ID | 依筆記本 ID 篩選")
):
    """
    Get all notes with optional notebook filtering.

    獲取所有筆記，可依筆記本篩選。

    - **notebook_id**: 篩選特定筆記本的筆記（選填）
    """
    try:
        if notebook_id:
            # Get notes for a specific notebook
            from open_notebook.domain.notebook import Notebook
            notebook = await Notebook.get(notebook_id)
            if not notebook:
                raise HTTPException(status_code=404, detail="Notebook not found")
            notes = await notebook.get_notes()
        else:
            # Get all notes
            notes = await Note.get_all(order_by="updated desc")
        
        return [
            NoteResponse(
                id=note.id or "",
                title=note.title,
                content=note.content,
                note_type=note.note_type,
                created=str(note.created),
                updated=str(note.updated),
            )
            for note in notes
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching notes: {str(e)}")


@router.post("/notes", response_model=NoteResponse)
async def create_note(note_data: NoteCreate):
    """
    Create a new note.

    創建新筆記。

    - **title**: 筆記標題（選填，AI 筆記會自動生成）
    - **content**: 筆記內容
    - **note_type**: 筆記類型（human 或 ai）
    - **notebook_id**: 要添加到的筆記本 ID（選填）
    """
    try:
        # Auto-generate title if not provided and it's an AI note
        title = note_data.title
        if not title and note_data.note_type == "ai" and note_data.content:
            from open_notebook.graphs.prompt import graph as prompt_graph
            prompt = "Based on the Note below, please provide a Title for this content, with max 15 words"
            result = await prompt_graph.ainvoke(
                {  # type: ignore[arg-type]
                    "input_text": note_data.content,
                    "prompt": prompt
                }
            )
            title = result.get("output", "Untitled Note")
        
        # Validate note_type
        note_type: Optional[Literal["human", "ai"]] = None
        if note_data.note_type in ("human", "ai"):
            note_type = note_data.note_type  # type: ignore[assignment]
        elif note_data.note_type is not None:
            raise HTTPException(status_code=400, detail="note_type must be 'human' or 'ai'")

        new_note = Note(
            title=title,
            content=note_data.content,
            note_type=note_type,
        )
        await new_note.save()
        
        # Add to notebook if specified
        if note_data.notebook_id:
            from open_notebook.domain.notebook import Notebook
            notebook = await Notebook.get(note_data.notebook_id)
            if not notebook:
                raise HTTPException(status_code=404, detail="Notebook not found")
            await new_note.add_to_notebook(note_data.notebook_id)
        
        return NoteResponse(
            id=new_note.id or "",
            title=new_note.title,
            content=new_note.content,
            note_type=new_note.note_type,
            created=str(new_note.created),
            updated=str(new_note.updated),
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating note: {str(e)}")


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    """
    Get a specific note by ID.

    根據 ID 獲取特定筆記。

    - **note_id**: 筆記的唯一識別碼
    """
    try:
        note = await Note.get(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return NoteResponse(
            id=note.id or "",
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            created=str(note.created),
            updated=str(note.updated),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching note: {str(e)}")


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, note_update: NoteUpdate):
    """
    Update a note.

    更新筆記。

    - **note_id**: 筆記的唯一識別碼
    - **title**: 新的筆記標題（選填）
    - **content**: 新的筆記內容（選填）
    - **note_type**: 新的筆記類型（選填，human 或 ai）
    """
    try:
        note = await Note.get(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # Update only provided fields
        if note_update.title is not None:
            note.title = note_update.title
        if note_update.content is not None:
            note.content = note_update.content
        if note_update.note_type is not None:
            if note_update.note_type in ("human", "ai"):
                note.note_type = note_update.note_type  # type: ignore[assignment]
            else:
                raise HTTPException(status_code=400, detail="note_type must be 'human' or 'ai'")

        await note.save()

        return NoteResponse(
            id=note.id or "",
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            created=str(note.created),
            updated=str(note.updated),
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating note: {str(e)}")


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """
    Delete a note.

    刪除筆記。

    - **note_id**: 要刪除的筆記唯一識別碼
    """
    try:
        note = await Note.get(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        await note.delete()
        
        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting note: {str(e)}")