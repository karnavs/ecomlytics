
from analytics.metrics import product_metrics, customer_segments, overview, funnel

def generate_insights():
    products = product_metrics()
    high_traffic = max(products, key=lambda x: x["views"])
    low_conversion = min(products, key=lambda x: x["conversion"])
    high_return = max(products, key=lambda x: x["return_rate"])
    segments = customer_segments()["counts"]
    return [
        {
            "type": "conversion",
            "priority": "High",
            "title": f"{low_conversion['product_name']} needs conversion investigation",
            "detail": f"It has {low_conversion['views']:,} views but only {low_conversion['conversion']}% purchase conversion.",
            "action": "Review pricing, product content, reviews, stock availability and checkout friction."
        },
        {
            "type": "traffic",
            "priority": "Medium",
            "title": f"{high_traffic['product_name']} attracts strong traffic",
            "detail": f"{high_traffic['views']:,} product views indicate strong customer interest.",
            "action": "Test stronger offers and landing-page improvements to turn traffic into purchases."
        },
        {
            "type": "returns",
            "priority": "Medium",
            "title": f"{high_return['product_name']} has elevated returns",
            "detail": f"Return rate is {high_return['return_rate']}% based on the product dataset.",
            "action": "Investigate sizing, product expectations, quality feedback and delivery issues."
        },
        {
            "type": "retention",
            "priority": "High",
            "title": f"{segments.get('At Risk', 0)} customers are currently at risk",
            "detail": "Customers with declining recency can reduce future revenue if not re-engaged.",
            "action": "Create targeted win-back campaigns and personalized product recommendations."
        }
    ]
