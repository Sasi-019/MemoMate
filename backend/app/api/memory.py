from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.memory import PersonalMemory
from app.models.user import User


router = APIRouter(
    prefix="/memory",
    tags=["Personal Memory"],
)


class MemoryCreate(BaseModel):
    title: str
    content: str


class MemoryResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: object

    class Config:
        from_attributes = True


@router.get("", response_model=List[MemoryResponse])
def get_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(PersonalMemory)
        .filter(PersonalMemory.user_id == current_user.id)
        .order_by(PersonalMemory.created_at.desc())
        .all()
    )


@router.post("", response_model=MemoryResponse)
def create_memory(
    request: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = request.title.strip()
    content = request.content.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Memory title is required",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Memory content is required",
        )

    memory = PersonalMemory(
        user_id=current_user.id,
        title=title,
        content=content,
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.id == memory_id,
            PersonalMemory.user_id == current_user.id,
        )
        .first()
    )

    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )

    return memory


@router.delete("/{memory_id}")
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.id == memory_id,
            PersonalMemory.user_id == current_user.id,
        )
        .first()
    )

    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )

    db.delete(memory)
    db.commit()

    return {
        "message": "Memory deleted successfully",
    }
