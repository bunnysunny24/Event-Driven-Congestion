# 🚦 ACORP: ASTraM Congestion Optimizer & Resource Planner

ACORP is a state-of-the-art, AI-driven traffic intelligence prototype designed for **Flipkart Gridlock Hackathon 2.0 (Round 2)**. It solves the challenges of **Event-Driven Traffic Congestion (Planned & Unplanned)** in Bengaluru by forecasting traffic impacts, optimizing officer deployments using Linear Programming, and calculating dynamic route diversions.

Developed in collaboration with insights from the **Bengaluru Traffic Police (BTP) ASTraM** framework.

---

## 🌟 Key Features

### 1. 📊 Historical Incident Explorer
*   **3D Geospatial Density Maps**: Interactive 3D Pydeck Hexagon maps showing event density and bottlenecks across Bangalore's major corridors.
*   **Marker Visualizations**: Folium map showing detailed, color-coded markers for individual historical incidents (accidents, breakdowns, waterlogging, public events).
*   **Temporal Analytics**: Plotly heatmaps highlighting peak days and hours of traffic disruptions.

### 2. 🔮 ML Congestion Forecaster
*   **XGBoost Predictive Engine**: Trained on 8,173 ASTraM incidents to forecast a quantified **Congestion Impact Score (1-10)** in advance.
*   **Explainable AI**: Real-time feature importance charts indicating which features (corridor, priority, cause, road-closures) drive traffic impacts.
*   **Advisory Generation**: Dynamic warnings and operational recommendations based on predicted impact thresholds.

### 3. 👮 Manpower & Barricade Optimizer
*   **Integer Linear Programming (ILP)**: Formulated with `PuLP` to minimize transit overhead (person-kilometers) while guaranteeing coverage at affected junctions.
*   **Allocation Matrix**: Automatic computation of police personnel assignments from 5 nearby stations to 5 target junctions.
*   **Visual Dispatch Map**: Displays deployment paths and recommends optimal spots for barricading.

### 4. 🗺️ Traffic Diversion Planner
*   **Corridor Graph Network**: Modeled using `NetworkX` representing major Bengaluru arterial corridors.
*   **Dynamic Rerouting**: Simulates lane closures by applying congestion penalties, computing alternative routes side-by-side with original routes.
*   **Route Comparison**: Maps primary (dashed orange) vs diversion (solid green) paths.

### 5. 📈 Post-Event Learning (Feedback Loop)
*   **Operational Debrief Form**: Allows officers to log actual outcomes (duration, congestion index, effectiveness) after an event.
*   **Performance Tracking**: Computes error metrics (MAE/RMSE) over time to monitor model accuracy.
*   **Drift Retraining**: Simulates model updates to adapt to changing city patterns.

---

## 🛠️ Tech Stack

*   **Frontend**: Streamlit (Premium Dark Theme)
*   **Machine Learning**: XGBoost, Scikit-learn
*   **Optimization**: PuLP (Mixed Integer Linear Programming)
*   **Network & Graphs**: NetworkX
*   **Maps & Geospatial**: Pydeck, Folium, Streamlit-Folium, GeoPandas, PyProj, Shapely
*   **Analytics**: Plotly Express, Pandas, NumPy

---

## 🚀 Installation & Running Guide

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

### 2. Clone the repository and install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit Application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🧠 System Architecture

```
                      +-----------------------------+
                      |     ASTraM Event Dataset    |
                      +--------------+--------------+
                                     |
                                     v
                       +-------------+-------------+
                       |    XGBoost Forecaster     |
                       +-------------+-------------+
                                     |
                                     v (Congestion Index)
                       +-------------+-------------+
                       |  PuLP LP Resource Engine  |
                       +-------------+-------------+
                                     |
                                     v (Allocations & Routes)
                      +--------------+--------------+
                      |   NetworkX Diversion Graph  |
                      +--------------+--------------+
                                     |
                                     v
                      +--------------+--------------+
                      | Streamlit Interactive Map &  |
                      |      Feedback Database      |
                      +-----------------------------+
```
