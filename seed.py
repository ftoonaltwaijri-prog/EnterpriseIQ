import csv, os
from app import init_db, connect, validate, BASE
init_db()
with open(os.path.join(BASE,"data","sample_sales.csv"),encoding="utf-8") as f:
    rows=[validate(r) for r in csv.DictReader(f)]
with connect() as c:
    c.executemany("INSERT OR IGNORE INTO sales(order_id,date,region,category,product,quantity,unit_price,unit_cost) VALUES (?,?,?,?,?,?,?,?)", rows)
print("Seeded synthetic sample data.")
