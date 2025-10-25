from flask import Flask, render_template, request, redirect
from database import fetch_data, insert_product, insert_sales, insert_stock, product_profit

app = Flask(__name__)

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/products')
def products():
    products = fetch_data('products')
    return render_template('products.html', products=products)


@app.route('/sales')
def sales():
    sales = fetch_data('sales')
    return render_template('sales.html', sales=sales)


@app.route('/stock')
def stock():
    stock = fetch_data('stock')
    return render_template('stock.html', stock=stock)


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


if __name__ == '__main__':
    app.run(debug=True)
