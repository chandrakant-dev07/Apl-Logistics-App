# APL Logistics Profitability Dashboard

Interactive Streamlit dashboard for the Customer, Product & Profitability Performance Analysis (Unified Mentor Project 7518).

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Contents

- `app.py` — Main Streamlit application (4 tabs: Revenue & Profit Overview, Customer Value Dashboard, Product & Category Performance, Discount Impact Analyzer)
- `data.parquet` — Cleaned, analysis-ready dataset (180,519 order line items)
- `requirements.txt` — Python dependencies

## Features

- Global filters: Customer Segment, Market, Order Region, Category, Discount Rate range
- Profit waterfall, customer value tiers, discount-margin diagnostics, shipping reliability
- "What-If" discount scenario simulator
- Full data tables with CSV-style formatting

## Deploying

This app can be deployed for free on [Streamlit Community Cloud](https://streamlit.io/cloud):
1. Push this folder to a GitHub repository
2. Connect the repo at share.streamlit.io
3. Set the main file path to `app.py`
