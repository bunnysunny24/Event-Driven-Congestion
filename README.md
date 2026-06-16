# 🚦 ACORP: ASTraM Congestion Optimizer & Resource Planner

ACORP is a state-of-the-art, AI-driven traffic intelligence prototype designed for **Flipkart Gridlock Hackathon 2.0 (Round 2)**. It addresses the challenge of **Event-Driven Traffic Congestion (Planned & Unplanned)** in Bengaluru by forecasting traffic impacts, optimizing officer deployments using Linear Programming, and calculating dynamic route diversions.

Developed in collaboration with insights from the **Bengaluru Traffic Police (BTP) ASTraM** framework.

---

## 🚀 Live Demo & Deployment
*   **GitHub Repository**: [https://github.com/bunnysunny24/Event-Driven-Congestion.git](https://github.com/bunnysunny24/Event-Driven-Congestion.git)
*   **Live App Demo**: *Deploying the app to Streamlit Cloud is free and recommended. See the [Hosting Guide](#-hosting-guide-streamlit-community-cloud) below.*

---

## 🧠 The AI, ML & Optimization Core

This prototype integrates multiple advanced computational methods to solve traffic gridlocks:

### 1. Predictive Engine (XGBoost Regressor)
To quantify **Event Impact in Advance**, we train an **XGBoost Regressor** on **8,171 historical ASTraM incidents**.
*   **Features Modeled**: Event Type (Planned/Unplanned), Event Cause, Affected Corridor, Affected Zone, Priority level, Road Closure requirements, Hour of Day, and Day of Week.
*   **Target Variable**: A calculated **Congestion Impact Score (1-10)** mapped from historical priority levels, causes, and road closures.
*   **Explainable AI**: The system uses model feature importance rankings to give operators clear insights into *why* a particular event is predicted to cause a certain congestion level.

### 2. Manpower Allocation (Integer Linear Programming)
Rather than relying on experience-driven deployment, we model officer allocation from nearby Police Stations (Sources) to congested Junctions (Sinks) as a **Transportation Optimization Problem** solved via **Mixed Integer Linear Programming (MILP)** using `PuLP`:

$$
\text{Minimize } \sum_{s \in S} \sum_{j \in J} d_{s,j} \cdot x_{s,j}
$$

**Subject to:**
1.  **Junction Coverage Constraints**: The sum of officers allocated to a junction must meet the dynamic requirement (which scales based on the predicted Congestion Impact Score and road-closure requirements):
    $$
    \sum_{s \in S} x_{s,j} \ge \text{ScaledRequirement}_j \quad \forall j \in J
    $$
2.  **Station Capacity Constraints**: The number of officers drawn from a station cannot exceed its capacity:
    $$
    \sum_{j \in J} x_{s,j} \le \text{Capacity}_s \quad \forall s \in S
    $$
3.  **Integrity Constraints**: Officers must be deployed in whole numbers:
    $$
    x_{s,j} \in \mathbb{Z}^+ \quad \forall s \in S, j \in J
    $$

### 3. Dynamic Rerouting (Graph Theory & Dijkstra's Algorithm)
Bengaluru's arterial road network is modeled as a directed corridor network $G = (V, E)$ using `NetworkX`. 
*   When an event requires lane closures or causes high congestion, a **Congestion Delay Penalty** $\alpha$ (input via slider) is dynamically applied to the edge weight representing that corridor.
*   The system calculates the alternative path minimizing travel time:
    $$
    w_{\text{delayed}}(u, v) = w_{\text{base}}(u, v) \cdot \alpha
    $$
*   Dijkstra's shortest path algorithm computes both the standard route and the diversion route, overlaying both on an interactive map.

---

## 🌟 Key Application Pages

### 1. 📊 Historical Incident Explorer
*   **3D Geospatial Density Maps**: Interactive 3D Pydeck Hexagon maps showing historical event density and bottlenecks across Bangalore's major corridors.
*   **Folium Map Markers**: Detailed, color-coded markers for individual incidents (accidents, waterlogging, VIP movements).
*   **Temporal Heatmaps**: Peak hour vs. day-of-week incident occurrence matrix.

### 2. 🔮 ML Congestion Forecaster
*   **Specifications Form**: Inputs event details (type, cause, priority, expected date/time, corridor).
*   **Quantified Advisory**: Displays predicted score (1-10) with BTP operational guidelines (e.g. low impact vs. critical high impact requiring immediate diversion activation).

### 3. 👮 Manpower & Barricade Optimizer
*   **Optimization Run**: Outputs the PuLP-solved optimal officer allocation matrix.
*   **Visual Dispatch Map**: Renders lines between stations and junctions indicating personnel movement paths.
*   **Barricading suggestions**: Recommends locations for protective barricades.

### 4. 🗺️ Traffic Diversion Planner
*   **Rerouting Simulation**: Renders the primary path (dashed orange) vs the diversion path (solid green) avoiding the congested corridor (solid red).

### 5. 📈 Post-Event Learning (Feedback Loop)
*   **Debrief Logger**: Officers enter actual event outcomes (duration, actual congestion index).
*   **Drift Detection**: Alerts when Mean Absolute Error (MAE) of predictions drifts above a threshold of 0.8.
*   **Model Retraining**: Trigger retraining of the XGBoost model on the new data buffer to adapt predictions to new traffic patterns.

---

## 🛠️ Installation & Running Guide

### 1. Prerequisites
*   Python 3.9 - 3.11 installed.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/bunnysunny24/Event-Driven-Congestion.git
cd Event-Driven-Congestion
pip install -r requirements.txt
```

### 3. Run Locally
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🌐 Hosting Guide: Streamlit Community Cloud

Hosting the prototype is **free** and takes less than 2 minutes. Follow these steps to deploy:

1.  Go to [Streamlit Community Cloud](https://share.streamlit.io/) and click **Sign Up** (use your GitHub account).
2.  Once logged in, click the **New App** button in the top right.
3.  Fill in the deployment details:
    *   **Repository**: `bunnysunny24/Event-Driven-Congestion`
    *   **Branch**: `main`
    *   **Main file path**: `app.py`
4.  Click **Deploy!**

Your app will be built and accessible via a public `https://<your-app-name>.streamlit.app` URL, which you can share with the judges.
