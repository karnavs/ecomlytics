import csv
from pathlib import Path
from collections import defaultdict
from datetime import date, timedelta


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"


# ============================================================
# CSV READER
# ============================================================

def read_csv(name):
    filepath = DATA / name

    if not filepath.exists():
        raise FileNotFoundError(
            f"Dataset not found: {filepath}"
        )

    with open(
        filepath,
        newline="",
        encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))


# ============================================================
# SAFE CONVERSION HELPERS
# ============================================================

def to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def percentage(value, total, decimals=2):
    if total == 0:
        return 0

    return round(
        (value / total) * 100,
        decimals
    )


# ============================================================
# OVERVIEW
# ============================================================

def overview():

    products = read_csv("products.csv")
    customers = read_csv("customers.csv")
    orders = read_csv("orders.csv")

    # Only completed orders contribute to sales revenue.
    completed_orders = [
        o for o in orders
        if o.get("status", "").lower() == "completed"
    ]

    returned_orders = [
        o for o in orders
        if o.get("status", "").lower() == "returned"
    ]

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue = sum(
        to_float(o.get("revenue"))
        for o in completed_orders
    )

    # --------------------------------------------------------
    # UNITS
    # --------------------------------------------------------

    units = sum(
        to_int(o.get("quantity"))
        for o in completed_orders
    )

    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    order_count = len(completed_orders)

    # --------------------------------------------------------
    # AVERAGE ORDER VALUE
    # --------------------------------------------------------

    aov = (
        revenue / order_count
        if order_count > 0
        else 0
    )

    # --------------------------------------------------------
    # REPEAT CUSTOMERS
    # --------------------------------------------------------

    repeat_customers = sum(
        1
        for c in customers
        if to_int(c.get("orders")) > 1
    )

    repeat_rate = percentage(
        repeat_customers,
        len(customers),
        1
    )

    # --------------------------------------------------------
    # RETURNS
    # --------------------------------------------------------

    total_returns = sum(
        to_int(p.get("returns"))
        for p in products
    )

    return_rate = percentage(
        total_returns,
        units,
        1
    )

    # --------------------------------------------------------
    # PROFIT
    # --------------------------------------------------------

    profit = 0

    for product in products:

        price = to_float(
            product.get("price")
        )

        cost = to_float(
            product.get("cost")
        )

        units_sold = to_int(
            product.get("units_sold")
        )

        profit += (
            (price - cost)
            * units_sold
        )

    # --------------------------------------------------------
    # GROWTH
    # --------------------------------------------------------

    growth = calculate_growth(
        completed_orders
    )

    return {
        "revenue": round(revenue, 2),
        "orders": order_count,
        "aov": round(aov, 2),
        "units": units,
        "customers": len(customers),
        "products": len(products),
        "repeat_rate": repeat_rate,
        "return_rate": return_rate,
        "profit": round(profit, 2),
        "growth": growth,
        "returned_orders": len(returned_orders),
        "comparison": period_comparison(orders, days=30)
    }


# ============================================================
# PERIOD-OVER-PERIOD COMPARISON (real dates, not illustrative)
# ============================================================
#
# Compares the most recent `days`-day window in the dataset
# against the immediately preceding window of the same length,
# anchored to the latest order_date present in the data (since
# this is historical/demo data rather than live data ending
# "today"). Every value here is derived from orders.csv — none
# of it is a hardcoded/illustrative percentage.
#
# If a metric can't be honestly computed (e.g. no orders in the
# previous window, so percentage growth would be undefined),
# the field is returned as None so the frontend can show
# "Not enough data" instead of fabricating a number.
# ============================================================

def _parse_dates(orders):
    parsed = []
    for o in orders:
        try:
            parsed.append((date.fromisoformat(o["order_date"]), o))
        except (ValueError, KeyError, TypeError):
            continue
    return parsed


def _period_stats(rows):
    completed = [o for o in rows if o.get("status", "").lower() == "completed"]
    revenue = sum(to_float(o.get("revenue")) for o in completed)
    order_count = len(completed)
    aov = revenue / order_count if order_count else 0

    customer_orders = defaultdict(int)
    for o in completed:
        cid = o.get("customer_id")
        if cid:
            customer_orders[cid] += 1
    repeat_customers = sum(1 for c, n in customer_orders.items() if n > 1)
    total_customers_in_period = len(customer_orders)
    repeat_rate = percentage(repeat_customers, total_customers_in_period, 1)

    return {
        "revenue": round(revenue, 2),
        "orders": order_count,
        "aov": round(aov, 2),
        "repeat_rate": repeat_rate,
    }


def _pct_change(current, previous):
    if previous in (0, None):
        return None
    return round(((current - previous) / previous) * 100, 1)


def period_comparison(orders, days=30):
    parsed = _parse_dates(orders)

    if not parsed:
        return {
            "period_days": days,
            "note": "Not enough data to calculate period comparison.",
        }

    latest = max(d for d, _ in parsed)
    current_start = latest - timedelta(days=days - 1)
    previous_start = current_start - timedelta(days=days)
    previous_end = current_start - timedelta(days=1)

    current_rows = [o for d, o in parsed if current_start <= d <= latest]
    previous_rows = [o for d, o in parsed if previous_start <= d <= previous_end]

    current_stats = _period_stats(current_rows)
    previous_stats = _period_stats(previous_rows)

    if not previous_rows:
        note = "Not enough historical data before this period to calculate change."
    else:
        note = None

    metrics_out = {}
    for key in ("revenue", "orders", "aov", "repeat_rate"):
        metrics_out[key] = {
            "value": current_stats[key],
            "previous_value": previous_stats[key],
            "change_pct": _pct_change(current_stats[key], previous_stats[key]),
        }

    return {
        "period_days": days,
        "current_period": {"start": str(current_start), "end": str(latest)},
        "previous_period": {"start": str(previous_start), "end": str(previous_end)},
        "metrics": metrics_out,
        "note": note,
    }


# ============================================================
# SALES GROWTH
# ============================================================

def calculate_growth(orders):

    if not orders:
        return 0

    dates = []

    for order in orders:

        try:
            dates.append(
                date.fromisoformat(
                    order["order_date"]
                )
            )
        except (ValueError, KeyError):
            continue

    if not dates:
        return 0

    minimum_date = min(dates)
    maximum_date = max(dates)

    total_days = (
        maximum_date - minimum_date
    ).days

    if total_days <= 1:
        return 0

    midpoint = (
        minimum_date +
        (
            maximum_date - minimum_date
        ) / 2
    )

    first_period_revenue = 0
    second_period_revenue = 0

    for order in orders:

        try:
            order_date = date.fromisoformat(
                order["order_date"]
            )
        except (ValueError, KeyError):
            continue

        revenue = to_float(
            order.get("revenue")
        )

        if order_date <= midpoint:
            first_period_revenue += revenue
        else:
            second_period_revenue += revenue

    if first_period_revenue == 0:
        return 0

    growth = (
        (
            second_period_revenue
            - first_period_revenue
        )
        / first_period_revenue
    ) * 100

    return round(growth, 1)


# ============================================================
# PRODUCT INTELLIGENCE
# ============================================================

def product_metrics():

    products = read_csv("products.csv")

    out = []

    for p in products:

        # ----------------------------------------------------
        # BASIC VALUES
        # ----------------------------------------------------

        views = to_int(
            p.get("views")
        )

        add_to_cart = to_int(
            p.get("add_to_cart")
        )

        checkout = to_int(
            p.get("checkout")
        )

        units = to_int(
            p.get("units_sold")
        )

        returns = to_int(
            p.get("returns")
        )

        price = to_float(
            p.get("price")
        )

        cost = to_float(
            p.get("cost")
        )

        rating = to_float(
            p.get("rating")
        )

        # ----------------------------------------------------
        # REVENUE
        # ----------------------------------------------------

        revenue = (
            units * price
        )

        # ----------------------------------------------------
        # PROFIT / MARGIN
        # ----------------------------------------------------

        profit = (
            (price - cost)
            * units
        )

        margin = percentage(
            profit,
            revenue
        )

        # ----------------------------------------------------
        # CONVERSION
        # ----------------------------------------------------

        conversion = percentage(
            units,
            views
        )

        # ----------------------------------------------------
        # CART RATE
        # ----------------------------------------------------

        cart_rate = percentage(
            add_to_cart,
            views
        )

        # ----------------------------------------------------
        # CHECKOUT RATE
        # ----------------------------------------------------

        checkout_rate = percentage(
            checkout,
            add_to_cart
        )

        # ----------------------------------------------------
        # CHECKOUT TO PURCHASE
        # ----------------------------------------------------

        purchase_rate = percentage(
            units,
            checkout
        )

        # ----------------------------------------------------
        # RETURN RATE
        # ----------------------------------------------------

        return_rate = percentage(
            returns,
            units
        )

        out.append({

            "product_id":
                p.get("product_id", ""),

            "product_name":
                p.get("product_name", ""),

            "category":
                p.get("category", ""),

            "price":
                price,

            "cost":
                cost,

            "views":
                views,

            "add_to_cart":
                add_to_cart,

            "checkout":
                checkout,

            "units_sold":
                units,

            "returns":
                returns,

            "rating":
                rating,

            "revenue":
                round(
                    revenue,
                    2
                ),

            "profit":
                round(
                    profit,
                    2
                ),

            "margin":
                round(
                    margin,
                    2
                ),

            "conversion":
                round(
                    conversion,
                    2
                ),

            "cart_rate":
                round(
                    cart_rate,
                    2
                ),

            "checkout_rate":
                round(
                    checkout_rate,
                    2
                ),

            "purchase_from_checkout":
                round(
                    purchase_rate,
                    2
                ),

            "return_rate":
                round(
                    return_rate,
                    2
                )
        })

    return out


# ============================================================
# PRODUCT SUMMARY
# ============================================================

def product_summary():

    products = product_metrics()

    if not products:
        return {}

    best_seller = max(
        products,
        key=lambda x: x["units_sold"]
    )

    highest_revenue = max(
        products,
        key=lambda x: x["revenue"]
    )

    highest_profit = max(
        products,
        key=lambda x: x["profit"]
    )

    lowest_conversion = min(
        products,
        key=lambda x: x["conversion"]
    )

    highest_return_rate = max(
        products,
        key=lambda x: x["return_rate"]
    )

    highest_rating = max(
        products,
        key=lambda x: x["rating"]
    )

    return {
        "best_seller": best_seller,
        "highest_revenue": highest_revenue,
        "highest_profit": highest_profit,
        "lowest_conversion": lowest_conversion,
        "highest_returns": highest_return_rate,
        "highest_rating": highest_rating
    }


# ============================================================
# CUSTOMER SEGMENTATION
# ============================================================

def determine_segment(customer):

    orders = to_int(
        customer.get("orders")
    )

    spend = to_float(
        customer.get("total_spend")
    )

    days = to_int(
        customer.get("last_order_days")
    )

    # --------------------------------------------------------
    # AT RISK
    # --------------------------------------------------------

    if days >= 61 and spend >= 6000:
        return "At Risk"

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    if orders >= 8 and spend >= 35000:
        return "VIP"

    # --------------------------------------------------------
    # LOYAL
    # --------------------------------------------------------

    if orders >= 4:
        return "Loyal"

    # --------------------------------------------------------
    # RETURNING
    # --------------------------------------------------------

    if orders >= 2:
        return "Returning"

    # --------------------------------------------------------
    # NEW
    # --------------------------------------------------------

    return "New"


# ============================================================
# CUSTOMER INTELLIGENCE
# ============================================================

def customer_segments():

    customers = read_csv(
        "customers.csv"
    )

    counts = defaultdict(int)
    spend = defaultdict(float)

    segmented_customers = []

    for c in customers:

        segment = determine_segment(c)

        customer = {

            "customer_id":
                c.get(
                    "customer_id",
                    ""
                ),

            "customer_name":
                c.get(
                    "customer_name",
                    ""
                ),

            "city":
                c.get(
                    "city",
                    ""
                ),

            "orders":
                to_int(
                    c.get("orders")
                ),

            "total_spend":
                to_float(
                    c.get("total_spend")
                ),

            "last_order_days":
                to_int(
                    c.get("last_order_days")
                ),

            "first_order_date":
                c.get(
                    "first_order_date",
                    ""
                ),

            "last_order_date":
                c.get(
                    "last_order_date",
                    ""
                ),

            "segment":
                segment
        }

        segmented_customers.append(
            customer
        )

        counts[segment] += 1

        spend[segment] += (
            customer["total_spend"]
        )

    return {
        "counts": dict(counts),

        "spend": {
            key: round(
                value,
                2
            )
            for key, value in spend.items()
        },

        "customers":
            segmented_customers
    }


# ============================================================
# CUSTOMER SUMMARY
# ============================================================

def customer_summary():

    data = customer_segments()

    customers = data["customers"]

    if not customers:
        return {}

    top_customer = max(
        customers,
        key=lambda x: x["total_spend"]
    )

    at_risk = [
        c for c in customers
        if c["segment"] == "At Risk"
    ]

    vip = [
        c for c in customers
        if c["segment"] == "VIP"
    ]

    loyal = [
        c for c in customers
        if c["segment"] == "Loyal"
    ]

    returning = [
        c for c in customers
        if c["segment"] == "Returning"
    ]

    new_customers = [
        c for c in customers
        if c["segment"] == "New"
    ]

    return {

        "top_customer":
            top_customer,

        "at_risk_count":
            len(at_risk),

        "vip_count":
            len(vip),

        "loyal_count":
            len(loyal),

        "returning_count":
            len(returning),

        "new_count":
            len(new_customers)
    }


# ============================================================
# FUNNEL ANALYTICS
# ============================================================

def funnel():

    products = read_csv(
        "products.csv"
    )

    # --------------------------------------------------------
    # TOTAL FUNNEL VALUES
    # --------------------------------------------------------

    total_views = sum(
        to_int(
            p.get("views")
        )
        for p in products
    )

    total_cart = sum(
        to_int(
            p.get("add_to_cart")
        )
        for p in products
    )

    total_checkout = sum(
        to_int(
            p.get("checkout")
        )
        for p in products
    )

    total_purchase = sum(
        to_int(
            p.get("units_sold")
        )
        for p in products
    )

    # --------------------------------------------------------
    # CONVERSION RATES
    # --------------------------------------------------------

    view_to_cart = percentage(
        total_cart,
        total_views
    )

    cart_to_checkout = percentage(
        total_checkout,
        total_cart
    )

    checkout_to_purchase = percentage(
        total_purchase,
        total_checkout
    )

    overall_conversion = percentage(
        total_purchase,
        total_views
    )

    # --------------------------------------------------------
    # DROPOFFS
    # --------------------------------------------------------

    dropoffs = {

        "view_to_cart":
            round(
                100 - view_to_cart,
                2
            ),

        "cart_to_checkout":
            round(
                100 - cart_to_checkout,
                2
            ),

        "checkout_to_purchase":
            round(
                100 - checkout_to_purchase,
                2
            )
    }

    return {

        "stages": [

            {
                "name":
                    "Product Views",

                "value":
                    total_views
            },

            {
                "name":
                    "Add to Cart",

                "value":
                    total_cart
            },

            {
                "name":
                    "Checkout",

                "value":
                    total_checkout
            },

            {
                "name":
                    "Purchase",

                "value":
                    total_purchase
            }
        ],

        "conversion_rates": {

            "view_to_cart":
                round(
                    view_to_cart,
                    2
                ),

            "cart_to_checkout":
                round(
                    cart_to_checkout,
                    2
                ),

            "checkout_to_purchase":
                round(
                    checkout_to_purchase,
                    2
                ),

            "overall_conversion":
                round(
                    overall_conversion,
                    2
                )
        },

        "dropoffs":
            dropoffs
    }


# ============================================================
# RETENTION ANALYTICS
# ============================================================

def retention():

    customers = read_csv(
        "customers.csv"
    )

    total_customers = len(
        customers
    )

    if total_customers == 0:
        return {
            "repeat_rate": 0,
            "repeat_customers": 0,
            "total_customers": 0,
            "cohorts": []
        }

    repeat_customers = sum(
        1
        for c in customers
        if to_int(
            c.get("orders")
        ) > 1
    )

    repeat_rate = percentage(
        repeat_customers,
        total_customers,
        1
    )

    purchase_1 = sum(
        1
        for c in customers
        if to_int(
            c.get("orders")
        ) >= 1
    )

    purchase_2 = sum(
        1
        for c in customers
        if to_int(
            c.get("orders")
        ) >= 2
    )

    purchase_3 = sum(
        1
        for c in customers
        if to_int(
            c.get("orders")
        ) >= 3
    )

    purchase_4 = sum(
        1
        for c in customers
        if to_int(
            c.get("orders")
        ) >= 4
    )

    cohorts = [

        {
            "period":
                "Purchase 1",

            "customers":
                purchase_1,

            "retention":
                100
        },

        {
            "period":
                "Purchase 2",

            "customers":
                purchase_2,

            "retention":
                percentage(
                    purchase_2,
                    purchase_1,
                    1
                )
        },

        {
            "period":
                "Purchase 3",

            "customers":
                purchase_3,

            "retention":
                percentage(
                    purchase_3,
                    purchase_1,
                    1
                )
        },

        {
            "period":
                "Purchase 4+",

            "customers":
                purchase_4,

            "retention":
                percentage(
                    purchase_4,
                    purchase_1,
                    1
                )
        }
    ]

    return {

        "repeat_rate":
            repeat_rate,

        "repeat_customers":
            repeat_customers,

        "total_customers":
            total_customers,

        "cohorts":
            cohorts
    }


# ============================================================
# CATEGORY ANALYTICS
# ============================================================

def category_metrics():

    products = product_metrics()

    categories = defaultdict(
        lambda: {
            "products": 0,
            "views": 0,
            "add_to_cart": 0,
            "checkout": 0,
            "units": 0,
            "revenue": 0,
            "profit": 0,
            "returns": 0
        }
    )

    for product in products:

        category = product[
            "category"
        ]

        categories[category][
            "products"
        ] += 1

        categories[category][
            "views"
        ] += product[
            "views"
        ]

        categories[category][
            "add_to_cart"
        ] += product[
            "add_to_cart"
        ]

        categories[category][
            "checkout"
        ] += product[
            "checkout"
        ]

        categories[category][
            "units"
        ] += product[
            "units_sold"
        ]

        categories[category][
            "revenue"
        ] += product[
            "revenue"
        ]

        categories[category][
            "profit"
        ] += product[
            "profit"
        ]

        categories[category][
            "returns"
        ] += product[
            "returns"
        ]

    result = []

    for category, values in categories.items():

        result.append({

            "category":
                category,

            "products":
                values["products"],

            "views":
                values["views"],

            "add_to_cart":
                values["add_to_cart"],

            "checkout":
                values["checkout"],

            "units_sold":
                values["units"],

            "revenue":
                round(
                    values["revenue"],
                    2
                ),

            "profit":
                round(
                    values["profit"],
                    2
                ),

            "conversion":
                percentage(
                    values["units"],
                    values["views"]
                ),

            "return_rate":
                percentage(
                    values["returns"],
                    values["units"]
                )
        })

    return sorted(
        result,
        key=lambda x: x["revenue"],
        reverse=True
    )


# ============================================================
# SALES TREND
# ============================================================

def sales_trend():

    orders = read_csv(
        "orders.csv"
    )

    daily = defaultdict(
        lambda: {
            "revenue": 0,
            "orders": 0,
            "units": 0
        }
    )

    for order in orders:

        if order.get(
            "status",
            ""
        ).lower() != "completed":
            continue

        order_date = order.get(
            "order_date",
            ""
        )

        daily[order_date][
            "revenue"
        ] += to_float(
            order.get("revenue")
        )

        daily[order_date][
            "orders"
        ] += 1

        daily[order_date][
            "units"
        ] += to_int(
            order.get("quantity")
        )

    result = []

    for order_date in sorted(
        daily.keys()
    ):

        result.append({

            "date":
                order_date,

            "revenue":
                round(
                    daily[order_date][
                        "revenue"
                    ],
                    2
                ),

            "orders":
                daily[order_date][
                    "orders"
                ],

            "units":
                daily[order_date][
                    "units"
                ]
        })

    return result


# ============================================================
# BUSINESS OPPORTUNITIES
# ============================================================

def business_opportunities():

    products = product_metrics()

    opportunities = []

    for product in products:

        # ----------------------------------------------------
        # HIGH TRAFFIC / LOW CONVERSION
        # ----------------------------------------------------

        if (
            product["views"] >= 30000
            and product["conversion"] < 3
        ):

            opportunities.append({

                "type":
                    "conversion",

                "priority":
                    "High",

                "product":
                    product["product_name"],

                "title":
                    "High Traffic, Low Conversion",

                "detail":
                    (
                        f'{product["product_name"]} has '
                        f'{product["views"]:,} views but only '
                        f'{product["conversion"]}% purchase '
                        f'conversion.'
                    ),

                "action":
                    (
                        "Investigate pricing, reviews, "
                        "product content, availability "
                        "and checkout experience."
                    )
            })

        # ----------------------------------------------------
        # HIGH RETURN RATE
        # ----------------------------------------------------

        if product["return_rate"] >= 5:

            opportunities.append({

                "type":
                    "returns",

                "priority":
                    "High",

                "product":
                    product["product_name"],

                "title":
                    "High Return Rate",

                "detail":
                    (
                        f'{product["product_name"]} has a '
                        f'{product["return_rate"]}% return rate.'
                    ),

                "action":
                    (
                        "Investigate product quality, "
                        "description accuracy, sizing "
                        "and customer expectations."
                    )
            })

        # ----------------------------------------------------
        # HIGH MARGIN
        # ----------------------------------------------------

        if (
            product["margin"] >= 45
            and product["conversion"] >= 4
        ):

            opportunities.append({

                "type":
                    "profit",

                "priority":
                    "Medium",

                "product":
                    product["product_name"],

                "title":
                    "Strong Profit Opportunity",

                "detail":
                    (
                        f'{product["product_name"]} combines '
                        f'{product["conversion"]}% conversion '
                        f'with a {product["margin"]}% margin.'
                    ),

                "action":
                    (
                        "Consider prioritizing this product "
                        "in marketing and promotional campaigns."
                    )
            })

    # --------------------------------------------------------
    # FUNNEL OPPORTUNITY
    # --------------------------------------------------------

    funnel_data = funnel()

    rates = funnel_data[
        "conversion_rates"
    ]

    if rates["checkout_to_purchase"] < 70:

        opportunities.append({

            "type":
                "funnel",

            "priority":
                "High",

            "product":
                "",

            "title":
                "Checkout Drop-off Detected",

            "detail":
                (
                    "A significant portion of customers "
                    "reaching checkout do not complete "
                    "their purchase."
                ),

            "action":
                (
                    "Investigate shipping costs, payment "
                    "experience, checkout friction and "
                    "trust signals."
                )
        })

    # --------------------------------------------------------
    # CUSTOMER RETENTION OPPORTUNITY
    # --------------------------------------------------------

    customer_data = customer_segments()

    at_risk_count = customer_data[
        "counts"
    ].get(
        "At Risk",
        0
    )

    if at_risk_count > 0:

        opportunities.append({

            "type":
                "retention",

            "priority":
                "Medium",

            "product":
                "",

            "title":
                "Customers at Risk",

            "detail":
                (
                    f'{at_risk_count} valuable customers '
                    "appear to be becoming inactive."
                ),

            "action":
                (
                    "Consider targeted reactivation "
                    "campaigns and personalized offers."
                )
        })

    return opportunities


# ============================================================
# COMPLETE ANALYTICS SUMMARY
# ============================================================

def analytics_summary():

    return {

        "overview":
            overview(),

        "products":
            product_summary(),

        "customers":
            customer_summary(),

        "funnel":
            funnel(),

        "retention":
            retention(),

        "categories":
            category_metrics(),

        "sales_trend":
            sales_trend(),

        "opportunities":
            business_opportunities()
    }