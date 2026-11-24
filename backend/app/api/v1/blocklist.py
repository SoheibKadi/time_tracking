import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, BlocklistItem

router = APIRouter(prefix="/blocklist", tags=["blocklist"])


class BlocklistItemOut(BaseModel):
    id: uuid.UUID
    pattern: str

    model_config = {"from_attributes": True}


class BlocklistItemCreate(BaseModel):
    pattern: str


@router.get("", response_model=List[BlocklistItemOut])
def list_items(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(BlocklistItem).filter(BlocklistItem.user_id == user.id).all()


@router.post("", response_model=BlocklistItemOut, status_code=201)
def add_item(body: BlocklistItemCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = BlocklistItem(user_id=user.id, pattern=body.pattern.strip())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(BlocklistItem).filter(BlocklistItem.id == item_id, BlocklistItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
