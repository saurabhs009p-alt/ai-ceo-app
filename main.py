from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
from typing import Optional, List
import csv
import requests
import schedule
import time
import threading

print("NEW CODE RUNNING 🚀")

app = FastAPI()

# ---------- INPUT MODEL ----------
class ProductInput(BaseModel):
    name: str
    cost: float
    selling_price: float
    listings: int
    reviews: int
    demand: Optional[int] = None

# ---------- LOG FILE ----------
DATA_FILE = "data.json"

def save_log(data):
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

    with open(DATA_FILE, "r") as f:
        logs = json.load(f)

    logs.append(data)

    with open(DATA_FILE, "w") as f:
        json.dump(logs, f, indent=2)

# ---------- PRODUCT ENGINE ----------
def calculate_profit(cost, selling_price):
    return selling_price - cost

# ---------- COMPETITION ----------
def competition_score(listings, reviews, demand):
    score = (listings * 0.3) + (reviews * 0.2) - (demand * 0.5)
    return round(score, 2)

# ---------- DEMAND ----------
def get_demand_score(keyword: str):
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=330)

        pytrends.build_payload([keyword], timeframe='today 7-d')
        data = pytrends.interest_over_time()

        if data is None or data.empty or keyword not in data.columns:
            return 30

        return int(data[keyword].mean())

    except Exception:
        print("Trend fallback used")
        return 30

# ---------- SCORING ----------
def product_score(profit, demand, comp_score):
    profit_score = min(profit / 10, 50)
    demand_score = min(demand * 0.3, 30)
    comp_penalty = min(comp_score, 20)
    comp_score_final = 20 - comp_penalty

    return round(profit_score + demand_score + comp_score_final, 2)

# ---------- DECISION ----------
def decision_logic(profit, comp_score, score):
    if score > 70:
        return "SELL 🚀"
    elif score > 40:
        return "TEST ⚠️"
    else:
        return "REJECT ❌"

# ---------- CSV ----------
def load_products_from_csv():
    products = []

    with open("products.csv", "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            products.append(ProductInput(
                name=row["name"],
                cost=float(row["cost"]),
                selling_price=float(row["selling_price"]),
                listings=int(row["listings"]),
                reviews=int(row["reviews"])
            ))

    return products

# ---------- API ----------
def fetch_products_from_api():
    url = "https://fakestoreapi.com/products"
    response = requests.get(url)
    data = response.json()

    products = []

    for item in data[:5]:
        products.append(ProductInput(
            name=item["title"],
            cost=float(item["price"] * 0.6),
            selling_price=float(item["price"]),
            listings=100,
            reviews=int(item["rating"]["count"])
        ))

    return products
def run_scheduler():
    import schedule
    import time

    schedule.every(1).minutes.do(daily_job)  # test के लिए

    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------- AUTO JOB ----------
def daily_job():
    print("AUTO JOB RUNNING...")

    products = fetch_products_from_api()

    for product in products:
        demand = get_demand_score(product.name)

        profit = calculate_profit(product.cost, product.selling_price)
        comp = competition_score(product.listings, product.reviews, demand)

        score = product_score(profit, demand, comp)
        decision = decision_logic(profit, comp, score)

        result = {
            "product": product.name,
            "profit": profit,
            "competition_score": comp,
            "demand": demand,
            "score": score,
            "decision": decision
        }

        save_log(result)
def run_scheduler():
    import schedule
    import time

    schedule.every().day.at("10:00").do(daily_job)

    while True:
        schedule.run_pending()
        time.sleep(1)       

# ---------- ROUTES ----------
@app.on_event("startup")
def start_scheduler():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

@app.get("/")
def home():
    return {"message": "AI CEO Core Running 🚀"}

@app.post("/analyze")
def analyze(product: ProductInput):

    demand = product.demand if product.demand is not None else get_demand_score(product.name)

    profit = calculate_profit(product.cost, product.selling_price)
    comp = competition_score(product.listings, product.reviews, demand)

    score = product_score(profit, demand, comp)
    decision = decision_logic(profit, comp, score)

    result = {
        "product": product.name,
        "profit": profit,
        "competition_score": comp,
        "demand": demand,
        "score": score,
        "decision": decision
    }

    save_log(result)
    return result

@app.post("/analyze-bulk")
def analyze_bulk(products: List[ProductInput]):

    results = []

    for product in products:
        demand = product.demand if product.demand is not None else get_demand_score(product.name)

        profit = calculate_profit(product.cost, product.selling_price)
        comp = competition_score(product.listings, product.reviews, demand)

        score = product_score(profit, demand, comp)
        decision = decision_logic(profit, comp, score)

        results.append({
            "product": product.name,
            "score": score,
            "decision": decision
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "top_products": results[:3],
        "all_products": results
    }

@app.get("/auto-products")
def auto_products():

    products = load_products_from_csv()
    results = []

    for product in products:
        demand = get_demand_score(product.name)

        profit = calculate_profit(product.cost, product.selling_price)
        comp = competition_score(product.listings, product.reviews, demand)

        score = product_score(profit, demand, comp)
        decision = decision_logic(profit, comp, score)

        results.append({
            "product": product.name,
            "score": score,
            "decision": decision
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {"top_products": results[:3]}

@app.get("/auto-api-products")
def auto_api_products():

    products = fetch_products_from_api()
    results = []

    for product in products:
        demand = get_demand_score(product.name)

        profit = calculate_profit(product.cost, product.selling_price)
        comp = competition_score(product.listings, product.reviews, demand)

        score = product_score(profit, demand, comp)
        decision = decision_logic(profit, comp, score)

        results.append({
            "product": product.name,
            "profit": profit,
            "competition_score": comp,
            "demand": demand,
            "score": score,
            "decision": decision
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "top_products": results[:3],
        "all_products": results
    }

@app.get("/logs")
def logs():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)