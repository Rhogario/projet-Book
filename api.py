from flask import Flask, jsonify, request, abort
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
token = os.getenv("API_TOKEN", "secret123")


def run_query(query):
    conn = sqlite3.connect("projet_final_database.db")
    df = pd.read_sql_query(query, conn)
    return df

if not os.path.isfile("projet_final_database.db"):
    raise FileNotFoundError("Il n'existe pas de projet_final_database.db, avez-vous pensé à run la pipeline ?")


@app.before_request
def check_key():
    if request.args.get("token") != token :
        abort(401)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/sales_by_country", methods=["GET"])
def get_sales_by_country():
    query = """
    SELECT *
    FROM sales_by_country
    """
    df = run_query(query)
    return jsonify(df.to_dict(orient="records"))

@app.route("/sales", methods=["GET"])
def get_sales():
    query = """
    SELECT *
    FROM sales
    """
    df = run_query(query)
    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=False)