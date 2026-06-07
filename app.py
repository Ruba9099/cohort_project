import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


PORT = int(os.environ.get("PORT", "3000"))
DB_FILE = os.environ.get("DB_FILE", "data/store.db")


def get_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row else None


def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${password_hash}"


def check_password(password, stored_password):
    salt, password_hash = stored_password.split("$", 1)
    test_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return hmac.compare_digest(test_hash, password_hash)


def init_db():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                image_url TEXT,
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                UNIQUE(user_id, product_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                total REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
            );
            """
        )

        count = db.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        if count == 0:
            db.executemany(
                """
                INSERT INTO products (name, description, price, image_url, stock)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    ("Classic T-Shirt", "Comfortable cotton t-shirt for everyday use.", 15.99, "https://placehold.co/600x400?text=T-Shirt", 30),
                    ("Running Shoes", "Lightweight shoes made for daily walking and running.", 49.99, "https://placehold.co/600x400?text=Shoes", 12),
                    ("Backpack", "Durable backpack with multiple storage sections.", 34.50, "https://placehold.co/600x400?text=Backpack", 20),
                ],
            )


class StoreAPI(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
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
        with get_db() as db:
            return db.execute(
                """
                SELECT users.id, users.name, users.email
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()

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
            with get_db() as db:
                products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
            return self.send_json([row_to_dict(product) for product in products])

        if path.startswith("/api/products/"):
            product_id = path.split("/")[-1]
            with get_db() as db:
                product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
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
            with get_db() as db:
                orders = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
            return self.send_json([row_to_dict(order) for order in orders])

        if path.startswith("/api/orders/"):
            user = self.require_user()
            if not user:
                return
            order_id = path.split("/")[-1]
            with get_db() as db:
                order = db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user["id"])).fetchone()
                if not order:
                    return self.send_json({"message": "Order not found"}, 404)
                items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
            data = row_to_dict(order)
            data["items"] = [row_to_dict(item) for item in items]
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
                with get_db() as db:
                    cursor = db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, hash_password(password)),
                    )
                    token = create_session(db, cursor.lastrowid)
                return self.send_json({"token": token, "user": {"id": cursor.lastrowid, "name": name, "email": email}}, 201)
            except sqlite3.IntegrityError:
                return self.send_json({"message": "Email already registered"}, 409)

        if path == "/api/auth/login":
            email = data.get("email", "").lower()
            password = data.get("password", "")
            with get_db() as db:
                user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
                if not user or not check_password(password, user["password_hash"]):
                    return self.send_json({"message": "Invalid email or password"}, 401)
                token = create_session(db, user["id"])
            return self.send_json({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})

        if path == "/api/auth/logout":
            token = self.headers.get("Authorization", "").replace("Bearer ", "", 1)
            with get_db() as db:
                db.execute("DELETE FROM sessions WHERE token = ?", (token,))
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
            with get_db() as db:
                result = db.execute(
                    "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
                    (quantity, user["id"], product_id),
                )
                if result.rowcount == 0:
                    return self.send_json({"message": "Cart item not found"}, 404)
            return self.send_json(get_cart(user["id"]))

        return self.send_json({"message": "Route not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path

        if path.startswith("/api/products/"):
            product_id = path.split("/")[-1]
            with get_db() as db:
                result = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
                if result.rowcount == 0:
                    return self.send_json({"message": "Product not found"}, 404)
            return self.send_json({"message": "Product deleted"})

        if path.startswith("/api/cart/"):
            user = self.require_user()
            if not user:
                return
            product_id = path.split("/")[-1]
            with get_db() as db:
                db.execute("DELETE FROM cart_items WHERE user_id = ? AND product_id = ?", (user["id"], product_id))
            return self.send_json(get_cart(user["id"]))

        return self.send_json({"message": "Route not found"}, 404)

    def create_product(self, data):
        required = ["name", "description", "price"]
        if any(not data.get(field) for field in required):
            return self.send_json({"message": "Name, description, and price are required"}, 400)
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO products (name, description, price, image_url, stock) VALUES (?, ?, ?, ?, ?)",
                (
                    data["name"],
                    data["description"],
                    float(data["price"]),
                    data.get("image_url"),
                    int(data.get("stock", 0)),
                ),
            )
            product = db.execute("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self.send_json(row_to_dict(product), 201)

    def update_product(self, product_id, data):
        with get_db() as db:
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not product:
                return self.send_json({"message": "Product not found"}, 404)
            updated = {
                "name": data.get("name", product["name"]),
                "description": data.get("description", product["description"]),
                "price": float(data.get("price", product["price"])),
                "image_url": data.get("image_url", product["image_url"]),
                "stock": int(data.get("stock", product["stock"])),
            }
            db.execute(
                """
                UPDATE products
                SET name = ?, description = ?, price = ?, image_url = ?, stock = ?
                WHERE id = ?
                """,
                (updated["name"], updated["description"], updated["price"], updated["image_url"], updated["stock"], product_id),
            )
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return self.send_json(row_to_dict(product))

    def add_to_cart(self, user_id, data):
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))
        if not product_id or quantity < 1:
            return self.send_json({"message": "Product ID and valid quantity are required"}, 400)
        with get_db() as db:
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not product:
                return self.send_json({"message": "Product not found"}, 404)
            db.execute(
                """
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, product_id)
                DO UPDATE SET quantity = quantity + excluded.quantity
                """,
                (user_id, product_id, quantity),
            )
        return self.send_json(get_cart(user_id), 201)

    def checkout(self, user_id, data):
        customer_name = data.get("customer_name")
        address = data.get("address")
        phone = data.get("phone")
        if not customer_name or not address or not phone:
            return self.send_json({"message": "Customer name, address, and phone are required"}, 400)

        with get_db() as db:
            cart_items = db.execute(
                """
                SELECT cart_items.product_id, cart_items.quantity, products.name, products.price
                FROM cart_items
                JOIN products ON products.id = cart_items.product_id
                WHERE cart_items.user_id = ?
                """,
                (user_id,),
            ).fetchall()
            if not cart_items:
                return self.send_json({"message": "Cart is empty"}, 400)

            total = round(sum(item["price"] * item["quantity"] for item in cart_items), 2)
            cursor = db.execute(
                "INSERT INTO orders (user_id, customer_name, address, phone, total) VALUES (?, ?, ?, ?, ?)",
                (user_id, customer_name, address, phone, total),
            )
            order_id = cursor.lastrowid
            db.executemany(
                """
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(order_id, item["product_id"], item["name"], item["price"], item["quantity"]) for item in cart_items],
            )
            db.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

        return self.send_json({"message": "Order placed successfully", "order_id": order_id, "total": total}, 201)


def create_session(db, user_id):
    token = secrets.token_hex(32)
    db.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    return token


def get_cart(user_id):
    with get_db() as db:
        items = db.execute(
            """
            SELECT
                cart_items.id,
                cart_items.product_id,
                cart_items.quantity,
                products.name,
                products.price,
                products.image_url,
                ROUND(products.price * cart_items.quantity, 2) AS subtotal
            FROM cart_items
            JOIN products ON products.id = cart_items.product_id
            WHERE cart_items.user_id = ?
            ORDER BY cart_items.id DESC
            """,
            (user_id,),
        ).fetchall()
    cart_items = [row_to_dict(item) for item in items]
    total = round(sum(item["subtotal"] for item in cart_items), 2)
    return {"items": cart_items, "total": total}


if __name__ == "__main__":
    init_db()
    server = HTTPServer(("localhost", PORT), StoreAPI)
    print(f"API running at http://localhost:{PORT}")
    server.serve_forever()
