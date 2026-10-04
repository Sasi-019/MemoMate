from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.list import SmartList, SmartListItem
from app.models.user import User


router = APIRouter(
    prefix="/lists",
    tags=["Smart Lists"],
)


# ============================================================
# SCHEMAS
# ============================================================

class ListItemResponse(BaseModel):
    id: int
    list_id: int
    text: str
    completed: bool

    class Config:
        from_attributes = True


class ListResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    # Include items inside the list response
    items: List[ListItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ListCreate(BaseModel):
    name: str


class ListItemCreate(BaseModel):
    text: str


# ============================================================
# HELPER
# ============================================================

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

    if not smart_list:
        raise HTTPException(
            status_code=404,
            detail="List not found.",
        )

    return smart_list


# ============================================================
# GET ALL LISTS
# ============================================================

@router.get("", response_model=List[ListResponse])
def get_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lists = (
        db.query(SmartList)
        .filter(
            SmartList.user_id == current_user.id
        )
        .order_by(
            SmartList.id.desc()
        )
        .all()
    )

    return lists


# ============================================================
# CREATE LIST
# ============================================================

@router.post("", response_model=ListResponse)
def create_list(
    payload: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="List name cannot be empty.",
        )

    # Check duplicate list
    existing = (
        db.query(SmartList)
        .filter(
            SmartList.user_id == current_user.id,
            SmartList.name == name,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A list with this name already exists.",
        )

    smart_list = SmartList(
        user_id=current_user.id,
        name=name,
        created_at=datetime.utcnow(),
    )

    db.add(smart_list)
    db.commit()
    db.refresh(smart_list)

    return smart_list


# ============================================================
# GET SINGLE LIST
# ============================================================

@router.get(
    "/{list_id}",
    response_model=ListResponse,
)
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    smart_list = get_owned_list(
        list_id=list_id,
        user_id=current_user.id,
        db=db,
    )

    return smart_list


# ============================================================
# DELETE LIST
# ============================================================

@router.delete("/{list_id}")
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    smart_list = get_owned_list(
        list_id=list_id,
        user_id=current_user.id,
        db=db,
    )

    db.delete(smart_list)
    db.commit()

    return {
        "message": "List deleted successfully.",
        "list_id": list_id,
    }


# ============================================================
# GET ITEMS OF A LIST
# ============================================================

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
        list_id=list_id,
        user_id=current_user.id,
        db=db,
    )

    return (
        db.query(SmartListItem)
        .filter(
            SmartListItem.list_id == smart_list.id
        )
        .order_by(
            SmartListItem.id.asc()
        )
        .all()
    )


# ============================================================
# ADD ITEM TO LIST
# ============================================================

@router.post(
    "/{list_id}/items",
    response_model=ListItemResponse,
)
def add_list_item(
    list_id: int,
    payload: ListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    smart_list = get_owned_list(
        list_id=list_id,
        user_id=current_user.id,
        db=db,
    )

    text = payload.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Item text cannot be empty.",
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


# ============================================================
# COMPLETE / UNCOMPLETE ITEM
# ============================================================

@router.put(
    "/items/{item_id}/complete",
    response_model=ListItemResponse,
)
def complete_item(
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

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found.",
        )

    item.completed = not item.completed

    db.commit()
    db.refresh(item)

    return item


# ============================================================
# DELETE ITEM
# ============================================================

@router.delete("/items/{item_id}")
def delete_item(
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

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found.",
        )

    db.delete(item)
    db.commit()

    return {
        "message": "Item deleted successfully.",
        "item_id": item_id,
    }