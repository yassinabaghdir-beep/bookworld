import os
import sqlite3
import pandas as pd
from flask import Flask, jsonify, request
from dotenv import load_dotenv
load_dotenv(override=True)

API_KEY = os.environ["API_KEY"]
DB_PATH = "bookworld_final.db"

app = Flask(__name__)

@app.route("/health")
def health():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify(error="Cle API invalide ou absente"), 401
    return jsonify(status="ok")

@app.route("/sales-by-country")
def sales_by_country():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify(error="Cle API invalide ou absente"), 401

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM sales_by_country ORDER BY total_revenue_eur DESC", conn)
    conn.close()
    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)