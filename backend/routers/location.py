from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from database.session import get_db
from models.locker import Locker, Cell
from models.order import Order
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from pydantic import BaseModel
from auth.utils import get_current_user
from uuid import UUID
from enum import Enum



router = APIRouter(
    prefix="/location",
    tags=["location"],
    dependencies=[Depends(get_current_user)]
)



@router.get("/coordinate")
async def get_locate():
    return {
        "Message": "Here is the coordinate"
    }
