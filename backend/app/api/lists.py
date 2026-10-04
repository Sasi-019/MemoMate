from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.list import SmartList, SmartListItem
from app.models.user import User


router = APIRouter(
    prefix="/lists",
    tags=["Smart Lists"],
)


class ListCreate(BaseModel):
    name: str


class ListResponse(BaseModel):
    id: int
    name: str
    created_at: str

    class Config:
        from_attributes = True


class ListItemCreate(BaseModel):
    text: str


class ListItemResponse(BaseModel):
    id: int
    list_id: int
    text: str
    completed: bool

    class Config:
        from_attributes = True


def get_owned_list(
    list_id: int,
    user_id: int,
    db: Session,
):
    smart_list = (
        db.query(SmartList)
        .filter(
            SmartList.id == list_id,
            SmartList.user_id == user_id,
        )
        .first()
    )

    if smart_list is None:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    return smart_list


@router.get("", response_model=List[ListResponse])
def get_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(SmartList)
        .filter(SmartList.user_id == current_user.id)
        .order_by(SmartList.id.desc())
        .all()
    )


@router.post("", response_model=ListResponse)
def create_list(
    request: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="List name is required",
        )

    existing = (
        db.query(SmartList)
        .filter(
            SmartList.user_id == current_user.id,
            SmartList.name.ilike(name),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A list with this name already exists",
        )

    from datetime import datetime

    smart_list = SmartList(
        user_id=current_user.id,
        name=name,
        created_at=datetime.utcnow().isoformat(),
    )

    db.add(smart_list)
    db.commit()
    db.refresh(smart_list)

    return smart_list


@router.get("/{list_id}", response_model=ListResponse)
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_list(
        list_id,
        current_user.id,
        db,
    )


@router.delete("/{list_id}")
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    smart_list = get_owned_list(
        list_id,
        current_user.id,
        db,
    )

    db.query(SmartListItem).filter(
        SmartListItem.list_id == smart_list.id
    ).delete(synchronize_session=False)

    db.delete(smart_list)
    db.commit()

    return {
        "message": "List deleted successfully",
    }


@router.get(
    "/{list_id}/items",
    response_model=List[ListItemResponse],
)
def get_list_items(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    smart_list = get_owned_list(
        list_id,
        current_user.id,
        db,
    )

    return (
        db.query(SmartListItem)
        .filter(SmartListItem.list_id == smart_list.id)
        .order_by(SmartListItem.id.asc())
        .all()
    )


@router.post(
    "/{list_id}/items",
    response_model=ListItemResponse,
)
def add_list_item(
    list_id: int,
    request: ListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    smart_list = get_owned_list(
        list_id,
        current_user.id,
        db,
    )

    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Item text is required",
        )

    item = SmartListItem(
        list_id=smart_list.id,
        text=text,
        completed=False,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.put(
    "/items/{item_id}/complete",
    response_model=ListItemResponse,
)
def complete_list_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(SmartListItem)
        .join(
            SmartList,
            SmartList.id == SmartListItem.list_id,
        )
        .filter(
            SmartListItem.id == item_id,
            SmartList.user_id == current_user.id,
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="List item not found",
        )

    item.completed = True
    db.commit()
    db.refresh(item)

    return item


@router.delete("/items/{item_id}")
def delete_list_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(SmartListItem)
        .join(
            SmartList,
            SmartList.id == SmartListItem.list_id,
        )
        .filter(
            SmartListItem.id == item_id,
            SmartList.user_id == current_user.id,
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="List item not found",
        )

    db.delete(item)
    db.commit()

    return {
        "message": "List item deleted successfully",
    }
