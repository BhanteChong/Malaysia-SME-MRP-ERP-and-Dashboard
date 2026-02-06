import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

def init_database():
    conn = sqlite3.connect('sme_data.db', check_same_thread=False)
    c = conn.cursor()
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER, category TEXT)''')
    
    # Sales table
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY, product_id INTEGER, quantity INTEGER, 
                  total REAL, sale_date TEXT)''')
    
    # Check if demo data exists
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        load_demo_data(conn, 'retail')
    
    conn.commit()
    return conn

def load_demo_data(conn, industry):
    c = conn.cursor()
    c.execute("DELETE FROM products")
    c.execute("DELETE FROM sales")
    
    if industry == 'retail':
        products = [
            ('Nasi Lemak Set', 12.50, 100, 'Makanan'),
            ('Teh Tarik', 4.50, 200, 'Minuman'),
            ('Roti Canai', 3.00, 150, 'Makanan'),
            ('Milo Ais', 5.00, 180, 'Minuman'),
            ('Nasi Goreng', 10.00, 120, 'Makanan'),
            ('Kopi O', 3.50, 200, 'Minuman'),
            ('Mee Goreng', 9.00, 100, 'Makanan'),
            ('Air Sirap', 3.00, 150, 'Minuman'),
        ]
    elif industry == 'manufacturing':
        products = [
            ('PCB Board A1', 45.00, 500, 'Electronics'),
            ('Plastic Casing M2', 12.00, 1000, 'Parts'),
            ('LED Module X5', 28.00, 750, 'Electronics'),
            ('Rubber Seal R3', 5.50, 2000, 'Parts'),
            ('Motor Unit P7', 120.00, 200, 'Assembly'),
            ('Wire Harness W2', 35.00, 400, 'Electronics'),
            ('Metal Bracket B4', 18.00, 600, 'Parts'),
            ('Sensor Module S1', 85.00, 300, 'Electronics'),
        ]
    else:  # consulting
        products = [
            ('Business Review (2hr)', 500.00, 50, 'Consulting'),
            ('Tax Filing Service', 350.00, 100, 'Accounting'),
            ('HR Setup Package', 1200.00, 30, 'HR'),
            ('IT Audit Basic', 800.00, 40, 'IT'),
            ('Legal Review', 450.00, 60, 'Legal'),
            ('Marketing Strategy', 900.00, 35, 'Marketing'),
            ('Training Workshop', 650.00, 45, 'Training'),
            ('Compliance Check', 400.00, 55, 'Accounting'),
        ]
    
    c.executemany("INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)", products)
    
    # Generate 30 days of sales
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        num_sales = random.randint(5, 15)
        for _ in range(num_sales):
            prod_id = random.randint(1, len(products))
            qty = random.randint(1, 5)
            price = products[prod_id-1][1]
            c.execute("INSERT INTO sales (product_id, quantity, total, sale_date) VALUES (?, ?, ?, ?)",
                     (prod_id, qty, price * qty, date))
    
    conn.commit()

def get_products(conn):
    return pd.read_sql("SELECT * FROM products", conn)

def get_sales(conn):
    return pd.read_sql("""
        SELECT s.*, p.name, p.category 
        FROM sales s 
        JOIN products p ON s.product_id = p.id
    """, conn)

def add_sale(conn, product_id, quantity, total):
    c = conn.cursor()
    c.execute("INSERT INTO sales (product_id, quantity, total, sale_date) VALUES (?, ?, ?, ?)",
             (product_id, quantity, total, datetime.now().strftime('%Y-%m-%d')))
    c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    conn.commit()
