import requests
import re
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
import os

books = []

# Scrape first 5 pages
for page in range(1, 6):

    url = f"https://books.toscrape.com//catalogue/page-{page}.html"

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("article", class_="product_pod"):

        title = a.h3.a["title"]

        price_text = a.find("p", class_="price_color").text

        rating_word = a.find(
            "p",
            class_="star-rating"
        )["class"][1]

        avail_text = a.find(
            "p",
            class_="instock"
        ).text.strip()

        books.append({
            "title": title,
            "price_gbp": float(re.sub(r"[^0-9.]", "", price_text)),
            "rating": {
                "One": 1,
                "Two": 2,
                "Three": 3,
                "Four": 4,
                "Five": 5
            }[rating_word],
            "in_stock": 1 if "In stock" in avail_text else 0,
            "category": "All"
        })

# Create DataFrame
df = pd.DataFrame(books)

# GBP to INR conversion
FIXED_RATE = 105.50
df["price_inr"] = df["price_gbp"] * FIXED_RATE

# Create directory if missing
os.makedirs("data_pipeline", exist_ok=True)

# Create database
conn = sqlite3.connect("data_pipeline/books.db")

# Create tables
conn.execute("""
CREATE TABLE IF NOT EXISTS categories(
    category_id INTEGER PRIMARY KEY,
    category_name TEXT UNIQUE
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS books(
    book_id INTEGER PRIMARY KEY,
    title TEXT,
    price_gbp REAL,
    price_inr REAL,
    rating INTEGER,
    in_stock INTEGER,
    category_id INTEGER,
    FOREIGN KEY(category_id)
        REFERENCES categories(category_id)
)
""")

# Insert categories and books
for cat in df["category"].unique():

    conn.execute(
        "INSERT OR IGNORE INTO categories(category_name) VALUES(?)",
        (cat,)
    )

    cat_id = conn.execute(
        "SELECT category_id FROM categories WHERE category_name=?",
        (cat,)
    ).fetchone()[0]

    for _, r in df[df["category"] == cat].iterrows():

        conn.execute(
            """
            INSERT INTO books
            (title, price_gbp, price_inr,
             rating, in_stock, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                r["title"],
                r["price_gbp"],
                r["price_inr"],
                r["rating"],
                r["in_stock"],
                cat_id
            )
        )

# Save changes
conn.commit()

# Analytics query
q1 = pd.read_sql(
    """
    SELECT
        c.category_name,
        AVG(b.price_inr) AS avg_price
    FROM books b
    JOIN categories c
        ON b.category_id = c.category_id
    GROUP BY c.category_name
    """,
    conn
)

print("Done -", len(df), "books, DB created")
print(q1)

conn.close()