# 🏆 ZOMATHON KPT Prediction & Label Cleaning System

### Full-Stack Prototype --- Bias Detection + Intelligent Time Correction

------------------------------------------------------------------------

## 📌 Problem Statement

Kitchen Preparation Time (KPT) data can become **corrupted due to rider
pressure bias**:

-   Riders arriving early may pressure restaurants to tap "Food Ready"
-   This artificially reduces reported preparation time
-   Corrupted labels degrade model training quality
-   Inaccurate data leads to unreliable prediction systems

This system detects and corrects that bias in real time.

------------------------------------------------------------------------

## 💡 Solution Overview

This prototype implements a **two-stage correction pipeline**:

### 1️⃣ Label Cleaning Module

Detects corrupted KPT labels using rider proximity and timing gap logic.

### 2️⃣ Dynamic Rush Multiplier

Adjusts clean KPT dynamically using real kitchen load signals: - Google
busyness - Active POS orders

------------------------------------------------------------------------

## 🧠 Core Innovation

Instead of blindly trusting timestamps, this system:

-   Detects pressure-induced early taps
-   Replaces corrupted labels using rule-based correction
-   Quantifies improvement using MAE (Mean Absolute Error)
-   Visualizes improvement live

This ensures **cleaner training data and more reliable predictions**.

------------------------------------------------------------------------

# 🏗️ Project Structure

    zomathon-app/
    ├── backend/
    │   ├── main.py
    │   └── requirements.txt
    ├── frontend/
    │   └── index.html
    ├── start.sh
    └── README.md

------------------------------------------------------------------------

# ⚡ Quick Start (Local Setup)

## 1️⃣ Install Dependencies

``` bash
cd backend
pip install -r requirements.txt
```

## 2️⃣ Start Backend

``` bash
uvicorn main:app --reload --port 8000
```

You should see:

    INFO:     Uvicorn running on http://127.0.0.1:8000
    INFO:     Application startup complete.

## 3️⃣ Open Frontend

Open:

    frontend/index.html

No build step required.

------------------------------------------------------------------------

# 🌐 Deployment (Free Options)

## Option A --- Railway (Recommended)

1.  Push repo to GitHub\
2.  Go to railway.app → Deploy from GitHub\
3.  Start command:

```{=html}
<!-- -->
```
    uvicorn main:app --host 0.0.0.0 --port $PORT

4.  Update in `index.html`:

``` javascript
const API = "https://your-railway-url"
```

Host frontend via GitHub Pages or Netlify.

------------------------------------------------------------------------

# 🔌 API Reference

  Method   Endpoint                          Description
  -------- --------------------------------- -------------------
  GET      `/`                               Health check
  POST     `/api/orders/place`               Place 1 order
  POST     `/api/orders/bulk/{n}`            Bulk simulate
  GET      `/api/orders?limit=20`            Order history
  GET      `/api/stats`                      Aggregate metrics
  GET      `/api/stats/timeline`             MAE over time
  GET      `/api/simulate/scenario/{name}`   Run scenario
  DELETE   `/api/orders/reset`               Reset system

------------------------------------------------------------------------

# 🧮 Algorithm Details

## 🔹 Module 1 --- Label Cleaning

``` python
def clean_label(rider_dist_meters, for_time, received_time):
    gap = received_time - for_time

    if rider_dist_meters >= 15:
        return ACCEPT  # Rider not present → no pressure

    if gap < 5:
        return ACCEPT  # Fast handoff → likely genuine

    return REPLACE(kpt=received_time - 5)
```

### Decision Table

  Rider Distance   Gap        Action
  ---------------- ---------- ---------
  ≥ 15m            Any        Accept
  ≤ 15m            \< 5 min   Accept
  ≤ 15m            ≥ 5 min    Replace

------------------------------------------------------------------------

## 🔹 Module 2 --- Rush Multiplier

``` python
def compute_rush_multiplier(google_busyness, pos_orders):
    kitchen_load = (google_busyness / 100) * 0.5 + (pos_orders / 18) * 0.5
    return 1 + kitchen_load * 0.35
```

-   Max increase: +35%
-   Reflects real-time kitchen workload

------------------------------------------------------------------------

# 📊 Metrics & Evaluation

The system computes:

-   Raw MAE (with corrupted labels)
-   Clean MAE (after correction)
-   Corruption rate
-   Replace rate
-   Timeline improvement trend

Judges can visually observe MAE improvement in real time.

------------------------------------------------------------------------

# 🎯 Simulated Scenarios

-   `busy_night` → 85% corruption bias\
-   `rush_hour` → 90% corruption bias\
-   `quiet_morning` → 15% corruption

------------------------------------------------------------------------

# 🖥️ What Judges Will See

### Dashboard

-   Place orders live
-   View MAE improvements
-   See corruption detection in action
-   Visual error comparison charts

### Orders Tab

-   Complete order table
-   Detailed signal breakdown
-   Decision explanation per order

### Algo Tab

-   Transparent algorithm logic
-   Decision table
-   Rush multiplier explanation

------------------------------------------------------------------------

# 🛠 Tech Stack

  Layer          Technology
  -------------- ----------------------------
  Backend API    FastAPI (Python)
  Data Storage   In-memory (demo optimized)
  Frontend       React (CDN, no build)
  Charts         Pure CSS / SVG
  Deployment     Railway / Replit / Render

------------------------------------------------------------------------

# 🚀 Impact

-   Improves training data reliability\
-   Reduces systematic bias\
-   Enhances KPT prediction accuracy\
-   Demonstrates production-ready correction logic

------------------------------------------------------------------------

# 🏁 Version

**ZOMATHON KPT Prediction System --- Prototype v2.0**

------------------------------------------------------------------------
# Contributors

1) Samarth Nalkar
2) Anirudh Rawat
3) Syed Shavez Jafar

