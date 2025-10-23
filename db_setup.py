import sqlite3
import os
import random

DB_DIR = "db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, "app_data.sqlite")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER
)
""")

product_names = [
    "گوشی سامسونگ", "گوشی شیائومی", "گوشی اپل", "تبلت لنوو", "لپ‌تاپ ایسوس",
    "لپ‌تاپ لنوو", "تلویزیون ال‌جی", "تلویزیون سونی", "هدفون بی‌سیم", "ساعت هوشمند",
    "پاوربانک", "اسپیکر بلوتوثی", "کیبورد مکانیکی", "موس بی‌سیم", "هارد اکسترنال",
    "کارت حافظه", "دوربین دیجیتال", "مانیتور گیمینگ", "مودم همراه", "پروژکتور"
]

descriptions = [
    "دارای باتری قوی و صفحه‌نمایش AMOLED",
    "پشتیبانی از شارژ سریع ۶۵ وات",
    "حافظه داخلی بالا و دوربین باکیفیت",
    "مناسب برای کارهای روزمره و بازی‌های سبک",
    "دارای پردازنده پرقدرت و بدنه فلزی",
    "کیفیت صدای عالی و طراحی مدرن",
    "نمایشگر با رزولوشن بالا و رنگ‌های زنده",
    "سبک و قابل حمل با عمر باتری طولانی",
    "دارای گارانتی رسمی و خدمات پس از فروش",
]

products = []
for i in range(100):
    name = random.choice(product_names) + f" مدل {random.randint(100,999)}"
    description = random.choice(descriptions)
    price = random.randint(2_000_000, 80_000_000)
    products.append((name, description, price))

cur.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)

conn.commit()
conn.close()

print(f"✅ دیتابیس با {len(products)} محصول ساخته شد: {DB_PATH}")





