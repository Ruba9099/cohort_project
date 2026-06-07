from typing import List, Optional

from pydantic import BaseModel


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    name: str
    price: float
    image_url: Optional[str] = None
    subtotal: float


class CartOut(BaseModel):
    items: List[CartItemOut]
    total: float
