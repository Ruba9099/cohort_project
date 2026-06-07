from typing import List

import psycopg2.extras
from fastapi import APIRouter, Depends, HTTPException

from ..core.security import get_current_user
from ..database import dcur, get_db
from ..schemas.order import CheckoutRequest, CheckoutResponse, OrderDetailOut, OrderOut

router = APIRouter()


@router.post("/checkout", response_model=CheckoutResponse, status_code=201)
def checkout(body: CheckoutRequest, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute(
                """
                SELECT cart_items.product_id, cart_items.quantity, products.name, products.price
                FROM cart_items
                JOIN products ON products.id = cart_items.product_id
                WHERE cart_items.user_id = %s
                """,
                (user["id"],),
            )
            cart_items = [dict(row) for row in cur.fetchall()]

            if not cart_items:
                raise HTTPException(status_code=400, detail="Cart is empty")

            total = round(sum(item["price"] * item["quantity"] for item in cart_items), 2)

            cur.execute(
                "INSERT INTO orders (user_id, customer_name, address, phone, total) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user["id"], body.customer_name, body.address, body.phone, total),
            )
            order_id = cur.fetchone()["id"]

            psycopg2.extras.execute_batch(
                cur,
                """
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [(order_id, i["product_id"], i["name"], i["price"], i["quantity"]) for i in cart_items],
            )

            cur.execute("DELETE FROM cart_items WHERE user_id = %s", (user["id"],))

    return {"message": "Order placed successfully", "order_id": order_id, "total": total}


@router.get("", response_model=List[OrderOut])
def list_orders(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC", (user["id"],))
            return [dict(row) for row in cur.fetchall()]


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user["id"]))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            items = [dict(row) for row in cur.fetchall()]
    result = dict(order)
    result["items"] = items
    return result
