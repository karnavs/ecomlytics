
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from analytics.metrics import overview, product_metrics, customer_segments, funnel
from insights.engine import generate_insights

app = FastAPI(title="Ecomlytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = Path(__file__).resolve().parents[1]

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login.html", status_code=302)

@app.get("/api/overview")
def get_overview():
    return overview()

@app.get("/api/products")
def get_products():
    return product_metrics()

@app.get("/api/customers/segments")
def get_segments():
    return customer_segments()

@app.get("/api/funnel")
def get_funnel():
    return funnel()

@app.get("/api/insights")
def get_insights():
    return generate_insights()

@app.get("/api/health")
def health():
    return {"status": "ok", "platform": "Ecomlytics"}

app.mount("/", StaticFiles(directory=str(BASE / "frontend"), html=True), name="frontend")
