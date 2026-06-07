from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: Optional[str] = None
    stock: int = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: Optional[str] = None
    stock: int
    created_at: datetime
