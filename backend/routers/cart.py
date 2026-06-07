from fastapi import APIRouter, Depends, HTTPException

from ..core.security import get_current_user
from ..database import dcur, get_db
from ..schemas.cart import CartItemAdd, CartItemUpdate, CartOut

router = APIRouter()


def _get_cart(user_id: int) -> dict:
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute(
                """
                SELECT
                    cart_items.id,
                    cart_items.product_id,
                    cart_items.quantity,
                    products.name,
                    products.price,
                    products.image_url,
                    ROUND((products.price * cart_items.quantity)::NUMERIC, 2) AS subtotal
                FROM cart_items
                JOIN products ON products.id = cart_items.product_id
                WHERE cart_items.user_id = %s
                ORDER BY cart_items.id DESC
                """,
                (user_id,),
            )
            items = [dict(row) for row in cur.fetchall()]
    for item in items:
        item["subtotal"] = float(item["subtotal"])
    total = round(sum(item["subtotal"] for item in items), 2)
    return {"items": items, "total": total}


@router.get("", response_model=CartOut)
def get_cart(user: dict = Depends(get_current_user)):
    return _get_cart(user["id"])


@router.post("", response_model=CartOut, status_code=201)
def add_to_cart(body: CartItemAdd, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE id = %s", (body.product_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Product not found")
            cur.execute(
                """
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                """,
                (user["id"], body.product_id, body.quantity),
            )
    return _get_cart(user["id"])


@router.put("/{product_id}", response_model=CartOut)
def update_cart_item(product_id: int, body: CartItemUpdate, user: dict = Depends(get_current_user)):
    if body.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE cart_items SET quantity = %s WHERE user_id = %s AND product_id = %s",
                (body.quantity, user["id"], product_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cart item not found")
    return _get_cart(user["id"])


@router.delete("/{product_id}", response_model=CartOut)
def remove_from_cart(product_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s",
                (user["id"], product_id),
            )
    return _get_cart(user["id"])
