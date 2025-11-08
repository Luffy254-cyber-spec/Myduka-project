from datetime import datetime, timedelta
from functools import wraps
import random
from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_mail import Message, Mail
from database import calculate_total_loss, calculate_total_profit, calculate_total_sales, calculate_total_stock, count_products, count_sales_entries, create_user, daily_profit, daily_sales, delete_product_by_id, delete_sale_by_id, delete_stock_by_id, fetch_data, fetch_otp_logs, fetch_products_for_dropdown, fetch_user_by_id, get_all_users, get_audit_logs, get_connection, get_recent_sales, get_revenue_timeseries, get_system_stats, get_top_products, get_top_products_by_revenue, get_user_by_email, get_violation_logs, insert_product, insert_sales, insert_stock, log_otp_attempt, product_profit, product_sales, save_otp, search_everything, update_password, update_product, update_sale_quantity, update_stock_quantity, update_user_role, verify_otp
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, current_user, login_required
from flask_login import UserMixin
from flask_login import login_user
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_babel import Babel, gettext
import time
from flask import session

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes

def is_locked_out():
    lockout = session.get("lockout_until")
    return lockout and time.time() < lockout

def increment_attempts():
    session["attempts"] = session.get("attempts", 0) + 1
    if session["attempts"] >= MAX_ATTEMPTS:
        session["lockout_until"] = time.time() + LOCKOUT_SECONDS

def reset_attempts():
    session.pop("attempts", None)
    session.pop("lockout_until", None)





class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')


# import os

app = Flask(__name__)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects to this route if not logged in
app.secret_key = 'your-unique-secret-key'  # 🔐 Add this line
# app.secret_key = os.environ.get('SECRET_KEY', 'fallback-dev-key')
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
babel = Babel(app)

# ROUTES 
# ---------- DECORATORS ----------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ("admin", "superadmin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "superadmin":
            flash("Superadmin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/products')
@login_required
def products():
    search = request.args.get('search', '').strip()
    products = fetch_data('products') or []

    if search:
        products = [
            p for p in products
            if search.lower() in p['name'].lower()
            or search in str(p['buying_price'])
            or search in str(p['selling_price'])
        ]

    return render_template('products.html', products=products)

@app.route('/sales')
@login_required
def sales():
    search = request.args.get('search', '').strip()
    sales = fetch_data('sales') or []
    products = fetch_products_for_dropdown() or []

    if search:
        sales = [
            s for s in sales
            if search.lower() in str(s['pid']).lower()
            or search.lower() in str(s['quantity'])
            or search.lower() in str(s['created_at'])
        ]

    return render_template('sales.html', sales=sales, products=products)

@app.route('/stock')
@login_required
def stock():
    search = request.args.get('search', '').strip()
    stock = fetch_data('stock') or []
    products = fetch_products_for_dropdown() or []

    if search:
        stock = [
            s for s in stock
            if search.lower() in str(s['pid']).lower()
            or search.lower() in str(s['stock_quantity'])
            or search.lower() in str(s['created_at'])
        ]

    return render_template('stock.html', stock=stock, products=products)


# #  PROFIT 
# @app.route('/profit')
# def profit():
#     profit = product_profit()
#     return render_template('profit.html', profit=profit)


# FORM HANDLERS 
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    buying_price = request.form['buying_price']
    selling_price = request.form['selling_price']
    insert_product((name, buying_price, selling_price))
    return redirect(url_for('products'))


@app.route('/add_sale', methods=['POST'])
def add_sale():
    pid = request.form['pid']
    quantity = request.form['quantity']
    insert_sales((pid, quantity))
    return redirect(url_for('sales'))



@app.route('/add_stock', methods=['POST'])
def add_stock():
    pid = request.form['pid']
    quantity = request.form['quantity']
    insert_stock((pid, quantity))
    return redirect('/stock')

@app.route('/dashboard')
@login_required
def dashboard():
    # --- Sales per product ---
    sales_data = product_sales()
    sales_labels = [row['name'] for row in sales_data]
    sales_values = [float(row['total_sales']) for row in sales_data]

    # --- Profit per product ---
    profit_data = product_profit()
    profit_labels = [row['name'] for row in profit_data]
    profit_values = [float(row['profit']) for row in profit_data]

    # --- Daily sales ---
    daily_sales_data = daily_sales()
    daily_sales_labels = [row['day'].strftime('%Y-%m-%d') for row in daily_sales_data]
    daily_sales_values = [float(row['total_sales']) for row in daily_sales_data]

    # --- Daily profit ---
    daily_profit_data = daily_profit()
    daily_profit_labels = [row['day'].strftime('%Y-%m-%d') for row in daily_profit_data]
    daily_profit_values = [float(row['total_profit']) for row in daily_profit_data]

    # --- Summary totals ---
    total_products = count_products()
    total_sales = calculate_total_sales()
    total_stock = calculate_total_stock()
    total_profit = calculate_total_profit()
    total_loss = calculate_total_loss()
    total_transactions = count_sales_entries()

    return render_template(
        'dashboard.html',
        # Chart data
        sales_labels=sales_labels,
        sales_values=sales_values,
        profit_labels=profit_labels,
        profit_values=profit_values,
        daily_sales_labels=daily_sales_labels,
        daily_sales_values=daily_sales_values,
        daily_profit_labels=daily_profit_labels,
        daily_profit_values=daily_profit_values,

        # Summary totals
        total_products=total_products,
        total_sales=total_sales,
        total_stock=total_stock,
        total_profit=total_profit,
        total_loss=total_loss,
        total_transactions=total_transactions
    )

# def check_password_hash(stored_hash, password):
#     raise NotImplementedError

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_locked_out():
        return render_template("429.html"), 429

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = get_user_by_email(email)

        # Validate user credentials
        if not user or not check_password_hash(user['password_hash'], password):
            increment_attempts()
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

        # Successful login
        reset_attempts()
        user_obj = User(user['id'], user['full_name'], user['email'], user['role'])
        login_user(user_obj)
        session['user_name'] = user['full_name']
        flash(f"Welcome back, {user['full_name']}!", "success")

        # Role-based redirects
        if user['role'] == 'superadmin':
            return redirect(url_for('superadmin_dashboard'))
        elif user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'supplier':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_locked_out():
        return render_template("429.html"), 429

    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']

        # Validation
        if not full_name or not email or not password or not confirm:
            increment_attempts()
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        if password != confirm:
            increment_attempts()
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        if get_user_by_email(email):
            increment_attempts()
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('login'))

        # Create user
        reset_attempts()
        hashed_password = generate_password_hash(password)
        create_user(full_name, email, hashed_password)
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profit')
@login_required
def profit():
    profit_data = product_profit()

    # Prepare labels and values for charting
    labels = [row['name'] for row in profit_data]
    values = [float(row['profit']) for row in profit_data]

    return render_template('profit.html', labels=labels, values=values, profit=profit_data)




@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        user = get_user_by_email(email)

        if not user:
            flash("Email not found.", "danger")
            return redirect(url_for('forgot_password'))

        otp = str(random.randint(100000, 999999))
        expiry = datetime.utcnow() + timedelta(minutes=10)
        save_otp(email, otp, expiry)

        msg = Message("Your OTP Code", recipients=[email])
        msg.body = f"Your OTP is: {otp}. It expires in 10 minutes."
        mail.send(msg)

        flash("OTP sent to your email.", "info")
        return redirect(url_for('reset_password'))

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        # Validate required fields
        if not email or not password or not confirm:
            flash("All fields are required.", "danger")
            return redirect(url_for('reset_password', email=email))

        # Check if user exists
        user = get_user_by_email(email)
        if not user:
            flash("Email not found.", "danger")
            return redirect(url_for('reset_password'))

        # Check password match
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('reset_password', email=email))

        # Update password
        hashed = generate_password_hash(password)
        update_password(email, hashed)
        flash("Password reset successful! You can now log in.", "success")
        return redirect(url_for('login'))

    # Preserve email across redirects
    email = request.args.get('email', '')
    return render_template('reset_password.html', email=email)

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    email = request.form['email'].strip().lower()
    user = get_user_by_email(email)

    if not user:
        flash("Email not found.", "danger")
        return redirect(url_for('forgot_password'))

    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=10)
    save_otp(email, otp, expiry)
    log_otp_attempt(email, otp, "resent")

    msg = Message("Your OTP Code", recipients=[email])
    msg.body = f"Your new OTP is: {otp}. It expires in 10 minutes."
    mail.send(msg)

    flash("New OTP sent to your email.", "info")
    return redirect(url_for('reset_password'))


@app.route('/admin/otp-logs')
def otp_logs():
    logs = fetch_otp_logs()
    return render_template('otp_logs.html', logs=logs)



@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for('dashboard'))

    results = search_everything(query)
    return render_template('search_results.html', query=query, results=results)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

class User(UserMixin):
    def __init__(self, id, full_name, email=None, role='user'):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.role = role

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    user_data = fetch_user_by_id(user_id)
    if user_data:
        username = user_data.get('username') or user_data.get('full_name') or user_data.get('email')
        email = user_data.get('email')
        role = user_data.get('role') or 'user'   # <-- ensure role loads
        return User(user_data['id'], username, email, role)
    return None

# ---------- ADMIN ----------
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    users = get_all_users()
    violations = get_violation_logs()
    return render_template("admin_dashboard.html", users=users, violations=violations)

# ---------- SUPERADMIN ----------
@app.route("/superadmin/dashboard")
@superadmin_required
def superadmin_dashboard():
    users = get_all_users()
    audit_logs = get_audit_logs()
    system_stats = get_system_stats()
    return render_template("superadmin_dashboard.html",
                           users=users, audit_logs=audit_logs, system_stats=system_stats)

@app.route("/superadmin/promote", methods=["POST"])
@superadmin_required
def promote_user():
    user_id = request.form["user_id"]
    new_role = request.form["new_role"]
    update_user_role(user_id, new_role)
    flash("Role updated successfully.", "success")
    return redirect(url_for("superadmin_dashboard"))

@app.route('/all_users')
@login_required
def all_users():
    if current_user.role != 'superadmin':
        flash('Access denied: Super Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    query = request.args.get('q', '').strip().lower()
    users = get_all_users()

    if query:
        users = [
            user for user in users
            if query in user['full_name'].lower()
            or query in user['email'].lower()
            or query in user['role'].lower()
        ]

    return render_template('superadmin/all_users.html', users=users, query=query)

# ---------- ADMIN & SUPER ADMIN ROUTES ----------

@app.route('/violation_logs')
@login_required
def violation_logs():
    # Allow both Admin and Super Admin
    if current_user.role not in ['admin', 'superadmin']:
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM violation_logs ORDER BY detected_at DESC")
    logs = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('superadmin/violation_logs.html', logs=logs)


@app.route('/audit_logs')
@login_required
def audit_logs():
    # Allow both Admin and Super Admin
    if current_user.role not in ['admin', 'superadmin']:
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    logs = get_audit_logs()
    return render_template('superadmin/audit_logs.html', logs=logs)


@app.route('/system_stats')
@login_required
def system_stats():
    # Allow both Admin and Super Admin
    if current_user.role not in ['admin', 'superadmin']:
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # --- Get overall statistics ---
        stats = get_system_stats() or {
            'total_users': 0,
            'total_sales': 0,
            'total_revenue': 0.0
        }

        # --- Get revenue timeseries (for charts) ---
        try:
            revenue_labels, revenue_values = get_revenue_timeseries(days=30)
        except Exception as e:
            print("Revenue timeseries error:", e)
            revenue_labels, revenue_values = [], []

        # --- Get top products ---
        try:
            top_products = get_top_products()
        except Exception as e:
            print("Top products error:", e)
            top_products = []

        return render_template(
            'superadmin/system_stats.html',
            stats=stats,
            revenue_labels=revenue_labels,
            revenue_values=revenue_values,
            top_products=top_products
        )

    except Exception as e:
        print("System stats route error:", e)
        flash('An error occurred while loading system statistics.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/update_role/<int:user_id>', methods=['POST'])
@login_required
def update_role(user_id):
    if current_user.role != 'superadmin':
        flash('Access denied: Super Admins only.', 'danger')
        return redirect(url_for('all_users'))

    new_role = request.form.get('role')

    if not new_role:
        flash('Please select a valid role.', 'warning')
        return redirect(url_for('all_users'))

    from database import update_user_role
    update_user_role(user_id, new_role)
    flash(f"User role updated to {new_role}.", "success")
    return redirect(url_for('all_users'))



@app.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    name = request.form['name']
    buying_price = request.form['buying_price']
    selling_price = request.form['selling_price']
    update_product(product_id, name, buying_price, selling_price)
    flash("Product updated successfully.", "success")
    return redirect(url_for('products'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    delete_product_by_id(product_id)
    flash("Product deleted.", "info")
    return redirect(url_for('products'))

@app.route('/edit_stock/<int:stock_id>', methods=['POST'])
def edit_stock(stock_id):
    quantity = request.form['quantity']
    update_stock_quantity(stock_id, quantity)
    flash("Stock updated successfully.", "success")
    return redirect(url_for('stock'))

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    delete_stock_by_id(stock_id)
    flash("Stock entry deleted.", "info")
    return redirect(url_for('stock'))

@app.route('/edit_sale/<int:sale_id>', methods=['POST'])
def edit_sale(sale_id):
    quantity = request.form['quantity']
    update_sale_quantity(sale_id, quantity)
    flash("Sale updated successfully.", "success")
    return redirect(url_for('sales'))

@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    delete_sale_by_id(sale_id)
    flash("Sale entry deleted.", "info")
    return redirect(url_for('sales'))

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@app.route('/privacy')
@login_required
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
@login_required
def terms():
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Optional: save to database, send email, log message
        flash("Your message has been sent successfully!", "success")
        return redirect('/contact')

    return render_template('contact.html')

@app.errorhandler(404)
def page_not_found(e):
    missing_url = request.path
    app.logger.warning(f"404 Not Found: {missing_url}")
    return render_template("404.html"), 404

@app.errorhandler(429)
def too_many_attempts(e):
    return render_template("429.html"), 429


#  RUN APP 
if __name__ == '__main__':
    app.run(debug=True)