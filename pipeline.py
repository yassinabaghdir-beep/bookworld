"""Pipeline ETL BookWorld : extraction, transformation et chargement des ventes."""

import re
import sqlite3

import pandas as pd
import requests
from bs4 import BeautifulSoup

SALES_PATH = "sales_raw.csv"
REF_DB_PATH = "bookworld_reference.db"
FINAL_DB_PATH = "bookworld_final.db"
SCHEMA_PATH = "schema_final.sql"

BOOKS_URL = "https://books.toscrape.com/"
FRANKFURTER_URL = "https://api.frankfurter.app"


def extract():
    """Extraction des ventes, des référentiels, des prix des livres et des taux de change."""
    # --- Ventes (CSV) ---
    try:
        df_sales = pd.read_csv(SALES_PATH)
    except FileNotFoundError as e:
        raise RuntimeError(f"Fichier sales_raw.csv introuvable : {e}")
    print("Ventes :", df_sales.shape)

    # --- Référentiels (SQLite) ---
    try:
        conn = sqlite3.connect(REF_DB_PATH)
        countries = pd.read_sql("SELECT * FROM countries", conn)
        channels = pd.read_sql("SELECT * FROM channels", conn)
        category_rules = pd.read_sql("SELECT * FROM category_rules", conn)
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Erreur lecture bookworld_reference.db : {e}")
    print("Pays :", countries.shape)

    # --- Prix des livres (scraping) ---
    try:
        resp = requests.get(BOOKS_URL, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Erreur lors du scraping : {e}")
    soup = BeautifulSoup(resp.content, "html.parser")
    books = []
    for art in soup.select("article.product_pod"):
        title = art.h3.a.get("title")
        price_txt = art.select_one("p.price_color").text
        price = float(re.search(r"[\d.]+", price_txt).group())
        books.append({"title": title, "price_gbp": price})
    df_books = pd.DataFrame(books)
    print("Livres scrapés :", len(df_books))

    # --- Taux GBP -> EUR (API Frankfurter) ---
    debut = df_sales["order_date"].min()
    fin = df_sales["order_date"].max()
    url = f"{FRANKFURTER_URL}/{debut}..{fin}"
    params = {"from": "GBP", "to": "EUR"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Échec de l'appel à l'API Frankfurter : {e}")
    lignes = []
    for date, valeurs in data["rates"].items():
        lignes.append({"order_date": date, "taux_gbp_eur": valeurs["EUR"]})
    taux = pd.DataFrame(lignes)
    print("Taux récupérés :", len(taux), "jours ouvrés")

    return df_sales, countries, channels, category_rules, df_books, taux


def transform(df_sales, countries, df_books, taux):
    """Enrichissement des ventes, conversion en EUR et agrégation par pays."""
    # --- Ajout des prix ---
    df_sales["book_name"] = df_sales["book_name"].str.strip()
    df_books["title"] = df_books["title"].str.strip()

    df = df_sales.merge(df_books, how="left", left_on="book_name", right_on="title")
    df = df.drop(columns="title")
    print("Après jointure prix :", df.shape, "| sans prix :", df["price_gbp"].isna().sum())

    # --- Chiffre d'affaires en GBP ---
    df["revenue_gbp"] = df["price_gbp"] * df["quantity"] * (1 - df["discount_rate"])

    # --- Conversion en EUR (dernier taux connu les jours non ouvrés) ---
    toutes_dates = pd.DataFrame({
        "order_date": pd.date_range(df["order_date"].min(), df["order_date"].max()).strftime("%Y-%m-%d")
    })
    taux = toutes_dates.merge(taux, how="left", on="order_date")
    taux["taux_gbp_eur"] = taux["taux_gbp_eur"].ffill()
    df = df.merge(taux, how="left", on="order_date")
    df["revenue_eur"] = df["revenue_gbp"] * df["taux_gbp_eur"]
    print("Ventes sans taux :", df["taux_gbp_eur"].isna().sum())

    # --- Ajout de NL et des noms de pays ---
    nl = pd.DataFrame([{"country_code": "NL", "country_name": "Netherlands", "currency_code": "EUR",
                        "vat_rate": 21.0, "region": "Europe", "is_active": None}])
    countries = pd.concat([countries, nl], ignore_index=True)

    df = df.merge(countries[["country_code", "country_name"]], how="left", on="country_code")
    print("Ventes sans pays :", df["country_name"].isna().sum())

    # --- Agrégation par pays ---
    sales_by_country = df.groupby(["country_code", "country_name"]).agg(
        total_orders=("order_id", "nunique"),
        total_quantity=("quantity", "sum"),
        total_revenue_gbp=("revenue_gbp", "sum"),
        total_revenue_eur=("revenue_eur", "sum"),
    ).reset_index()
    sales_by_country = sales_by_country.round(2)
    print("sales_by_country :", len(sales_by_country), "pays")

    # --- Pseudonymisation ---
    sales = df.drop(columns=["customer_first_name", "customer_last_name"])
    print("Colonnes de sales :", sales.columns.tolist())

    # --- Table books et nettoyage de sales ---
    books = sales[["book_id", "book_name", "price_gbp"]].drop_duplicates()
    sales = sales.drop(columns=["book_name", "country_name"])

    return sales, sales_by_country, countries, books


def load(sales, sales_by_country, countries, channels, books):
    """Création du schéma et chargement des tables dans bookworld_final.db."""
    try:
        conn = sqlite3.connect(FINAL_DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")

        # --- Création du schéma ---
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            conn.executescript(f.read())

        # --- Chargement des tables (dimensions puis faits) ---
        books.to_sql("books", conn, if_exists="append", index=False)
        countries.to_sql("countries", conn, if_exists="append", index=False)
        channels.to_sql("channels", conn, if_exists="append", index=False)
        sales.to_sql("sales", conn, if_exists="append", index=False)
        sales_by_country.to_sql("sales_by_country", conn, if_exists="append", index=False)
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement de la base finale : {e}")

    print("Base finale créée : bookworld_final.db")
    print("books :", len(books), "| countries :", len(countries), "| channels :", len(channels))
    print("sales :", len(sales), "| sales_by_country :", len(sales_by_country))


if __name__ == "__main__":
    df_sales, countries, channels, category_rules, df_books, taux = extract()
    sales, sales_by_country, countries, books = transform(df_sales, countries, df_books, taux)
    load(sales, sales_by_country, countries, channels, books)