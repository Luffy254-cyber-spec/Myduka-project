from datetime import datetime, timedelta
import random
from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_mail import Message, Mail
from database import create_user, daily_profit, daily_sales, fetch_data, fetch_otp_logs, fetch_products_for_dropdown, fetch_user_by_id, get_user_by_email, insert_product, insert_sales, insert_stock, log_otp_attempt, product_profit, product_sales, save_otp, search_everything, update_password, verify_otp
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required
from flask_login import UserMixin
from flask_login import login_user, logout_user, current_user


# import os

app = Flask(__name__)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects to this route if not logged in
app.secret_key = 'your-unique-secret-key'  # 🔐 Add this line
# app.secret_key = os.environ.get('SECRET_KEY', 'fallback-dev-key')
# ROUTES 

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

# DASHBOARD
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

    return render_template(
        'dashboard.html',
        sales_labels=sales_labels,
        sales_values=sales_values,
        profit_labels=profit_labels,
        profit_values=profit_values,
        daily_sales_labels=daily_sales_labels,
        daily_sales_values=daily_sales_values,
        daily_profit_labels=daily_profit_labels,
        daily_profit_values=daily_profit_values
    )

# def check_password_hash(stored_hash, password):
#     raise NotImplementedError

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = get_user_by_email(email)

        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['full_name'])
            login_user(user_obj)  # ✅ this activates Flask-Login session
            session['user_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for('dashboard'))

        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# def generate_password_hash(password):
#     raise NotImplementedError

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']

        # Validation
        if not full_name or not email or not password or not confirm:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        if get_user_by_email(email):
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('login'))

        # Create user
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
    return redirect(url_for('login'))



class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    # Use local fetch_user_by_id to retrieve user data
    user_data = fetch_user_by_id(user_id)
    if user_data:
        # support different possible username fields stored in the user record
        username = user_data.get('username') or user_data.get('full_name') or user_data.get('email')
        return User(user_data['id'], username)
    return None

#  RUN APP 
if __name__ == '__main__':
    app.run(debug=True)