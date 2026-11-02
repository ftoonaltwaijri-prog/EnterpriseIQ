import csv, io, os, sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template, request, Response

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("ANALYTICS_DB", os.path.join(BASE, "analytics.db"))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
SCHEMA = """CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT UNIQUE NOT NULL, date TEXT NOT NULL, region TEXT NOT NULL, category TEXT NOT NULL, product TEXT NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL, unit_cost REAL NOT NULL)"""

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c: c.execute(SCHEMA)

def validate(row):
    required = ("order_id", "date", "region", "category", "product", "quantity", "unit_price", "unit_cost")
    if any(not str(row.get(k, "")).strip() for k in required): raise ValueError("Missing required field")
    datetime.strptime(row["date"], "%Y-%m-%d")
    q, p, cost = int(row["quantity"]), float(row["unit_price"]), float(row["unit_cost"])
    if q <= 0 or p < 0 or cost < 0: raise ValueError("Invalid numeric value")
    return (row["order_id"].strip(), row["date"], row["region"].strip(), row["category"].strip(), row["product"].strip(), q, p, cost)

@app.route("/")
def home(): return render_template("index.html")

@app.route("/api/summary")
def summary():
    with connect() as c:
        totals = dict(c.execute("SELECT COUNT(*) orders, COALESCE(SUM(quantity*unit_price),0) revenue, COALESCE(SUM(quantity*(unit_price-unit_cost)),0) profit, COALESCE(SUM(quantity),0) units FROM sales").fetchone())
        monthly = [dict(r) for r in c.execute("SELECT substr(date,1,7) month, ROUND(SUM(quantity*unit_price),2) revenue, ROUND(SUM(quantity*(unit_price-unit_cost)),2) profit FROM sales GROUP BY substr(date,1,7) ORDER BY month")]
        regions = [dict(r) for r in c.execute("SELECT region, ROUND(SUM(quantity*unit_price),2) revenue FROM sales GROUP BY region ORDER BY revenue DESC")]
        categories = [dict(r) for r in c.execute("SELECT category, ROUND(SUM(quantity*unit_price),2) revenue, ROUND(SUM(quantity*(unit_price-unit_cost)),2) profit FROM sales GROUP BY category ORDER BY revenue DESC")]
        products = [dict(r) for r in c.execute("SELECT product, ROUND(SUM(quantity*(unit_price-unit_cost)),2) profit FROM sales GROUP BY product ORDER BY profit DESC LIMIT 5")]
        recent = [dict(r) for r in c.execute("SELECT order_id,date,region,product,quantity,ROUND(quantity*unit_price,2) revenue FROM sales ORDER BY date DESC, id DESC LIMIT 10")]
    totals["margin_pct"] = round(100*totals["profit"]/totals["revenue"],2) if totals["revenue"] else 0
    return jsonify(totals=totals, monthly=monthly, regions=regions, categories=categories, top_products=products, recent=recent)

@app.route("/api/forecast")
def forecast():
    with connect() as c:
        rows=c.execute("SELECT substr(date,1,7) month, SUM(quantity*unit_price) revenue FROM sales GROUP BY substr(date,1,7) ORDER BY month").fetchall()
    vals=[r["revenue"] for r in rows]
    return jsonify(method="3-month trailing average baseline", estimated_next_month_revenue=round(sum(vals[-3:])/min(len(vals),3),2) if vals else 0, months_used=min(len(vals),3), note="Illustrative baseline; not a validated production forecast.")

@app.route("/api/upload", methods=["POST"])
def upload():
    f=request.files.get("file")
    if not f or not f.filename.lower().endswith(".csv"): return jsonify(error="Upload a .csv file"),400
    try:
        reader=csv.DictReader(io.StringIO(f.read().decode("utf-8-sig")))
        required={"order_id","date","region","category","product","quantity","unit_price","unit_cost"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames): return jsonify(error="Missing CSV columns"),400
        rows=[validate(row) for row in reader]
        if len(rows)>20000: return jsonify(error="Maximum 20,000 rows"),400
        if len(set(r[0] for r in rows))!=len(rows): return jsonify(error="Duplicate order ID"),400
        with connect() as c: c.executemany("INSERT INTO sales(order_id,date,region,category,product,quantity,unit_price,unit_cost) VALUES (?,?,?,?,?,?,?,?)",rows)
        return jsonify(imported=len(rows))
    except (ValueError,UnicodeError,sqlite3.IntegrityError) as e: return jsonify(error=str(e)),400

@app.route("/api/export")
def export():
    with connect() as c: rows=c.execute("SELECT order_id,date,region,category,product,quantity,unit_price,unit_cost FROM sales ORDER BY date").fetchall()
    out=io.StringIO(); w=csv.writer(out); w.writerow(["order_id","date","region","category","product","quantity","unit_price","unit_cost"]); w.writerows([tuple(r) for r in rows])
    return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=sales_export.csv"})

if __name__=="__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG")=="1")
