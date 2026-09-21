import csv
import random
from pathlib import Path
from datetime import date, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# BASIC DATA
# ============================================================

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Arjun", "Aryan",
    "Aditi", "Ananya", "Anika", "Diya", "Isha",
    "Kavya", "Meera", "Neha", "Pooja", "Riya",
    "Sahana", "Shreya", "Sneha", "Tanvi", "Varsha"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Reddy",
    "Nair", "Gupta", "Verma", "Joshi", "Mehta",
    "Rao", "Iyer", "Shah", "Das", "Bhat"
]

CITIES = [
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Kochi"
]

PRODUCTS = [
    {
        "product_id": "P001",
        "product_name": "Premium Hoodie",
        "category": "Fashion",
        "price": 2499,
        "cost": 1300,
        "rating": 3.2,
        "performance": "weak_conversion"
    },
    {
        "product_id": "P002",
        "product_name": "Running Shoes",
        "category": "Footwear",
        "price": 3999,
        "cost": 2100,
        "rating": 4.4,
        "performance": "best"
    },
    {
        "product_id": "P003",
        "product_name": "Wireless Earbuds",
        "category": "Electronics",
        "price": 2999,
        "cost": 1500,
        "rating": 3.8,
        "performance": "normal"
    },
    {
        "product_id": "P004",
        "product_name": "Smart Watch",
        "category": "Electronics",
        "price": 5499,
        "cost": 3200,
        "rating": 4.2,
        "performance": "best"
    },
    {
        "product_id": "P005",
        "product_name": "Cotton T-Shirt",
        "category": "Fashion",
        "price": 999,
        "cost": 420,
        "rating": 4.1,
        "performance": "best"
    },
    {
        "product_id": "P006",
        "product_name": "Denim Jacket",
        "category": "Fashion",
        "price": 2799,
        "cost": 1450,
        "rating": 3.9,
        "performance": "normal"
    },
    {
        "product_id": "P007",
        "product_name": "Laptop Backpack",
        "category": "Accessories",
        "price": 1799,
        "cost": 850,
        "rating": 4.5,
        "performance": "best"
    },
    {
        "product_id": "P008",
        "product_name": "Bluetooth Speaker",
        "category": "Electronics",
        "price": 2299,
        "cost": 1200,
        "rating": 3.7,
        "performance": "normal"
    },
    {
        "product_id": "P009",
        "product_name": "Sunglasses",
        "category": "Accessories",
        "price": 1499,
        "cost": 600,
        "rating": 4.0,
        "performance": "normal"
    },
    {
        "product_id": "P010",
        "product_name": "Sports Track Pants",
        "category": "Fashion",
        "price": 1599,
        "cost": 700,
        "rating": 4.3,
        "performance": "best"
    },
    {
        "product_id": "P011",
        "product_name": "Face Serum",
        "category": "Beauty",
        "price": 1299,
        "cost": 500,
        "rating": 4.2,
        "performance": "normal"
    },
    {
        "product_id": "P012",
        "product_name": "Moisturizer",
        "category": "Beauty",
        "price": 899,
        "cost": 350,
        "rating": 4.4,
        "performance": "best"
    },
    {
        "product_id": "P013",
        "product_name": "Coffee Maker",
        "category": "Home",
        "price": 3499,
        "cost": 1900,
        "rating": 4.1,
        "performance": "normal"
    },
    {
        "product_id": "P014",
        "product_name": "Air Fryer",
        "category": "Home",
        "price": 5999,
        "cost": 3500,
        "rating": 4.5,
        "performance": "best"
    },
    {
        "product_id": "P015",
        "product_name": "Yoga Mat",
        "category": "Fitness",
        "price": 1199,
        "cost": 450,
        "rating": 3.9,
        "performance": "normal"
    }
]


# ============================================================
# GENERATE PRODUCTS
# ============================================================

def generate_products():

    rows = []

    for product in PRODUCTS:

        performance = product["performance"]

        if performance == "weak_conversion":

            # Deliberately create the PPT-style example:
            # high traffic + weak conversion.

            views = 52400
            add_to_cart = 1850
            checkout = 1100
            units_sold = 942
            returns = 31

        elif performance == "best":

            views = random.randint(18000, 42000)

            add_to_cart = int(
                views * random.uniform(0.16, 0.23)
            )

            checkout = int(
                add_to_cart * random.uniform(0.55, 0.72)
            )

            units_sold = int(
                checkout * random.uniform(0.55, 0.78)
            )

            returns = int(
                units_sold * random.uniform(0.015, 0.035)
            )

        else:

            views = random.randint(12000, 38000)

            add_to_cart = int(
                views * random.uniform(0.10, 0.17)
            )

            checkout = int(
                add_to_cart * random.uniform(0.45, 0.65)
            )

            units_sold = int(
                checkout * random.uniform(0.45, 0.70)
            )

            returns = int(
                units_sold * random.uniform(0.025, 0.065)
            )

        rows.append({
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "category": product["category"],
            "price": product["price"],
            "cost": product["cost"],
            "views": views,
            "add_to_cart": add_to_cart,
            "checkout": checkout,
            "units_sold": units_sold,
            "returns": returns,
            "rating": product["rating"]
        })

    return rows


# ============================================================
# GENERATE CUSTOMERS
# ============================================================

def generate_customers(count=500):

    rows = []

    for i in range(1, count + 1):

        customer_id = f"C{i:04d}"

        name = (
            random.choice(FIRST_NAMES)
            + " "
            + random.choice(LAST_NAMES)
        )

        city = random.choice(CITIES)

        customer_type = random.random()

        if customer_type < 0.08:

            # VIP

            orders = random.randint(8, 18)

            total_spend = random.randint(
                35000,
                95000
            )

            last_order_days = random.randint(
                1,
                15
            )

        elif customer_type < 0.30:

            # Loyal

            orders = random.randint(4, 8)

            total_spend = random.randint(
                15000,
                35000
            )

            last_order_days = random.randint(
                1,
                30
            )

        elif customer_type < 0.50:

            # Returning

            orders = random.randint(2, 3)

            total_spend = random.randint(
                5000,
                16000
            )

            last_order_days = random.randint(
                5,
                45
            )

        elif customer_type < 0.78:

            # New

            orders = 1

            total_spend = random.randint(
                800,
                6000
            )

            last_order_days = random.randint(
                1,
                30
            )

        else:

            # At Risk

            orders = random.randint(
                2,
                6
            )

            total_spend = random.randint(
                6000,
                28000
            )

            last_order_days = random.randint(
                61,
                150
            )

        last_date = (
            date.today()
            - timedelta(days=last_order_days)
        )

        first_date = (
            last_date
            - timedelta(
                days=random.randint(
                    30,
                    400
                )
            )
        )

        rows.append({
            "customer_id": customer_id,
            "customer_name": name,
            "city": city,
            "orders": orders,
            "total_spend": total_spend,
            "last_order_days": last_order_days,
            "first_order_date": first_date.isoformat(),
            "last_order_date": last_date.isoformat()
        })

    return rows


# ============================================================
# GENERATE ORDERS
# ============================================================

def generate_orders(
    customers,
    products,
    count=5000
):

    rows = []

    customer_weights = []

    for customer in customers:

        # Customers with more orders get higher
        # probability of appearing in the order dataset.

        weight = max(
            1,
            int(customer["orders"])
        )

        customer_weights.append(weight)

    customer_pool = []

    for customer, weight in zip(
        customers,
        customer_weights
    ):

        customer_pool.extend(
            [customer] * weight
        )

    start_date = date.today() - timedelta(days=180)

    for i in range(1, count + 1):

        order_id = f"O{i:06d}"

        customer = random.choice(
            customer_pool
        )

        product = random.choice(
            products
        )

        quantity = random.randint(
            1,
            4
        )

        price = float(
            product["price"]
        )

        discount = random.choice([
            0,
            0,
            50,
            100,
            150,
            200,
            300,
            500
        ])

        gross = price * quantity

        revenue = max(
            0,
            gross - discount
        )

        order_date = (
            start_date
            + timedelta(
                days=random.randint(
                    0,
                    180
                )
            )
        )

        status_roll = random.random()

        if status_roll < 0.93:

            status = "Completed"

        elif status_roll < 0.97:

            status = "Returned"

        else:

            status = "Cancelled"

        rows.append({
            "order_id": order_id,
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "order_date": order_date.isoformat(),
            "quantity": quantity,
            "price": int(price),
            "discount": discount,
            "revenue": round(revenue, 2),
            "status": status
        })

    return rows


# ============================================================
# WRITE CSV
# ============================================================

def write_csv(filename, rows):

    if not rows:
        return

    filepath = DATA_DIR / filename

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()

        writer.writerows(rows)

    print(
        f"Created: {filepath}"
    )

    print(
        f"Rows: {len(rows)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("ECOMLYTICS DATASET GENERATOR")
    print("=" * 60)

    print()

    # Products

    products = generate_products()

    write_csv(
        "products.csv",
        products
    )

    # Customers

    customers = generate_customers(
        count=500
    )

    write_csv(
        "customers.csv",
        customers
    )

    # Orders

    orders = generate_orders(
        customers,
        products,
        count=5000
    )

    write_csv(
        "orders.csv",
        orders
    )

    print()

    print("=" * 60)
    print("DATASET GENERATION COMPLETE")
    print("=" * 60)

    print()

    print(
        f"Products : {len(products)}"
    )

    print(
        f"Customers: {len(customers)}"
    )

    print(
        f"Orders   : {len(orders)}"
    )

    print()

    print(
        f"Files saved in: {DATA_DIR}"
    )


if __name__ == "__main__":
    main()