# EnterpriseIQ

Enterprise Analytics & Decision Intelligence Platform

A student portfolio project featuring a Flask/SQLite analytics backend and a static GitHub Pages showcase.

## Features
- Revenue, profit and regional sales analysis
- CSV import and data validation
- Basic next-month revenue projection
- JSON API, interactive web dashboard, CSV exports
- Synthetic sample data for demonstration

## Technologies
Python, Flask, SQLite, Pandas, JavaScript, HTML/CSS

## Live showcase
GitHub Pages hosts a **static sample-data demonstration**, not the running Flask backend. To use the full application, run it locally.

## Run locally
```bash
python -m pip install -r requirements.txt
python seed.py
python app.py
```
Then visit http://127.0.0.1:5000 .

## Tests
```bash
python -m pytest -q
```

## Status
Portfolio prototype using synthetic data. Validate backend installation and tests before claiming production readiness. No real company data is included.
