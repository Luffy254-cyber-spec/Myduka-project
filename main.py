from flask import Flask, render_template, request, redirect
from database import fetch_data, insert_product, insert_sales, insert_stock, product_profit

app = Flask(__name__)

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')


# ---------- PRODUCTS ----------
@app.route('/products')
def products():
    search = request.args.get('search', '').strip()
    products = fetch_data('products')

    if search:
        products = [p for p in products if search.lower() in p[1].lower()]

    return render_template('products.html', products=products)


# ---------- SALES ----------
@app.route('/sales')
def sales():
    search = request.args.get('search', '').strip()
    sales = fetch_data('sales')

    if search:
        sales = [
            s for s in sales
            if search.lower() in str(s[1]).lower()
            or search.lower() in str(s[3]).lower()
        ]

    return render_template('sales.html', sales=sales)


# ---------- STOCK ----------
@app.route('/stock')
def stock():
    search = request.args.get('search', '').strip()
    stock = fetch_data('stock')

    if search:
        stock = [
            s for s in stock
            if search.lower() in str(s[1]).lower()
            or search.lower() in str(s[2]).lower()
            or search.lower() in str(s[3]).lower()
        ]

    return render_template('stock.html', stock=stock)


# ---------- PROFIT ----------
@app.route('/profit')
def profit():
    profit = product_profit()
    return render_template('profit.html', profit=profit)


# ---------- FORM HANDLERS ----------
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    buying_price = request.form['buying_price']
    selling_price = request.form['selling_price']
    insert_product((name, buying_price, selling_price))
    return redirect('/products')


@app.route('/add_sale', methods=['POST'])
def add_sale():
    pid = request.form['pid']
    quantity = request.form['quantity']
    insert_sales((pid, quantity))
    return redirect('/sales')


@app.route('/add_stock', methods=['POST'])
def add_stock():
    pid = request.form['pid']
    quantity = request.form['quantity']
    insert_stock((pid, quantity))
    return redirect('/stock')


# ---------- RUN APP ----------
if __name__ == '__main__':
    app.run(debug=True)
