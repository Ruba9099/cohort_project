from datetime import datetime
from typing import List

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    customer_name: str
    address: str
    phone: str


class CheckoutResponse(BaseModel):
    message: str
    order_id: int
    total: float


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    quantity: int


class OrderOut(BaseModel):
    id: int
    user_id: int
    customer_name: str
    address: str
    phone: str
    total: float
    created_at: datetime


class OrderDetailOut(OrderOut):
    items: List[OrderItemOut]
