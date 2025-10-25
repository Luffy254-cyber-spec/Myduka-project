import psycopg2
from datetime import datetime

# connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="12199",
    dbname="myduka_db"
)
curr = conn.cursor()


# # PRODUCTS

# def fetch_products():
#     curr.execute('select * from products;')
#     products = curr.fetchall()
#     return products

# products = fetch_products()
# print(" PRODUCTS:")
# print(products)


# # STOCK

# def fetch_stock():
#     curr.execute('select * from stock;')
#     stock = curr.fetchall()
#     return stock

# stock = fetch_stock()
# print(" STOCK:")
# print(stock)

# # SALES

# def fetch_sales():
#     curr.execute('select * from sales;')
#     sales = curr.fetchall()
#     return sales

# sales = fetch_sales()
# print(" SALES:")
# print(sales)



# # INSERT PRODUCT

# def insert_product(name, buying_price, selling_price):
#     curr.execute(
#         "insert into products (name, buying_price, selling_price) values (%s, %s, %s)",
#         (name, buying_price, selling_price)
#     )
#     conn.commit()
#     print(f" Product '{name}' added!")




# # INSERT STOCK

# def insert_stock(pid, quantity):
#     curr.execute(
#         "insert into stock (pid, stock_quantity) values (%s, %s) on conflict (pid) do update set stock_quantity = stock.stock_quantity + excluded.stock_quantity",
#         (pid, quantity)
#     )
#     conn.commit()
#     print(f" Added {quantity} units to stock for product ID {pid}")





# # INSERT SALE

# def insert_sale(pid, quantity):
#     curr.execute("select stock_quantity from stock where pid = %s", (pid,))
#     stock = curr.fetchone()

#     if not stock:
#         print(" Product not found in stock.")
#         return

#     if stock[0] < quantity:
#         print(" Not enough stock available.")
#         return

#     curr.execute(
#         "insert into sales (pid, quantity, created_at) values (%s, %s, %s)",
#         (pid, quantity, datetime.now())
#     )

#     curr.execute(
#         "update stock set stock_quantity = stock_quantity - %s where pid = %s",
#         (quantity, pid)
#     )

#     conn.commit()
#     print(f" Sale of {quantity} units recorded for product ID {pid}")


# # PROFIT PER PRODUCT

# def get_profit_per_product():
#     curr.execute("""
#         select p.name, sum(s.quantity * (p.selling_price - p.buying_price)) as profit
#         from sales s
#         join products p on s.pid = p.id
#         group by p.name
#     """)
#     profit = curr.fetchall()
#     return profit

# profit = get_profit_per_product()
# print(" PROFIT PER PRODUCT:")
# print(profit)



# # SALES PER PRODUCT

# def get_sales_per_product():
#     curr.execute("""
#         select p.name, sum(s.quantity) as total_sold
#         from sales s
#         join products p on s.pid = p.id
#         group by p.name
#     """)
#     sales_per_product = curr.fetchall()
#     return sales_per_product

# sales_per_product = get_sales_per_product()
# print(" SALES PER PRODUCT:")
# print(sales_per_product)

def fetch_data(table_name):
     curr.execute(f"SELECT * FROM {table_name}")
     return curr.fetchall()

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

# def insert_product(name, buying_price, selling_price):
#     query = "
#         INSERT INTO products(name, buying_price, selling_price)
#         VALUES (%s, %s, %s);
#     "
#     curr.execute(query, (name, buying_price, selling_price))


# conn.commit()

def insert_product(p_values):
     query = "INSERT INTO products(name, buying_price, selling_price) VALUES (%s, %s, %s);"
    
     curr.execute(query, p_values)
     conn.commit() 

# new_product=('Avocados',50,70)
# # insert_product(new_product)
# products = fetch_data('products')
# print(products)

#insert sales
def insert_sales(values):
     query = 'insert into sales(pid, quantity, created_at) values(%s, %s, now());'
     curr.execute(query, values)
     conn.commit()

# new_sale = (2,5)
# #insert_sales(new_sale)
# sales = fetch_data('sales')
# print(sales)

# insert stock
def insert_stock(values):
    query = 'INSERT INTO stock(pid, stock_quantity) VALUES (%s, %s);'
    curr.execute(query, values)
    conn.commit()

# new_stock = (2, 5)  
# #insert_stock(new_stock)
# stock = fetch_data('stock')
# print(stock)

# def insert_products(name, bp, sp):
#     curr.execute(
#         f"insert into products(name, buying_price, selling_price) values('{name}', {bp}, {sp})"
#     )
#     connect.commit()

# insert_products("milk", 60, 100)

# products = fetch_data('products')
# print(products)


# # profit per product
# def fetch_profit_per_product():
#     query = "SELECT name, (selling_price - buying_price) AS profit_per_product FROM products;"
#     curr.execute(query)
#     conn.commit()
    
# profit_data = fetch_profit_per_product()
# profit_data = fetch_data('products')
# print(profit_data)


# # sales per product
# def fetch_sales_per_product():
#     query = "SELECT p.name, SUM(s.quantity) AS total_sales FROM sales s JOIN products p ON s.pid = p.id GROUP BY p.name;"
#     curr.execute(query)
#     conn.commit()

# sales_data = fetch_sales_per_product()
# sales_data = fetch_data('sales')
# print(sales_data)
# profit per product
def product_profit():
    query = 'SELECT p.name, p.id, SUM((p.selling_price - p.buying_price) * s.quantity) AS profit FROM sales AS s INNER JOIN products AS p ON s.pid = p.id GROUP BY p.name, p.id;'
    curr.execute(query)
    profit = curr.fetchall()
    return profit

myprofits = product_profit()
print(f"My products profit: {myprofits}")


# sales per product
def product_sales():
    query = 'SELECT p.id, p.name, SUM(p.selling_price * s.quantity) AS total_sales FROM sales AS s JOIN products AS p ON s.pid = p.id GROUP BY p.id, p.name;'
    curr.execute(query)
    sales = curr.fetchall()
    return sales

mysales = product_sales()
print(f"My products sales: {mysales}")


# delete data by id
def delete_data(table, record_id):
    query = f'DELETE FROM {table} WHERE id = %s;'
    curr.execute(query, (record_id,))
    conn.commit()
    print(f"Record with id {record_id} deleted from {table} table.")
