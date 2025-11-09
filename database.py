from flask import flash, g, redirect, url_for
from flask_login import current_user
import psycopg2
from datetime import datetime
import psycopg2.extras
from functools import wraps
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "12199",
    "dbname": "myduka_db",
    "cursor_factory": psycopg2.extras.RealDictCursor
}
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

def product_exists(name):
    conn = get_connection()
    curr = conn.cursor()
    curr.execute("SELECT 1 FROM products WHERE LOWER(name) = %s LIMIT 1", (name.lower(),))
    exists = curr.fetchone() is not None
    curr.close()
    conn.close()
    return exists

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

# 🧮 Total Products
def count_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM products")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total'] if row else 0

# 💰 Total Sales (KSh)
def calculate_total_sales():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(s.quantity * p.selling_price), 0) AS total_sales
        FROM sales s
        JOIN products p ON s.pid = p.id
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total_sales'] if row else 0

# 📦 Total Stock
def calculate_total_stock():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(stock_quantity), 0) AS total_stock FROM stock")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total_stock'] if row else 0

# 📈 Total Profit (KSh)
def calculate_total_profit():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(s.quantity * (p.selling_price - p.buying_price)), 0) AS total_profit
        FROM sales s
        JOIN products p ON s.pid = p.id
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total_profit'] if row else 0

# 📉 Loss Incurred (KSh)
def calculate_total_loss():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(s.quantity * (p.buying_price - p.selling_price)), 0) AS total_loss
        FROM sales s
        JOIN products p ON s.pid = p.id
        WHERE p.buying_price > p.selling_price
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total_loss'] if row else 0

# 🧾 Total Transactions
def count_sales_entries():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM sales")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['total'] if row else 0

def create_tables():
    """Create basic tables for user management & audit."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    actor VARCHAR(255),
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255),
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()

def get_user_by_email(email):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
        return cur.fetchone()

def fetch_user_by_id(user_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        return cur.fetchone()

def get_all_users():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, full_name, email, role, created_at
            FROM users
            ORDER BY created_at DESC;
        """)
        return cur.fetchall()

def update_user_role(user_id, new_role):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE users SET role = %s WHERE id = %s RETURNING email;", (new_role, user_id))
        res = cur.fetchone()
        conn.commit()
        if res:
            log_audit("system", f"Updated role for {res['email']} to {new_role}")
        return res

def get_audit_logs(limit=50):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT actor, action, timestamp
            FROM audit_logs
            ORDER BY timestamp DESC
            LIMIT %s;
        """, (limit,))
        return cur.fetchall()

def log_audit(actor, action):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO audit_logs (actor, action) VALUES (%s,%s);", (actor, action))
        conn.commit()

def log_violation(email, reason):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO violations (email, reason) VALUES (%s,%s);", (email, reason))
        conn.commit()
        log_audit("system", f"Violation logged for {email}: {reason}")

def get_violation_logs():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT v.id, u.full_name, v.violation_type, v.description,
                   v.detected_at, v.resolved, v.severity, v.ban_duration
            FROM violation_logs v
            JOIN users u ON v.user_id = u.id
            ORDER BY v.detected_at DESC;
        """)
        return cur.fetchall()


def get_system_stats():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users;"); total_users = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM users WHERE role='admin';"); total_admins = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM users WHERE role='superadmin';"); total_superadmins = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM users WHERE role='supplier';"); total_suppliers = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM violations;"); total_violations = cur.fetchone()['count']
        return {
            "total_users": total_users,
            "total_admins": total_admins,
            "total_superadmins": total_superadmins,
            "total_suppliers": total_suppliers,
            "total_violations": total_violations
        }

def fetch_one(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def execute_query(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()

def fetch_all(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ---------- CUSTOM ADMIN QUERIES ----------
def get_audit_logs():
    query = "SELECT * FROM audit_logs ORDER BY created_at DESC;"
    return fetch_all(query)

def get_system_stats():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT COUNT(*) AS total_users FROM users;")
    total_users = cur.fetchone()['total_users']

    cur.execute("SELECT COUNT(*) AS total_sales FROM sales;")
    total_sales = cur.fetchone()['total_sales']

    # Use product price × quantity for total revenue
    cur.execute("""
        SELECT COALESCE(SUM(p.price * s.quantity), 0) AS total_revenue
        FROM sales s
        JOIN products p ON s.product_id = p.id;
    """)
    total_revenue = cur.fetchone()['total_revenue']

    cur.close()
    conn.close()

    return {
        'total_users': total_users,
        'total_sales': total_sales,
        'total_revenue': total_revenue
    }

def get_recent_sales(limit=10):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT s.id, p.name AS product_name, s.quantity, s.total, s.created_at
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        ORDER BY s.created_at DESC
        LIMIT %s;
    """
    cur.execute(query, (limit,))
    results = cur.fetchall()

    cur.close()
    conn.close()
    return [dict(r) for r in results]


# -------------------------------------------------
# ✅ 2. Get top products by total revenue
# -------------------------------------------------
def get_top_products_by_revenue(limit=5):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT p.name, SUM(s.total) AS revenue, SUM(s.quantity) AS sold
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        GROUP BY p.name
        ORDER BY revenue DESC
        LIMIT %s;
    """
    cur.execute(query, (limit,))
    results = cur.fetchall()

    cur.close()
    conn.close()
    return [dict(r) for r in results]


# -------------------------------------------------
# ✅ 3. Get revenue trend (for Chart.js graph)
# -------------------------------------------------
def get_revenue_timeseries(days=30):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT 
            DATE(s.created_at) AS sale_date,
            COALESCE(SUM(s.total), 0) AS daily_revenue
        FROM sales s
        WHERE s.created_at >= NOW() - INTERVAL %s
        GROUP BY DATE(s.created_at)
        ORDER BY DATE(s.created_at);
    """
    cur.execute(query, (f'{days} days',))
    data = cur.fetchall()

    cur.close()
    conn.close()

    labels = [str(row['sale_date']) for row in data]
    values = [float(row['daily_revenue']) for row in data]
    return labels, values

def get_top_products(limit=5):
    """
    Fetch top-selling products by total quantity and revenue.
    Joins products and sales tables to compute totals.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT 
            p.id,
            p.name AS product_name,
            COALESCE(SUM(s.quantity), 0) AS total_sold,
            COALESCE(SUM(p.price * s.quantity), 0) AS total_revenue
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC
        LIMIT %s;
    """

    cur.execute(query, (limit,))
    products = cur.fetchall()

    cur.close()
    conn.close()
    return products

def update_user_role(user_id, new_role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = %s WHERE id = %s;", (new_role, user_id))
    conn.commit()
    cur.close()
    conn.close()


def update_product(product_id, name, buying_price, selling_price):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE products
        SET name = %s,
            buying_price = %s,
            selling_price = %s
        WHERE id = %s;
    """, (name, buying_price, selling_price, product_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_product_by_id(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s;", (product_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_stock_quantity(stock_id, quantity):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE stock SET stock_quantity = %s WHERE id = %s;", (quantity, stock_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_stock_by_id(stock_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM stock WHERE id = %s;", (stock_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_sale_quantity(sale_id, quantity):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE sales SET quantity = %s WHERE id = %s;", (quantity, sale_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_sale_by_id(sale_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sales WHERE id = %s;", (sale_id,))
    conn.commit()
    cur.close()
    conn.close()

def log_action(user_id, actor_email, action, context, target_email=None, details=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_logs (user_id, actor_email, action, context, target_email, details)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, actor_email, action, context, target_email, details))
    conn.commit()
    cur.close()
    conn.close()
    


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
    return g.db

def get_cursor():
    return get_db().cursor(cursor_factory=RealDictCursor)

def get_pending_lockout_requests():
    cur = get_cursor()
    cur.execute("SELECT * FROM lockout_requests WHERE status = 'pending' ORDER BY created_at DESC")
    return cur.fetchall()

def get_rejected_lockout_requests():
    cur = get_cursor()
    cur.execute("SELECT * FROM lockout_requests WHERE status = 'rejected' ORDER BY created_at DESC")
    return cur.fetchall()

def get_lockout_request_by_id(request_id):
    cur = get_cursor()
    cur.execute("SELECT * FROM lockout_requests WHERE id = %s", (request_id,))
    return cur.fetchone()

def reject_lockout_request(request_id, reason):
    cur = get_cursor()
    cur.execute("UPDATE lockout_requests SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason, request_id))
    get_db().commit()

def restore_lockout_request(request_id):
    cur = get_cursor()
    cur.execute("UPDATE lockout_requests SET status = 'pending', rejection_reason = NULL WHERE id = %s", (request_id,))
    get_db().commit()

def log_action(user_id, actor_email, action, context, target_email=None, details=None):
    cur = get_cursor()
    cur.execute("""
        INSERT INTO audit_logs (user_id, actor_email, action, context, target_email, details)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, actor_email, action, context, target_email, details))
    get_db().commit()

def count_pending_lockouts():
    cur = get_cursor()
    cur.execute("SELECT COUNT(*) FROM lockout_requests WHERE status = 'pending'")
    return cur.fetchone()['count']

def count_rejected_lockouts():
    cur = get_cursor()
    cur.execute("SELECT COUNT(*) FROM lockout_requests WHERE status = 'rejected'")
    return cur.fetchone()['count']

def quick_unlock(email):
    cur = get_cursor()
    cur.execute("DELETE FROM lockout_requests WHERE email = %s", (email,))
    get_db().commit()

def get_notifications(user_id, role=None):
    cur = get_cursor()
    if role in ["admin", "superadmin"]:
        cur.execute("""
    SELECT n.*, u.full_name AS sender_name
    FROM notifications n
    LEFT JOIN users u ON n.sender_id = u.id
    WHERE n.role IN ('admin', 'superadmin') OR n.user_id = %s
    ORDER BY n.created_at DESC
""", (user_id,))
    else:
       cur.execute("""
    SELECT n.*, u.full_name AS sender_name
    FROM notifications n
    LEFT JOIN users u ON n.sender_id = u.id
    WHERE n.role IN ('admin', 'superadmin') OR n.user_id = %s
    ORDER BY n.created_at DESC
""", (user_id,))
    return cur.fetchall()



def broadcast_notification_to_all(title, message, sender_id):
    cur = get_cursor()
    cur.execute("""
        INSERT INTO notifications (user_id, sender_id, title, message, is_read, role, created_at)
        SELECT id, %s, %s, %s, FALSE, role, CURRENT_TIMESTAMP FROM users
    """, (sender_id, title, message))
    get_db().commit()



# ---------- NOTIFICATIONS HELPERS ----------

def mark_notifications_as_read(user_id, role=None):
    cur = get_cursor()
    if role in ["admin", "superadmin"]:
        cur.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE user_id = %s OR role IN ('admin', 'superadmin')
        """, (user_id,))
    else:
        cur.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE user_id = %s
        """, (user_id,))
    get_db().commit()


def clear_read_notifications_for_user(user_id, role=None):
    conn = get_db()
    cur = conn.cursor()
    if role in ("admin", "superadmin"):
        cur.execute("""
            DELETE FROM notifications
            WHERE is_read = TRUE
              AND (user_id = %s OR role IN ('admin', 'superadmin'))
            RETURNING id;
        """, (user_id,))
    else:
        cur.execute("""
            DELETE FROM notifications
            WHERE is_read = TRUE
              AND user_id = %s
            RETURNING id;
        """, (user_id,))

    deleted_rows = cur.fetchall()
    conn.commit()
    print(f"[DEBUG] Deleted {len(deleted_rows)} read notifications for user_id={user_id}, role={role}")



if __name__ == "__main__":
    create_tables()
