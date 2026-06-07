import datetime
import decimal
import hashlib
import hmac
import json
import os
import secrets
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import psycopg2
import psycopg2.errors
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.environ.get("PORT", "3000"))
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "store"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def dcur(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def row_to_dict(row):
    return dict(row) if row else None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${pw_hash}"


def check_password(password: str, stored: str) -> bool:
    salt, pw_hash = stored.split("$", 1)
    test_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return hmac.compare_digest(test_hash, pw_hash)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price FLOAT NOT NULL CHECK(price >= 0),
                    image_url TEXT,
                    stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    UNIQUE(user_id, product_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    customer_name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    total FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    price FLOAT NOT NULL,
                    quantity INTEGER NOT NULL
                )
            """)

            cur.execute("SELECT COUNT(*) FROM products")
            if cur.fetchone()[0] == 0:
                psycopg2.extras.execute_batch(cur, """
                    INSERT INTO products (name, description, price, image_url, stock)
                    VALUES (%s, %s, %s, %s, %s)
                """, [
                    ("Classic T-Shirt", "Comfortable cotton t-shirt for everyday use.", 15.99, "https://placehold.co/600x400?text=T-Shirt", 30),
                    ("Running Shoes", "Lightweight shoes made for daily walking and running.", 49.99, "https://placehold.co/600x400?text=Shoes", 12),
                    ("Backpack", "Durable backpack with multiple storage sections.", 34.50, "https://placehold.co/600x400?text=Backpack", 20),
                ])


def create_session(conn, user_id: int) -> str:
    token = secrets.token_hex(32)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO sessions (token, user_id) VALUES (%s, %s)", (token, user_id))
    return token


def get_cart(user_id: int) -> dict:
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("""
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
            """, (user_id,))
            items = [row_to_dict(row) for row in cur.fetchall()]
    total = round(sum(float(item["subtotal"]) for item in items), 2)
    return {"items": items, "total": total}


class StoreAPI(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data, cls=JSONEncoder).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "", 1) if auth_header.startswith("Bearer ") else ""
        if not token:
            return None
        with get_db() as conn:
            with dcur(conn) as cur:
                cur.execute("""
                    SELECT users.id, users.name, users.email
                    FROM sessions
                    JOIN users ON users.id = sessions.user_id
                    WHERE sessions.token = %s
                """, (token,))
                return cur.fetchone()

    def require_user(self):
        user = self.auth_user()
        if not user:
            self.send_json({"message": "Login required"}, 401)
            return None
        return user

    def do_OPTIONS(self):
        self.send_json({})

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            return self.send_json({
                "message": "Simple E-Commerce Store API",
                "routes": ["/api/auth/signup", "/api/auth/login", "/api/products", "/api/cart", "/api/orders/checkout"],
            })

        if path == "/api/auth/profile":
            user = self.require_user()
            if not user:
                return
            return self.send_json(row_to_dict(user))

        if path == "/api/products":
            with get_db() as conn:
                with dcur(conn) as cur:
                    cur.execute("SELECT * FROM products ORDER BY id DESC")
                    products = [row_to_dict(row) for row in cur.fetchall()]
            return self.send_json(products)

        if path.startswith("/api/products/"):
            product_id = path.split("/")[-1]
            with get_db() as conn:
                with dcur(conn) as cur:
                    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                    product = cur.fetchone()
            if not product:
                return self.send_json({"message": "Product not found"}, 404)
            return self.send_json(row_to_dict(product))

        if path == "/api/cart":
            user = self.require_user()
            if not user:
                return
            return self.send_json(get_cart(user["id"]))

        if path == "/api/orders":
            user = self.require_user()
            if not user:
                return
            with get_db() as conn:
                with dcur(conn) as cur:
                    cur.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC", (user["id"],))
                    orders = [row_to_dict(row) for row in cur.fetchall()]
            return self.send_json(orders)

        if path.startswith("/api/orders/"):
            user = self.require_user()
            if not user:
                return
            order_id = path.split("/")[-1]
            with get_db() as conn:
                with dcur(conn) as cur:
                    cur.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user["id"]))
                    order = cur.fetchone()
                    if not order:
                        return self.send_json({"message": "Order not found"}, 404)
                    cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
                    items = [row_to_dict(row) for row in cur.fetchall()]
            data = row_to_dict(order)
            data["items"] = items
            return self.send_json(data)

        return self.send_json({"message": "Route not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.read_json()

        if path == "/api/auth/signup":
            name = data.get("name")
            email = data.get("email", "").lower()
            password = data.get("password")
            if not name or not email or not password:
                return self.send_json({"message": "Name, email, and password are required"}, 400)
            try:
                with get_db() as conn:
                    with dcur(conn) as cur:
                        cur.execute(
                            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                            (name, email, hash_password(password)),
                        )
                        user_id = cur.fetchone()["id"]
                        token = create_session(conn, user_id)
                return self.send_json({"token": token, "user": {"id": user_id, "name": name, "email": email}}, 201)
            except psycopg2.errors.UniqueViolation:
                return self.send_json({"message": "Email already registered"}, 409)

        if path == "/api/auth/login":
            email = data.get("email", "").lower()
            password = data.get("password", "")
            with get_db() as conn:
                with dcur(conn) as cur:
                    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                    user = cur.fetchone()
                    if not user or not check_password(password, user["password_hash"]):
                        return self.send_json({"message": "Invalid email or password"}, 401)
                    token = create_session(conn, user["id"])
            return self.send_json({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})

        if path == "/api/auth/logout":
            token = self.headers.get("Authorization", "").replace("Bearer ", "", 1)
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
            return self.send_json({"message": "Logged out"})

        if path == "/api/products":
            return self.create_product(data)

        if path == "/api/cart":
            user = self.require_user()
            if not user:
                return
            return self.add_to_cart(user["id"], data)

        if path == "/api/orders/checkout":
            user = self.require_user()
            if not user:
                return
            return self.checkout(user["id"], data)

        return self.send_json({"message": "Route not found"}, 404)

    def do_PUT(self):
        path = urlparse(self.path).path
        data = self.read_json()

        if path.startswith("/api/products/"):
            return self.update_product(path.split("/")[-1], data)

        if path.startswith("/api/cart/"):
            user = self.require_user()
            if not user:
                return
            product_id = path.split("/")[-1]
            quantity = int(data.get("quantity", 0))
            if quantity < 1:
                return self.send_json({"message": "Quantity must be at least 1"}, 400)
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE cart_items SET quantity = %s WHERE user_id = %s AND product_id = %s",
                        (quantity, user["id"], product_id),
                    )
                    if cur.rowcount == 0:
                        return self.send_json({"message": "Cart item not found"}, 404)
            return self.send_json(get_cart(user["id"]))

        return self.send_json({"message": "Route not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path

        if path.startswith("/api/products/"):
            product_id = path.split("/")[-1]
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
                    if cur.rowcount == 0:
                        return self.send_json({"message": "Product not found"}, 404)
            return self.send_json({"message": "Product deleted"})

        if path.startswith("/api/cart/"):
            user = self.require_user()
            if not user:
                return
            product_id = path.split("/")[-1]
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM cart_items WHERE user_id = %s AND product_id = %s", (user["id"], product_id))
            return self.send_json(get_cart(user["id"]))

        return self.send_json({"message": "Route not found"}, 404)

    def create_product(self, data):
        required = ["name", "description", "price"]
        if any(not data.get(field) for field in required):
            return self.send_json({"message": "Name, description, and price are required"}, 400)
        with get_db() as conn:
            with dcur(conn) as cur:
                cur.execute(
                    "INSERT INTO products (name, description, price, image_url, stock) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (data["name"], data["description"], float(data["price"]), data.get("image_url"), int(data.get("stock", 0))),
                )
                product_id = cur.fetchone()["id"]
                cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product = cur.fetchone()
        return self.send_json(row_to_dict(product), 201)

    def update_product(self, product_id, data):
        with get_db() as conn:
            with dcur(conn) as cur:
                cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product = cur.fetchone()
                if not product:
                    return self.send_json({"message": "Product not found"}, 404)
                updated = {
                    "name": data.get("name", product["name"]),
                    "description": data.get("description", product["description"]),
                    "price": float(data.get("price", product["price"])),
                    "image_url": data.get("image_url", product["image_url"]),
                    "stock": int(data.get("stock", product["stock"])),
                }
                cur.execute("""
                    UPDATE products
                    SET name = %s, description = %s, price = %s, image_url = %s, stock = %s
                    WHERE id = %s
                """, (updated["name"], updated["description"], updated["price"], updated["image_url"], updated["stock"], product_id))
                cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product = cur.fetchone()
        return self.send_json(row_to_dict(product))

    def add_to_cart(self, user_id, data):
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))
        if not product_id or quantity < 1:
            return self.send_json({"message": "Product ID and valid quantity are required"}, 400)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
                if not cur.fetchone():
                    return self.send_json({"message": "Product not found"}, 404)
                cur.execute("""
                    INSERT INTO cart_items (user_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, product_id)
                    DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                """, (user_id, product_id, quantity))
        return self.send_json(get_cart(user_id), 201)

    def checkout(self, user_id, data):
        customer_name = data.get("customer_name")
        address = data.get("address")
        phone = data.get("phone")
        if not customer_name or not address or not phone:
            return self.send_json({"message": "Customer name, address, and phone are required"}, 400)

        with get_db() as conn:
            with dcur(conn) as cur:
                cur.execute("""
                    SELECT cart_items.product_id, cart_items.quantity, products.name, products.price
                    FROM cart_items
                    JOIN products ON products.id = cart_items.product_id
                    WHERE cart_items.user_id = %s
                """, (user_id,))
                cart_items = [dict(row) for row in cur.fetchall()]

                if not cart_items:
                    return self.send_json({"message": "Cart is empty"}, 400)

                total = round(sum(item["price"] * item["quantity"] for item in cart_items), 2)

                cur.execute(
                    "INSERT INTO orders (user_id, customer_name, address, phone, total) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (user_id, customer_name, address, phone, total),
                )
                order_id = cur.fetchone()["id"]

                psycopg2.extras.execute_batch(cur, """
                    INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                    VALUES (%s, %s, %s, %s, %s)
                """, [(order_id, item["product_id"], item["name"], item["price"], item["quantity"]) for item in cart_items])

                cur.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))

        return self.send_json({"message": "Order placed successfully", "order_id": order_id, "total": total}, 201)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    init_db()
    server = HTTPServer(("localhost", PORT), StoreAPI)
    print(f"API running at http://localhost:{PORT}")
    server.serve_forever()
