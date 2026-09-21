# Ecomlytics — E-commerce Product Intelligence & Decision Platform

A professional multi-page e-commerce analytics application connecting store data to metrics, customer/product intelligence, funnel analysis and business insights.

## Features
- Professional login page with demo authentication
- Overview dashboard
- Sales Analytics
- Product Intelligence with search and category filter
- Customer Intelligence and segmentation
- Retention & Funnel analytics
- Business Insights and recommended actions
- FastAPI backend
- CSV demo datasets
- Responsive professional UI
- Linked navigation and sign-out

## Project structure
The application entry point is `app.py` in the project root. The frontend is inside `frontend/`.

## Run on Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:

`http://127.0.0.1:8000/`

The root URL redirects to `/login.html`.

Demo login: any valid email address + any password.

## API endpoints

- `/api/overview`
- `/api/products`
- `/api/customers/segments`
- `/api/funnel`
- `/api/insights`
- `/api/health`

## Production note
The login is intentionally demo-only. For production, use server-side authentication, hashed passwords, sessions/JWT, HTTPS, database-backed users, CSRF protection and proper authorization.
