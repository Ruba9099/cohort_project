import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

U = "https://images.unsplash.com/photo-"
P = "?w=900&q=80&auto=format&fit=crop"

# (name, description, price, image_url, images[5+], category, stock)
_SEED = [
    ("Linen Oxford Shirt", "Breathable long-sleeve shirt with a relaxed premium fit.", 39.99,
     f"{U}1596755094514-f87e34085b2c{P}",
     [f"{U}1596755094514-f87e34085b2c{P}",
      f"{U}1602810318383-e386cc2a3ccf{P}",
      f"{U}1523398002811-999ca8dec234{P}",
      f"{U}1483985988355-763728e1935b{P}",
      f"{U}1536992266094-82847e1fd431{P}",
      f"{U}1558769132-cb1aea458c5e{P}"],
     "Apparel", 34),

    ("Everyday Cotton Tee", "Soft mid-weight cotton t-shirt built for repeat wear.", 18.5,
     f"{U}1521572163474-6864f9cf17ab{P}",
     [f"{U}1521572163474-6864f9cf17ab{P}",
      f"{U}1503342394128-c104d54dba01{P}",
      f"{U}1583743814966-8936f5b7be1a{P}",
      f"{U}1618354691551-44de113f016d{P}",
      f"{U}1576566588028-4147f3842f27{P}",
      f"{U}1434389677669-e08b4cac3105{P}"],
     "Apparel", 60),

    ("Slim Chino Pants", "Tapered stretch chinos for office days and weekends.", 54.0,
     f"{U}1473966968600-fa801b869a1a{P}",
     [f"{U}1473966968600-fa801b869a1a{P}",
      f"{U}1487222477894-8943e31ef7b2{P}",
      f"{U}1496747611176-843222e1e57c{P}",
      f"{U}1507679799987-c73779587ccf{P}",
      f"{U}1528459105426-b9548367069b{P}",
      f"{U}1594938298603-7d6a62ce2271{P}"],
     "Apparel", 27),

    ("Quilted Travel Jacket", "Lightweight quilted jacket with water-resistant finish.", 89.99,
     f"{U}1548883354-94bcfe321cbb{P}",
     [f"{U}1548883354-94bcfe321cbb{P}",
      f"{U}1541099649105-f69ad21f3246{P}",
      f"{U}1515886657613-9f3515b0c78f{P}",
      f"{U}1548126032-3c6c8d9bc4a6{P}",
      f"{U}1551028719-00167b16eac5{P}",
      f"{U}1591047139829-d91aecb6caea{P}"],
     "Apparel", 18),

    ("Performance Running Shoes", "Responsive road shoes with a breathable mesh upper.", 74.99,
     f"{U}1542291026-7eec264c27ff{P}",
     [f"{U}1542291026-7eec264c27ff{P}",
      f"{U}1511556532299-8f662fc26c06{P}",
      f"{U}1525966222134-fcfa99b8ae77{P}",
      f"{U}1491553895911-0055eca6402d{P}",
      f"{U}1539185441755-769473a23570{P}",
      f"{U}1606107557195-0e29a4b5b4aa{P}"],
     "Footwear", 25),

    ("Leather Court Sneakers", "Clean leather sneakers with cushioned all-day support.", 68.0,
     f"{U}1525966222134-fcfa99b8ae77{P}",
     [f"{U}1525966222134-fcfa99b8ae77{P}",
      f"{U}1549298916-b41d501d3772{P}",
      f"{U}1600185365483-26d7a4cc7519{P}",
      f"{U}1579338559194-a162d19bf842{P}",
      f"{U}1460353581641-37baddab0fa2{P}",
      f"{U}1595950653106-bdbce154a1c8{P}"],
     "Footwear", 31),

    ("Trail Runner Boots", "Rugged trail shoes with stable grip and reinforced toe.", 96.5,
     f"{U}1542838132-92c53300491e{P}",
     [f"{U}1542838132-92c53300491e{P}",
      f"{U}1562183241-b937e95585b6{P}",
      f"{U}1603808033192-082d6919d3e1{P}",
      f"{U}1608256246200-53e635b5b65f{P}",
      f"{U}1635108200427-db5df4a1e8bb{P}",
      f"{U}1441986300917-64674bd600d8{P}"],
     "Footwear", 16),

    ("Minimal Slide Sandals", "Easy slip-on sandals with contoured footbeds.", 28.0,
     f"{U}1603487742131-4160ec999306{P}",
     [f"{U}1603487742131-4160ec999306{P}",
      f"{U}1518049362265-d5b2a6249a35{P}",
      f"{U}1620385092463-6ab9f0d61dc5{P}",
      f"{U}1562157873-818bc0726f68{P}",
      f"{U}1543163521-1bf539c55dd2{P}",
      f"{U}1572635196237-14b3f281503f{P}"],
     "Footwear", 44),

    ("City Commuter Backpack", "Durable backpack with laptop storage and smart pockets.", 48.99,
     f"{U}1553062407-98eeb64c6a62{P}",
     [f"{U}1553062407-98eeb64c6a62{P}",
      f"{U}1590874103328-eac38a683ce7{P}",
      f"{U}1547949003-9792a18a2601{P}",
      f"{U}1578321272176-b7bbc0679853{P}",
      f"{U}1581605405669-fcdf81165afa{P}",
      f"{U}1491349174775-aaaefebe6a43{P}"],
     "Bags", 36),

    ("Canvas Weekend Duffel", "Roomy travel duffel with reinforced handles.", 59.0,
     f"{U}1594223274512-ad4803739b7c{P}",
     [f"{U}1594223274512-ad4803739b7c{P}",
      f"{U}1547949003-9792a18a2601{P}",
      f"{U}1512436991641-6745cdb1723f{P}",
      f"{U}1553062407-98eeb64c6a62{P}",
      f"{U}1499750310107-5fef28a66643{P}",
      f"{U}1565026168218-2e62f8ee3e5f{P}"],
     "Bags", 22),

    ("Compact Crossbody Bag", "Hands-free daily bag for essentials and travel.", 32.75,
     f"{U}1605733513549-de9b150bd70f{P}",
     [f"{U}1605733513549-de9b150bd70f{P}",
      f"{U}1590874103328-eac38a683ce7{P}",
      f"{U}1622560480605-d83c853bc5c3{P}",
      f"{U}1548036328-c9fa89d128fa{P}",
      f"{U}1566150905458-1bf1fc113f0d{P}",
      f"{U}1584917865442-de89df76afd3{P}"],
     "Bags", 41),

    ("Structured Leather Tote", "Polished tote with laptop sleeve and zip closure.", 82.0,
     f"{U}1590874103328-eac38a683ce7{P}",
     [f"{U}1590874103328-eac38a683ce7{P}",
      f"{U}1534375979027-0c0f2d9b5fbc{P}",
      f"{U}1551326992-4e3f2e8b8f10{P}",
      f"{U}1584917865442-de89df76afd3{P}",
      f"{U}1548036328-c9fa89d128fa{P}",
      f"{U}1566150905458-1bf1fc113f0d{P}"],
     "Bags", 19),

    ("Insulated Coffee Tumbler", "Leak-resistant stainless tumbler that keeps drinks hot.", 24.99,
     f"{U}1517256064527-09c73fc73e38{P}",
     [f"{U}1517256064527-09c73fc73e38{P}",
      f"{U}1547592180-85f173990554{P}",
      f"{U}1590080875518-0a9f6b1c6a0f{P}",
      f"{U}1610878180933-0a57f4e4a4d6{P}",
      f"{U}1509042239860-f550ce710b93{P}",
      f"{U}1544098485-2e2e2e85baa1{P}"],
     "Home", 70),

    ("Stoneware Dinner Set", "Four-piece matte stoneware set for everyday dining.", 46.0,
     f"{U}1610701596007-11502861dcfa{P}",
     [f"{U}1610701596007-11502861dcfa{P}",
      f"{U}1612196808214-b9a2f4f12b58{P}",
      f"{U}1505693416388-ac5ce068fe85{P}",
      f"{U}1559181567-c3190bac2438{P}",
      f"{U}1567620905732-2d1ec7ab7445{P}",
      f"{U}1490645935967-10de6ba17061{P}"],
     "Home", 24),

    ("Cotton Waffle Throw", "Textured throw blanket with a soft heavyweight hand.", 38.0,
     f"{U}1587563871167-1ee9c731aefb{P}",
     [f"{U}1587563871167-1ee9c731aefb{P}",
      f"{U}1505693416388-ac5ce068fe85{P}",
      f"{U}1513694203232-719a280e022f{P}",
      f"{U}1584100936595-c0654b55a2e6{P}",
      f"{U}1565557970-5f5b9e03c3cf{P}",
      f"{U}1543248939-4ef8a4699fba{P}"],
     "Home", 28),

    ("Walnut Desk Lamp", "Warm task lamp with dimmable LED and walnut base.", 64.99,
     f"{U}1507473885765-e6ed057f782c{P}",
     [f"{U}1507473885765-e6ed057f782c{P}",
      f"{U}1545239351-1141bd82e8a6{P}",
      f"{U}1555041469-a586c61ea9bc{P}",
      f"{U}1540931932077-0fd5af33d04d{P}",
      f"{U}1494438639946-1ebd1d20bf85{P}",
      f"{U}1484101402345-acaa9f58ea12{P}"],
     "Home", 14),

    ("Wireless Earbuds", "Compact earbuds with clear calls and charging case.", 79.99,
     f"{U}1606220945770-b5b6c2c55bf1{P}",
     [f"{U}1606220945770-b5b6c2c55bf1{P}",
      f"{U}1618384887929-16ec33fab9ef{P}",
      f"{U}1487215078519-e21cc028cb29{P}",
      f"{U}1518441318161-2f83a8b61fc6{P}",
      f"{U}1505740420928-5e560c06d30e{P}",
      f"{U}1572666276023-3c3b8aa08601{P}"],
     "Tech", 33),

    ("Portable Bluetooth Speaker", "Water-resistant speaker with rich 360-degree sound.", 58.0,
     f"{U}1608043152269-423dbba4e7e1{P}",
     [f"{U}1608043152269-423dbba4e7e1{P}",
      f"{U}1545239351-1141bd82e8a6{P}",
      f"{U}1587831990711-23ca6441447b{P}",
      f"{U}1547394765-185e1e68f34e{P}",
      f"{U}1611532736597-de2d4265fba3{P}",
      f"{U}1484704849700-f032f6d4d66f{P}"],
     "Tech", 21),

    ("MagSafe Desk Charger", "Fast magnetic charger with a weighted aluminum stand.", 42.5,
     f"{U}1615526675159-e248c3021d3f{P}",
     [f"{U}1615526675159-e248c3021d3f{P}",
      f"{U}1625842268584-8f3296236761{P}",
      f"{U}1556742502-ec7c0e9f34b1{P}",
      f"{U}1523275335684-37898b6baf30{P}",
      f"{U}1585771724684-38269d6639fd{P}",
      f"{U}1526256041504-5a09b46f7d71{P}"],
     "Tech", 46),

    ("Smart Fitness Band", "Slim tracker for workouts, sleep, and daily activity.", 69.0,
     f"{U}1576243345690-4e4b79b63288{P}",
     [f"{U}1576243345690-4e4b79b63288{P}",
      f"{U}1617043786394-f977fa12eddf{P}",
      f"{U}1518441318161-2f83a8b61fc6{P}",
      f"{U}1575311373937-040b8e1fd6b0{P}",
      f"{U}1510771463236-c9b7a46ee4b7{P}",
      f"{U}1485217988980-282686b876f2{P}"],
     "Tech", 29),

    ("Minimal Analog Watch", "Steel watch with clean dial and leather strap.", 118.0,
     f"{U}1523275335684-37898b6baf30{P}",
     [f"{U}1523275335684-37898b6baf30{P}",
      f"{U}1509944947351-0e2ca4f1f9a7{P}",
      f"{U}1490367532201-b9bc1dc483f6{P}",
      f"{U}1547996160-81dfa63595aa{P}",
      f"{U}1434493789847-2f02dc6ca35d{P}",
      f"{U}1508057198265-ab5a6a66b4db{P}"],
     "Accessories", 17),

    ("Polarized Sunglasses", "Light acetate sunglasses with polarized lenses.", 52.0,
     f"{U}1511499767150-a48a237f0083{P}",
     [f"{U}1511499767150-a48a237f0083{P}",
      f"{U}1504593811423-6dd665756598{P}",
      f"{U}1556306535-38febf6782e7{P}",
      f"{U}1473496169904-658ba7574b0d{P}",
      f"{U}1572635196237-14b3f281503f{P}",
      f"{U}1508296695146-257a814ea21a{P}"],
     "Accessories", 38),

    ("Braided Leather Belt", "Full-grain braided belt with brushed metal buckle.", 36.0,
     f"{U}1624222247344-550fb60583dc{P}",
     [f"{U}1624222247344-550fb60583dc{P}",
      f"{U}1618354691373-d851c5c3d5ab{P}",
      f"{U}1610652492500-ded49ceeb378{P}",
      f"{U}1584917865442-de89df76afd3{P}",
      f"{U}1589782182703-2aaa69037b5b{P}",
      f"{U}1553689741-371011b31afa{P}"],
     "Accessories", 26),

    ("Merino Rib Beanie", "Soft merino beanie for cold commutes and weekends.", 29.0,
     f"{U}1576871337622-98d48d1cf531{P}",
     [f"{U}1576871337622-98d48d1cf531{P}",
      f"{U}1509631179647-0177331693ae{P}",
      f"{U}1523398002811-999ca8dec234{P}",
      f"{U}1510598969022-c4c6c5d05769{P}",
      f"{U}1478369402113-1fd47c82f2c6{P}",
      f"{U}1467173572719-f14b9fb86e5f{P}"],
     "Accessories", 43),

    ("Hydration Day Bottle", "BPA-free bottle with carry loop and measurement marks.", 19.99,
     f"{U}1602143407151-7111542de6e8{P}",
     [f"{U}1602143407151-7111542de6e8{P}",
      f"{U}1556228829-8cd0466377be{P}",
      f"{U}1547592180-85f173990554{P}",
      f"{U}1517649763962-0c623066013b{P}",
      f"{U}1523362628745-0c100150b504{P}",
      f"{U}1504300257218-47b7fe2e2b90{P}"],
     "Wellness", 75),

    ("Cork Yoga Mat", "Non-slip cork mat with natural rubber base.", 44.99,
     f"{U}1599901860904-17e6ed7083a0{P}",
     [f"{U}1599901860904-17e6ed7083a0{P}",
      f"{U}1518611012118-696072aa579a{P}",
      f"{U}1506629905607-1f9b2f4a9f7a{P}",
      f"{U}1544367567-0f2fcb009e0b{P}",
      f"{U}1545389336-cf090fa0e47e{P}",
      f"{U}1574680096145-d05b474e2155{P}"],
     "Wellness", 20),

    ("Resistance Band Kit", "Five-band training kit with handles and door anchor.", 26.5,
     f"{U}1599058917212-d750089bc07e{P}",
     [f"{U}1599058917212-d750089bc07e{P}",
      f"{U}1517838277536-f5f99be501cd{P}",
      f"{U}1518611012118-696072aa579a{P}",
      f"{U}1506629905607-1f9b2f4a9f7a{P}",
      f"{U}1517836357463-d25dfeac3438{P}",
      f"{U}1571019613454-1cb2f99b2d8b{P}"],
     "Wellness", 55),

    ("Aromatherapy Diffuser", "Quiet ceramic diffuser with soft ambient light.", 35.0,
     f"{U}1608571423902-eed4a5ad8108{P}",
     [f"{U}1608571423902-eed4a5ad8108{P}",
      f"{U}1513694203232-719a280e022f{P}",
      f"{U}1524758631624-e2822e304c36{P}",
      f"{U}1505693416388-ac5ce068fe85{P}",
      f"{U}1541243784359-30f8e3cf8e18{P}",
      f"{U}1519331379826-f10be5486c6f{P}"],
     "Wellness", 32),

    ("Notebook Set", "Three lay-flat notebooks with dot grid pages.", 16.0,
     f"{U}1531346878377-a5be20888e57{P}",
     [f"{U}1531346878377-a5be20888e57{P}",
      f"{U}1512496015851-a90fb38ba796{P}",
      f"{U}1455390582262-044cdead277a{P}",
      f"{U}1516321318423-f06f85e504b3{P}",
      f"{U}1471107340929-a87cd0f5b5f3{P}",
      f"{U}1517842645736-4913f0aa1cdf{P}"],
     "Office", 80),

    ("Aluminum Laptop Stand", "Foldable stand for better posture and airflow.", 31.99,
     f"{U}1616628188508-8d17f384e605{P}",
     [f"{U}1616628188508-8d17f384e605{P}",
      f"{U}1498050108023-c5249f4df085{P}",
      f"{U}1488590528505-98d2b5aba04b{P}",
      f"{U}1516321318423-f06f85e504b3{P}",
      f"{U}1593642632559-0c6d3fc62b89{P}",
      f"{U}1547658719-da2b51169166{P}"],
     "Office", 40),
]

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
            count = cur.fetchone()[0]
            if count != len(_SEED):
                # Wrong product count (old placeholders or empty) — reseed from scratch
                cur.execute("TRUNCATE products RESTART IDENTITY CASCADE")
                psycopg2.extras.execute_batch(cur, """
                    INSERT INTO products (name, description, price, image_url, images, category, stock)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, _SEED)
            else:
                # Right count — just refresh images/category so no DB wipe is needed
                psycopg2.extras.execute_batch(cur, """
                    UPDATE products SET image_url = %s, images = %s, category = %s WHERE name = %s
                """, [(p[3], p[4], p[5], p[0]) for p in _SEED])

