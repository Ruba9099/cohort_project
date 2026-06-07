from typing import List

from fastapi import APIRouter, HTTPException

from ..database import dcur, get_db
from ..schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter()


@router.get("", response_model=List[ProductOut])
def list_products():
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("SELECT * FROM products ORDER BY id DESC")
            return [dict(row) for row in cur.fetchall()]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cur.fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product)


@router.post("", response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute(
                "INSERT INTO products (name, description, price, image_url, stock) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (body.name, body.description, body.price, body.image_url, body.stock),
            )
            product_id = cur.fetchone()["id"]
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            return dict(cur.fetchone())


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, body: ProductUpdate):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Product not found")
            updates = body.model_dump(exclude_unset=True)
            if updates:
                fields = ", ".join(f"{k} = %s" for k in updates)
                values = list(updates.values()) + [product_id]
                cur.execute(f"UPDATE products SET {fields} WHERE id = %s", values)
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            return dict(cur.fetchone())


@router.delete("/{product_id}")
def delete_product(product_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}
