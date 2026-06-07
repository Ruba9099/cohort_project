import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "store"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}


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
                    images TEXT[],
                    category TEXT,
                    stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS images TEXT[]")
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS category TEXT")
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
                    INSERT INTO products (name, description, price, image_url, images, category, stock)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    ("Linen Oxford Shirt", "Breathable long-sleeve shirt with a relaxed premium fit.", 39.99,
                     "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=900&q=80&auto=format&fit=crop"],
                     "Apparel", 34),
                    ("Everyday Cotton Tee", "Soft mid-weight cotton t-shirt built for repeat wear.", 18.5,
                     "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1503342394128-c104d54dba01?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1618354691551-44de113f016d?w=900&q=80&auto=format&fit=crop"],
                     "Apparel", 60),
                    ("Slim Chino Pants", "Tapered stretch chinos for office days and weekends.", 54.0,
                     "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=900&q=80&auto=format&fit=crop"],
                     "Apparel", 27),
                    ("Quilted Travel Jacket", "Lightweight quilted jacket with water-resistant finish.", 89.99,
                     "https://images.unsplash.com/photo-1548883354-94bcfe321cbb?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1548883354-94bcfe321cbb?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1548126032-3c6c8d9bc4a6?w=900&q=80&auto=format&fit=crop"],
                     "Apparel", 18),
                    ("Performance Running Shoes", "Responsive road shoes with a breathable mesh upper.", 74.99,
                     "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=900&q=80&auto=format&fit=crop"],
                     "Footwear", 25),
                    ("Leather Court Sneakers", "Clean leather sneakers with cushioned all-day support.", 68.0,
                     "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1579338559194-a162d19bf842?w=900&q=80&auto=format&fit=crop"],
                     "Footwear", 31),
                    ("Trail Runner Boots", "Rugged trail shoes with stable grip and reinforced toe.", 96.5,
                     "https://images.unsplash.com/photo-1542838132-92c53300491e?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1542838132-92c53300491e?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1562183241-b937e95585b6?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?w=900&q=80&auto=format&fit=crop"],
                     "Footwear", 16),
                    ("Minimal Slide Sandals", "Easy slip-on sandals with contoured footbeds.", 28.0,
                     "https://images.unsplash.com/photo-1603487742131-4160ec999306?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1603487742131-4160ec999306?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1518049362265-d5b2a6249a35?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1620385092463-6ab9f0d61dc5?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=900&q=80&auto=format&fit=crop"],
                     "Footwear", 44),
                    ("City Commuter Backpack", "Durable backpack with laptop storage and smart pockets.", 48.99,
                     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1547949003-9792a18a2601?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1578321272176-b7bbc0679853?w=900&q=80&auto=format&fit=crop"],
                     "Bags", 36),
                    ("Canvas Weekend Duffel", "Roomy travel duffel with reinforced handles.", 59.0,
                     "https://images.unsplash.com/photo-1594223274512-ad4803739b7c?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1594223274512-ad4803739b7c?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1547949003-9792a18a2601?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900&q=80&auto=format&fit=crop"],
                     "Bags", 22),
                    ("Compact Crossbody Bag", "Hands-free daily bag for essentials and travel.", 32.75,
                     "https://images.unsplash.com/photo-1605733513549-de9b150bd70f?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1605733513549-de9b150bd70f?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1547949003-9792a18a2601?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=900&q=80&auto=format&fit=crop"],
                     "Bags", 41),
                    ("Structured Leather Tote", "Polished tote with laptop sleeve and zip closure.", 82.0,
                     "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1534375979027-0c0f2d9b5fbc?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1551326992-4e3f2e8b8f10?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=900&q=80&auto=format&fit=crop"],
                     "Bags", 19),
                    ("Insulated Coffee Tumbler", "Leak-resistant stainless tumbler that keeps drinks hot.", 24.99,
                     "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1547592180-85f173990554?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1590080875518-0a9f6b1c6a0f?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1610878180933-0a57f4e4a4d6?w=900&q=80&auto=format&fit=crop"],
                     "Home", 70),
                    ("Stoneware Dinner Set", "Four-piece matte stoneware set for everyday dining.", 46.0,
                     "https://images.unsplash.com/photo-1610701596007-11502861dcfa?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1610701596007-11502861dcfa?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1612196808214-b9a2f4f12b58?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1610701596007-11502861dcfa?w=900&q=80&auto=format&fit=crop&sat=-20", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=900&q=80&auto=format&fit=crop"],
                     "Home", 24),
                    ("Cotton Waffle Throw", "Textured throw blanket with a soft heavyweight hand.", 38.0,
                     "https://images.unsplash.com/photo-1587563871167-1ee9c731aefb?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1587563871167-1ee9c731aefb?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=900&q=80&auto=format&fit=crop&sat=-10", "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=900&q=80&auto=format&fit=crop"],
                     "Home", 28),
                    ("Walnut Desk Lamp", "Warm task lamp with dimmable LED and walnut base.", 64.99,
                     "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=900&q=80&auto=format&fit=crop&sat=-35", "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=900&q=80&auto=format&fit=crop"],
                     "Home", 14),
                    ("Wireless Earbuds", "Compact earbuds with clear calls and charging case.", 79.99,
                     "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1487215078519-e21cc028cb29?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1518441318161-2f83a8b61fc6?w=900&q=80&auto=format&fit=crop"],
                     "Tech", 33),
                    ("Portable Bluetooth Speaker", "Water-resistant speaker with rich 360-degree sound.", 58.0,
                     "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1518441902117-f0cba5f1b5e0?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1587831990711-23ca6441447b?w=900&q=80&auto=format&fit=crop"],
                     "Tech", 21),
                    ("MagSafe Desk Charger", "Fast magnetic charger with a weighted aluminum stand.", 42.5,
                     "https://images.unsplash.com/photo-1615526675159-e248c3021d3f?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1615526675159-e248c3021d3f?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1625842268584-8f3296236761?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1556742502-ec7c0e9f34b1?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900&q=80&auto=format&fit=crop"],
                     "Tech", 46),
                    ("Smart Fitness Band", "Slim tracker for workouts, sleep, and daily activity.", 69.0,
                     "https://images.unsplash.com/photo-1576243345690-4e4b79b63288?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1576243345690-4e4b79b63288?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1617043786394-f977fa12eddf?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1617043786394-f977fa12eddf?w=900&q=80&auto=format&fit=crop&sat=-20", "https://images.unsplash.com/photo-1518441318161-2f83a8b61fc6?w=900&q=80&auto=format&fit=crop"],
                     "Tech", 29),
                    ("Minimal Analog Watch", "Steel watch with clean dial and leather strap.", 118.0,
                     "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1509944947351-0e2ca4f1f9a7?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1490367532201-b9bc1dc483f6?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1547996160-81dfa63595aa?w=900&q=80&auto=format&fit=crop"],
                     "Accessories", 17),
                    ("Polarized Sunglasses", "Light acetate sunglasses with polarized lenses.", 52.0,
                     "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1504593811423-6dd665756598?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1556306535-38febf6782e7?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=900&q=80&auto=format&fit=crop"],
                     "Accessories", 38),
                    ("Braided Leather Belt", "Full-grain braided belt with brushed metal buckle.", 36.0,
                     "https://images.unsplash.com/photo-1624222247344-550fb60583dc?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1624222247344-550fb60583dc?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1618354691373-d851c5c3d5ab?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1610652492500-ded49ceeb378?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=900&q=80&auto=format&fit=crop"],
                     "Accessories", 26),
                    ("Merino Rib Beanie", "Soft merino beanie for cold commutes and weekends.", 29.0,
                     "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1556306535-38febf6782e7?w=900&q=80&auto=format&fit=crop"],
                     "Accessories", 43),
                    ("Hydration Day Bottle", "BPA-free bottle with carry loop and measurement marks.", 19.99,
                     "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1556228829-8cd0466377be?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1547592180-85f173990554?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=900&q=80&auto=format&fit=crop"],
                     "Wellness", 75),
                    ("Cork Yoga Mat", "Non-slip cork mat with natural rubber base.", 44.99,
                     "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1506629905607-1f9b2f4a9f7a?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=900&q=80&auto=format&fit=crop&sat=-10"],
                     "Wellness", 20),
                    ("Resistance Band Kit", "Five-band training kit with handles and door anchor.", 26.5,
                     "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1506629905607-1f9b2f4a9f7a?w=900&q=80&auto=format&fit=crop"],
                     "Wellness", 55),
                    ("Aromatherapy Diffuser", "Quiet ceramic diffuser with soft ambient light.", 35.0,
                     "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=900&q=80&auto=format&fit=crop"],
                     "Wellness", 32),
                    ("Notebook Set", "Three lay-flat notebooks with dot grid pages.", 16.0,
                     "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=900&q=80&auto=format&fit=crop"],
                     "Office", 80),
                    ("Aluminum Laptop Stand", "Foldable stand for better posture and airflow.", 31.99,
                     "https://images.unsplash.com/photo-1616628188508-8d17f384e605?w=900&q=80&auto=format&fit=crop",
                     ["https://images.unsplash.com/photo-1616628188508-8d17f384e605?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=900&q=80&auto=format&fit=crop", "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=900&q=80&auto=format&fit=crop"],
                     "Office", 40),
                ])
