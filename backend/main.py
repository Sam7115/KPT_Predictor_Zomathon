"""
ZOMATHON KPT Prediction System — FastAPI Backend
Simulates real-time order processing with GPS label cleaning + rush detection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import random
import math
import time
from datetime import datetime
import uuid

app = FastAPI(title="ZOMATHON KPT API", version="1.0.0")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── STATIC DATA ─────────────────────────────────────────────────────────────

RESTAURANTS = [
    {"id": 1, "name": "Biryani Blues",    "cuisine": "Biryani",      "base_kpt": 22, "lat": 28.6139, "lng": 77.2090},
    {"id": 2, "name": "Pizza Republic",   "cuisine": "Pizza",         "base_kpt": 15, "lat": 28.6220, "lng": 77.2150},
    {"id": 3, "name": "Wok & Roll",       "cuisine": "Chinese",       "base_kpt": 12, "lat": 28.6100, "lng": 77.2200},
    {"id": 4, "name": "Desi Dhaba",       "cuisine": "North Indian",  "base_kpt": 25, "lat": 28.6180, "lng": 77.2050},
    {"id": 5, "name": "Burger Baron",     "cuisine": "Burgers",       "base_kpt": 10, "lat": 28.6250, "lng": 77.2100},
    {"id": 6, "name": "Sushi Stop",       "cuisine": "Japanese",      "base_kpt": 18, "lat": 28.6090, "lng": 77.2180},
    {"id": 7, "name": "Curry Palace",     "cuisine": "South Indian",  "base_kpt": 20, "lat": 28.6200, "lng": 77.2080},
    {"id": 8, "name": "The Wrap House",   "cuisine": "Fast Food",     "base_kpt": 8,  "lat": 28.6160, "lng": 77.2130},
]

MENU_ITEMS = {
    "Biryani":      ["Chicken Biryani", "Mutton Biryani", "Veg Biryani", "Egg Biryani"],
    "Pizza":        ["Margherita", "Pepperoni", "BBQ Chicken", "Paneer Tikka Pizza"],
    "Chinese":      ["Hakka Noodles", "Fried Rice", "Spring Rolls", "Manchurian"],
    "North Indian": ["Dal Makhani", "Butter Chicken", "Paneer Butter Masala", "Naan"],
    "Burgers":      ["Classic Beef Burger", "Veg Burger", "Chicken Crispy", "Double Patty"],
    "Japanese":     ["Salmon Sushi", "Veg Maki", "Ramen", "Gyoza"],
    "South Indian": ["Masala Dosa", "Idli Sambar", "Vada", "Uttapam"],
    "Fast Food":    ["Chicken Wrap", "Veg Wrap", "Loaded Fries", "Combo Meal"],
}

RIDER_NAMES = ["Arjun S.", "Ravi K.", "Priya M.", "Suresh P.", "Anjali T.", 
               "Mohammed A.", "Deepak R.", "Sunita B.", "Vikram H.", "Neha G."]

# In-memory order store
orders_db: List[dict] = []
order_counter = 0

# ─── CORE ALGORITHM ──────────────────────────────────────────────────────────

def haversine_distance(lat1, lng1, lat2, lng2):
    """Returns distance in meters between two GPS coordinates"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def clean_label(rider_dist_meters: float, for_time: float, received_time: float) -> dict:
    """
    YOUR EXACT ALGORITHM:
    If rider within 15m AND gap >= 5min → REPLACE with received - 5
    If rider within 15m AND gap < 5min  → ACCEPT
    If rider outside 15m                → ACCEPT
    """
    gap = round(received_time - for_time, 2)

    if rider_dist_meters >= 15:
        return {
            "kpt": for_time,
            "decision": "ACCEPTED",
            "reason": f"Rider was {rider_dist_meters:.1f}m away — outside 15m, no pressure bias",
            "confidence": 0.95
        }
    
    if gap < 5:
        return {
            "kpt": for_time,
            "decision": "ACCEPTED",
            "reason": f"Rider within 15m but gap only {gap} min < 5 min — valid handoff",
            "confidence": 0.72
        }
    else:
        clean_kpt = round(received_time - 5.0, 2)
        return {
            "kpt": clean_kpt,
            "decision": "REPLACED",
            "reason": f"Rider within 15m + gap {gap} min ≥ 5 min → KPT = Received − 5 min",
            "confidence": 0.88
        }


def compute_rush_multiplier(google_busyness: int, pos_orders: int) -> float:
    """Module 2: Real-time kitchen load → rush multiplier"""
    kitchen_load = (google_busyness / 100) * 0.5 + (pos_orders / 18) * 0.5
    rush = round(1 + kitchen_load * 0.35, 3)
    return rush


def generate_order_data(order_id: int) -> dict:
    """Generate a complete random order with all signals"""
    restaurant = random.choice(RESTAURANTS)
    cuisine = restaurant["cuisine"]
    items = random.sample(MENU_ITEMS[cuisine], k=random.randint(1, 3))
    rider_name = random.choice(RIDER_NAMES)

    # True prep time based on restaurant + complexity
    item_complexity_bonus = len(items) * random.uniform(0.5, 1.5)
    true_kpt = round(restaurant["base_kpt"] + random.uniform(-3, 5) + item_complexity_bonus, 1)

    # Simulate rider GPS — random distance 0-80m from restaurant
    rider_dist = round(random.uniform(0, 80), 1)
    rider_near = rider_dist < 15

    # Simulate rider coords based on distance
    offset = rider_dist / 111320  # rough meters to degrees
    rider_lat = restaurant["lat"] + random.uniform(-offset, offset)
    rider_lng = restaurant["lng"] + random.uniform(-offset, offset)

    # Verify with haversine
    actual_dist = round(haversine_distance(rider_lat, rider_lng, restaurant["lat"], restaurant["lng"]), 1)

    # Simulate FOR: if rider near, 70% chance merchant taps early (pressure)
    tapped_early = rider_near and random.random() < 0.70
    for_time = round(true_kpt - random.uniform(2, 5), 1) if tapped_early else true_kpt

    # Simulate Order Received: 1-7 min after food is actually ready
    received_time = round(true_kpt + random.uniform(1, 7), 1)

    # Module 1: Clean the label
    label_result = clean_label(actual_dist, for_time, received_time)
    clean_kpt = label_result["kpt"]
    gap = round(received_time - for_time, 1)

    # Module 2: Rush signals
    google_busyness = random.randint(20, 95)
    pos_orders = random.randint(3, 18)
    rider_cluster = random.randint(0, 5)

    rush_multiplier = compute_rush_multiplier(google_busyness, pos_orders)
    final_kpt = round(clean_kpt * rush_multiplier, 1)

    # Error metrics
    raw_error = round(abs(for_time - true_kpt), 2)
    clean_error = round(abs(clean_kpt - true_kpt), 2)

    return {
        "id": order_id,
        "order_uuid": str(uuid.uuid4())[:8].upper(),
        "timestamp": datetime.now().isoformat(),
        "timestamp_readable": datetime.now().strftime("%I:%M:%S %p"),

        # Restaurant + items
        "restaurant": restaurant,
        "items": items,
        "rider_name": rider_name,

        # Raw signals
        "true_kpt": true_kpt,
        "for_time": for_time,
        "received_time": received_time,
        "gap_minutes": gap,

        # GPS
        "rider_lat": round(rider_lat, 6),
        "rider_lng": round(rider_lng, 6),
        "rider_distance_m": actual_dist,
        "rider_near": rider_near,
        "tapped_early": tapped_early,

        # Label cleaning result (Module 1)
        "decision": label_result["decision"],
        "reason": label_result["reason"],
        "confidence": label_result["confidence"],
        "clean_kpt": clean_kpt,

        # Rush signals (Module 2)
        "google_busyness": google_busyness,
        "pos_orders": pos_orders,
        "rider_cluster": rider_cluster,
        "rush_multiplier": rush_multiplier,

        # Final output
        "final_kpt": final_kpt,

        # Error metrics
        "raw_error": raw_error,
        "clean_error": clean_error,
    }


def compute_stats(orders: List[dict]) -> dict:
    """Aggregate statistics across all orders"""
    if not orders:
        return {"total": 0, "corrupted": 0, "replaced": 0, "raw_mae": 0, "clean_mae": 0, "improvement_pct": 0}

    n = len(orders)
    corrupted = sum(1 for o in orders if o["tapped_early"])
    replaced = sum(1 for o in orders if o["decision"] == "REPLACED")
    raw_mae = round(sum(o["raw_error"] for o in orders) / n, 3)
    clean_mae = round(sum(o["clean_error"] for o in orders) / n, 3)
    improvement_pct = round(((raw_mae - clean_mae) / raw_mae * 100), 1) if raw_mae > 0 else 0.0

    # Breakdown by restaurant
    restaurant_stats = {}
    for o in orders:
        rname = o["restaurant"]["name"]
        if rname not in restaurant_stats:
            restaurant_stats[rname] = {"count": 0, "total_raw_err": 0, "total_clean_err": 0, "replaced": 0}
        restaurant_stats[rname]["count"] += 1
        restaurant_stats[rname]["total_raw_err"] += o["raw_error"]
        restaurant_stats[rname]["total_clean_err"] += o["clean_error"]
        if o["decision"] == "REPLACED":
            restaurant_stats[rname]["replaced"] += 1

    for rname, rs in restaurant_stats.items():
        rs["avg_raw_mae"] = round(rs["total_raw_err"] / rs["count"], 2)
        rs["avg_clean_mae"] = round(rs["total_clean_err"] / rs["count"], 2)
        del rs["total_raw_err"], rs["total_clean_err"]

    return {
        "total": n,
        "corrupted": corrupted,
        "replaced": replaced,
        "raw_mae": raw_mae,
        "clean_mae": clean_mae,
        "improvement_pct": improvement_pct,
        "corruption_rate_pct": round(corrupted / n * 100, 1),
        "replace_rate_pct": round(replaced / n * 100, 1),
        "restaurant_breakdown": restaurant_stats,
    }


# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.get("/api/health")
def root():
    return {"message": "ZOMATHON KPT Prediction API", "version": "1.0.0", "status": "running"}


@app.post("/api/orders/place")
def place_order():
    """Place a new random order and run the full pipeline"""
    global order_counter
    order_counter += 1
    order = generate_order_data(order_counter)
    orders_db.append(order)
    # Small artificial delay to simulate processing
    time.sleep(0.1)
    return {"success": True, "order": order}


@app.post("/api/orders/bulk/{count}")
def place_bulk_orders(count: int):
    """Place multiple orders at once (max 50)"""
    global order_counter
    count = min(count, 50)
    new_orders = []
    for _ in range(count):
        order_counter += 1
        order = generate_order_data(order_counter)
        orders_db.append(order)
        new_orders.append(order)
    return {"success": True, "orders_placed": len(new_orders), "orders": new_orders}


@app.get("/api/orders")
def get_orders(limit: int = 20, offset: int = 0):
    """Get paginated order history"""
    total = len(orders_db)
    sliced = list(reversed(orders_db))[offset: offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "orders": sliced
    }


@app.get("/api/orders/{order_id}")
def get_order(order_id: int):
    """Get a specific order by ID"""
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": f"Order {order_id} not found"}, 404
    return order


@app.get("/api/stats")
def get_stats():
    """Get aggregate statistics"""
    return compute_stats(orders_db)


@app.get("/api/stats/timeline")
def get_timeline():
    """Get MAE over time (for chart)"""
    if not orders_db:
        return {"timeline": []}

    timeline = []
    for i in range(1, len(orders_db) + 1):
        subset = orders_db[:i]
        n = len(subset)
        raw_mae = round(sum(o["raw_error"] for o in subset) / n, 3)
        clean_mae = round(sum(o["clean_error"] for o in subset) / n, 3)
        timeline.append({
            "order_num": i,
            "raw_mae": raw_mae,
            "clean_mae": clean_mae,
        })
    return {"timeline": timeline}


@app.get("/api/stats/restaurants")
def get_restaurant_stats():
    """Per-restaurant breakdown"""
    stats = compute_stats(orders_db)
    return {"restaurant_breakdown": stats.get("restaurant_breakdown", {})}


@app.delete("/api/orders/reset")
def reset_orders():
    """Clear all orders"""
    global order_counter
    orders_db.clear()
    order_counter = 0
    return {"success": True, "message": "All orders cleared"}


@app.get("/api/simulate/scenario/{scenario}")
def simulate_scenario(scenario: str):
    """
    Simulate specific scenarios:
    - busy_night: High busyness, many corrupted labels
    - quiet_morning: Low busyness, clean labels  
    - rush_hour: Extreme rush, many replacements
    """
    global order_counter
    scenarios = {
        "busy_night":    {"count": 15, "busyness_range": (70, 95), "corruption_bias": 0.85},
        "quiet_morning": {"count": 10, "busyness_range": (10, 35), "corruption_bias": 0.15},
        "rush_hour":     {"count": 20, "busyness_range": (85, 100), "corruption_bias": 0.90},
    }

    if scenario not in scenarios:
        return {"error": "Unknown scenario. Use: busy_night, quiet_morning, rush_hour"}

    cfg = scenarios[scenario]
    new_orders = []

    for _ in range(cfg["count"]):
        order_counter += 1
        restaurant = random.choice(RESTAURANTS)
        cuisine = restaurant["cuisine"]
        items = random.sample(MENU_ITEMS[cuisine], k=random.randint(1, 3))
        true_kpt = round(restaurant["base_kpt"] + random.uniform(-3, 5), 1)

        rider_dist = round(random.uniform(0, 80), 1)
        rider_near = rider_dist < 15
        tapped_early = rider_near and random.random() < cfg["corruption_bias"]
        for_time = round(true_kpt - random.uniform(2, 5), 1) if tapped_early else true_kpt
        received_time = round(true_kpt + random.uniform(1, 7), 1)

        label_result = clean_label(rider_dist, for_time, received_time)
        google_busyness = random.randint(*cfg["busyness_range"])
        pos_orders = random.randint(8, 18) if google_busyness > 70 else random.randint(2, 8)
        rush_multiplier = compute_rush_multiplier(google_busyness, pos_orders)

        order = {
            "id": order_counter,
            "order_uuid": str(uuid.uuid4())[:8].upper(),
            "timestamp": datetime.now().isoformat(),
            "timestamp_readable": datetime.now().strftime("%I:%M:%S %p"),
            "restaurant": restaurant,
            "items": items,
            "rider_name": random.choice(RIDER_NAMES),
            "true_kpt": true_kpt,
            "for_time": for_time,
            "received_time": received_time,
            "gap_minutes": round(received_time - for_time, 1),
            "rider_distance_m": rider_dist,
            "rider_near": rider_near,
            "tapped_early": tapped_early,
            "decision": label_result["decision"],
            "reason": label_result["reason"],
            "confidence": label_result["confidence"],
            "clean_kpt": label_result["kpt"],
            "google_busyness": google_busyness,
            "pos_orders": pos_orders,
            "rider_cluster": random.randint(0, 5),
            "rush_multiplier": rush_multiplier,
            "final_kpt": round(label_result["kpt"] * rush_multiplier, 1),
            "raw_error": round(abs(for_time - true_kpt), 2),
            "clean_error": round(abs(label_result["kpt"] - true_kpt), 2),
        }
        orders_db.append(order)
        new_orders.append(order)

    return {
        "success": True,
        "scenario": scenario,
        "orders_placed": len(new_orders),
        "stats": compute_stats(orders_db)
    }

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
