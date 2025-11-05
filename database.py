import psycopg2
from datetime import datetime
import psycopg2.extras
# connect to PostgreSQL

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="12199",
        dbname="myduka_db",
        cursor_factory=psycopg2.extras.RealDictCursor  # returns rows as dictionaries
    )


def fetch_data(table_name):
    conn = get_connection()
    curr = conn.cursor()
    curr.execute(f"SELECT * FROM {table_name}")
    data = curr.fetchall()
    curr.close()
    conn.close()
    return data


# PRODUCTS
products = fetch_data("products")
print(" PRODUCTS:")
print(products)

# STOCK
stock = fetch_data("stock")
print(" STOCK:")
print(stock)

# SALES
sales = fetch_data("sales")
print(" SALES:")
print(sales)


def insert_product(p_values):
    conn = get_connection()
    curr = conn.cursor()
    query = "INSERT INTO products(name, buying_price, selling_price) VALUES (%s, %s, %s);"
    curr.execute(query, p_values)
    conn.commit()
    curr.close()
    conn.close()


def insert_sales(values):
    conn = get_connection()
    curr = conn.cursor()
    query = 'INSERT INTO sales(pid, quantity, created_at) VALUES(%s, %s, NOW());'
    curr.execute(query, values)
    conn.commit()
    curr.close()
    conn.close()


def insert_stock(values):
    conn = get_connection()
    curr = conn.cursor()
    query = 'INSERT INTO stock(pid, stock_quantity) VALUES (%s, %s);'
    curr.execute(query, values)
    conn.commit()
    curr.close()
    conn.close()


def product_profit():
    conn = get_connection()
    curr = conn.cursor()
    query = '''
        SELECT p.name, p.id, SUM((p.selling_price - p.buying_price) * s.quantity) AS profit
        FROM sales AS s
        INNER JOIN products AS p ON s.pid = p.id
        GROUP BY p.name, p.id;
    '''
    curr.execute(query)
    profit = curr.fetchall()
    curr.close()
    conn.close()
    return profit


myprofits = product_profit()
print(f"My products profit: {myprofits}")


def product_sales():
    conn = get_connection()
    curr = conn.cursor()
    query = '''
        SELECT p.id, p.name, SUM(p.selling_price * s.quantity) AS total_sales
        FROM sales AS s
        JOIN products AS p ON s.pid = p.id
        GROUP BY p.id, p.name;
    '''
    curr.execute(query)
    sales = curr.fetchall()
    curr.close()
    conn.close()
    return sales


mysales = product_sales()
print(f"My products sales: {mysales}")


def delete_data(table, record_id):
    conn = get_connection()
    curr = conn.cursor()
    query = f'DELETE FROM {table} WHERE id = %s;'
    curr.execute(query, (record_id,))
    conn.commit()
    curr.close()
    conn.close()
    print(f"Record with id {record_id} deleted from {table} table.")


def fetch_products_for_dropdown():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products


def daily_sales():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(created_at) AS day,
               SUM(p.selling_price * s.quantity) AS total_sales
        FROM sales s
        JOIN products p ON s.pid = p.id
        GROUP BY day
        ORDER BY day;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data  # ✅ This must be present
# Secondary get_connection removed; using the real get_connection defined at the top of the file.



def daily_profit():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(created_at) AS day,
               SUM((p.selling_price - p.buying_price) * s.quantity) AS total_profit
        FROM sales s
        JOIN products p ON s.pid = p.id
        GROUP BY day
        ORDER BY day;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def create_user(full_name, email, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash)
        VALUES (%s, %s, %s);
    """, (full_name, email, password_hash))
    conn.commit()
    cur.close()
    conn.close()


def update_password(email, new_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash = %s WHERE email = %s;", (new_hash, email))
    conn.commit()
    cur.close()
    conn.close()


def save_otp(email, otp_code, expiry_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET otp_code = %s, otp_expiry = %s
        WHERE email = %s;
    """, (otp_code, expiry_time, email))
    conn.commit()
    cur.close()
    conn.close()


def verify_otp(email, otp_input):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT otp_code, otp_expiry
        FROM users
        WHERE email = %s;
    """, (email,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        return False

    now = datetime.utcnow()
    return result['otp_code'] == otp_input and now <= result['otp_expiry']


def log_otp_attempt(email, otp_code, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO otp_logs (email, otp_code, status, attempted_at)
        VALUES (%s, %s, %s, NOW());
    """, (email, otp_code, status))
    conn.commit()
    cur.close()
    conn.close()


def log_otp_expiry(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO otp_logs (email, otp_code, status, attempted_at)
        VALUES (%s, NULL, 'expired', NOW());
    """, (email,))
    conn.commit()
    cur.close()
    conn.close()


def fetch_otp_logs(limit=100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, email, otp_code, status, attempted_at
        FROM otp_logs
        ORDER BY attempted_at DESC
        LIMIT %s;
    """, (limit,))
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return logs


def search_everything(term):
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{term}%"

    cur.execute("""
        SELECT 'user' AS type, id, full_name AS label, email AS detail
        FROM users
        WHERE full_name ILIKE %s OR email ILIKE %s

        UNION

        SELECT 'product', id, name AS label, CAST(selling_price AS TEXT) AS detail
        FROM products
        WHERE name ILIKE %s OR CAST(selling_price AS TEXT) ILIKE %s

        UNION

        SELECT 'sale', id, CAST(pid AS TEXT) AS label, CAST(quantity AS TEXT) AS detail
        FROM sales
        WHERE CAST(pid AS TEXT) ILIKE %s OR CAST(quantity AS TEXT) ILIKE %s

        UNION

        SELECT 'stock', id, CAST(pid AS TEXT) AS label, CAST(stock_quantity AS TEXT) AS detail
        FROM stock
        WHERE CAST(pid AS TEXT) ILIKE %s OR CAST(stock_quantity AS TEXT) ILIKE %s
    """, (like, like, like, like, like, like, like, like))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def fetch_user_by_id(user_id):
    """
    Fallback helper to locate a user by id using fetch_data('users').
    This is used when the database module doesn't expose a direct fetch_user_by_id.
    """
    users = fetch_data('users') or []
    for u in users:
        # Compare as strings to be resilient to int/str id types
        if str(u.get('id')) == str(user_id):
            return u
    return None