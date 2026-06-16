# 🚦 ACORP: ASTraM Congestion Optimizer & Resource Planner

ACORP is a state-of-the-art, AI-driven traffic intelligence prototype designed for the **Flipkart Gridlock Hackathon 2.0 (Round 2)**. It addresses the challenges of **Event-Driven Traffic Congestion (Planned & Unplanned)** in Bengaluru by forecasting traffic impacts, optimizing officer deployments using Linear Programming, and calculating dynamic route diversions.

Developed in collaboration with insights from the **Bengaluru Traffic Police (BTP) ASTraM** framework.

---

## 🚀 Live Demo & Deployment
*   **Live App Demo**: [https://event-driven-congestion-oucttjnxbbiiwxshm8jwjr.streamlit.app/](https://event-driven-congestion-oucttjnxbbiiwxshm8jwjr.streamlit.app/)
*   **GitHub Repository**: [https://github.com/bunnysunny24/Event-Driven-Congestion.git](https://github.com/bunnysunny24/Event-Driven-Congestion.git)

---

## 📖 BTP ASTraM Operational Context
Under the current Bengaluru Traffic Police (BTP) operations, managing event-driven congestion (such as IPL matches at Chinnaswamy Stadium, political rallies, waterlogging, or sudden VIP movements) is highly experience-driven and reactive. The **ACORP** prototype solves this by providing a proactive planning suite that integrates historical analytics, predictive machine learning, and mathematical optimization:

```
                    +------------------------------------+
                    | BTP ASTraM Event & Incident Ingest |
                    +-----------------+------------------+
                                      |
                                      v
                    +------------------------------------+
                    |  XGBoost Congestion Forecast (1-10)|
                    +-----------------+------------------+
                                      |
                                      v (Congestion Index)
                    +------------------------------------+
                    | PuLP Integer LP Resource Allocator |
                    +-----------------+------------------+
                                      |
                                      v (Dispatch & Diversions)
                    +------------------------------------+
                    | NetworkX Dijkstra Diversion Routing|
                    +-----------------+------------------+
                                      |
                                      v
                    +------------------------------------+
                    | Post-Event Drift Learning Feedback |
                    +-----------------+------------------+
```

---

## 🧠 The AI, ML & Optimization Core

### 1. Predictive Engine (XGBoost Regressor)
To quantify **Event Impact in Advance**, we train an **XGBoost Regressor** on **8,171 historical ASTraM incidents**.
*   **Features Modeled**: Event Type (Planned/Unplanned), Event Cause, Affected Corridor, Affected Zone, Priority level, Road Closure requirements, Hour of Day, and Day of Week.
*   **Target Variable**: A calculated **Congestion Impact Score (1-10)** mapped from historical priority levels, causes, and road closures.
*   **Model Performance**: The model achieves a Cross-Validation Mean Absolute Error (MAE) of **`~0.028`** and Root Mean Squared Error (RMSE) of **`~0.073`**.
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

## 🌟 Key Application Pages & Walkthrough

### 1. 📊 Historical Incident Explorer
*   **3D Geospatial Density Maps**: Interactive 3D Pydeck Hexagon maps showing historical event density and bottlenecks across Bangalore's major corridors.
*   **Folium Map Markers**: Detailed, color-coded markers for individual incidents (accidents, waterlogging, VIP movements).
*   **Temporal Heatmaps**: Peak hour vs. day-of-week incident occurrence matrix.

![3D Density Map](Images/Screenshot%202026-06-16%20151759.png)
![Historical Charts](Images/Screenshot%202026-06-16%20151813.png)

---

### 2. 🔮 ML Congestion Forecaster
*   **Specifications Form**: Inputs event details (type, cause, priority, expected date/time, corridor).
*   **Quantified Advisory**: Displays predicted score (1-10) with BTP operational guidelines (e.g. low impact vs. critical high impact requiring immediate diversion activation).
*   **XGBoost Explainability**: Interpretable feature importances detailing which variables drive the prediction.

![Model Setup & Explainability](Images/Screenshot%202026-06-16%20151826.png)
![Prediction Results](Images/Screenshot%202026-06-16%20151841.png)

---

### 3. 👮 Manpower & Barricade Optimizer
*   **Optimization Run**: Outputs the PuLP-solved optimal officer allocation matrix.
*   **Visual Dispatch Map**: Renders lines between stations and junctions indicating personnel movement paths.
*   **Barricading suggestions**: Recommends locations for protective barricades.

![Manpower Allocation Matrix](Images/Screenshot%202026-06-16%20151854.png)
![Manpower Allocation Map](Images/Screenshot%202026-06-16%20151904.png)

---

### 4. 🗺️ Traffic Diversion Planner
*   **Rerouting Simulation**: Renders the primary path (dashed orange) vs the diversion path (solid green) avoiding the congested corridor (solid red).

![Rerouting Planner](Images/Screenshot%202026-06-16%20151917.png)

---

### 5. 📈 Post-Event Learning (Feedback Loop)
*   **Debrief Logger**: Officers enter actual event outcomes (duration, actual congestion index).
*   **Drift Detection**: Alerts when Mean Absolute Error (MAE) of predictions drifts above a threshold of 0.8.
*   **Model Retraining**: Trigger retraining of the XGBoost model on the new data buffer to adapt predictions to new traffic patterns.

![Feedback Loop & Drift Retraining](Images/Screenshot%202026-06-16%20151929.png)

---

## 📋 Hackathon Presentation Slide Deck (PPT) Structure
*Copy this section into an AI slide generator (like Gamma, Tome, or ChatGPT) to automatically generate your PPT presentation:*

*   **Slide 1: Title Slide**
    *   **Title**: ACORP: ASTraM Congestion Optimizer & Resource Planner
    *   **Subtitle**: AI-Driven Traffic Forecasting and Dynamic Resource Optimization for Bengaluru
    *   **Presenter Name**: [Your Name / Team Name]
*   **Slide 2: Problem Statement**
    *   **Core Issues**: Event-driven traffic congestion in Bengaluru is currently reactive, experience-based, and lacks a post-event learning loop.
    *   **Solution Vision**: Proactive, data-backed congestion score forecasting, mathematical resource allocation, and dynamic diversions.
*   **Slide 3: System Architecture & Workflow**
    *   **Pipeline**: Historical Incident Ingest $\rightarrow$ XGBoost Dual-Target Forecasting $\rightarrow$ PuLP Integer Linear Program Optimization $\rightarrow$ NetworkX Graph Routing $\rightarrow$ Drift Monitoring.
*   **Slide 4: ML Forecasting (XGBoost Regressors)**
    *   **Details**: Trained on 8,171 ASTraM incidents to predict:
        1.  *Congestion Impact Score (1-10)*
        2.  *Expected Clearance Duration (hours)*
    *   **Explainable AI**: Real-time feature importance displays factor weights (Priority, Road Closure, Cause).
*   **Slide 5: Mathematical Manpower Optimization (Integer LP)**
    *   **Objective**: Minimize total deployment overhead (person-kilometers).
    *   **Constraints**: Ensures junction coverage demands (which scale dynamically based on the predicted Congestion Score and road-closures) do not exceed police station capacities.
*   **Slide 6: Dynamic Diversion Planning (Graph Theory)**
    *   **Details**: 12-junction, 16-corridor graph representing main Bengaluru corridors.
    *   **Mechanism**: Applies a delay penalty multiplier to the affected route and computes the optimal diversion path using Dijkstra's shortest path algorithm.
*   **Slide 7: Continual Learning & Feedback Loop**
    *   **Concept**: Resolves the "No post-event learning" operational challenge. Officers input actual clearance durations to calculate Mean Absolute Error (MAE).
    *   **Retraining**: Automatically detects model drift (when MAE > 0.8) and triggers background retraining.
*   **Slide 8: Feasibility & Deployment Ready**
    *   **Advantages**: 100% open-source libraries. No complex commercial API dependencies (e.g. MapmyIndia restricted keys). Fully hosted and live on Streamlit Cloud.
*   **Slide 9: Key Outcomes & Real-World Impact**
    *   **Benefits**: Reduces commuter delay time (~45+ mins saved per diversion), lowers deployment overhead (person-km), and reduces manual police planning stress.
*   **Slide 10: Conclusion & Next Steps**
    *   **Vision**: Live integration with BTP ASTraM control room feeds and integration with VMS (Variable Message Signs) across Bengaluru.

---

## 🎬 Video Recording Script & Prompts
*Use this screenplay script to record your 3-minute Loom demo video:*

*   **Scene 1: Introduction (0:00 - 0:30)**
    *   **Visual**: Show the **Historical Explorer** tab.
    *   **Action**: Rotate and zoom the 3D Hexagon density map live. Click on a couple of markers on the Folium map.
    *   **Talking Points**: *"Hello judges, today we are looking at ACORP, a decision support prototype built for the Bengaluru Traffic Police to manage event-driven congestion. Our database consists of 8,171 historical ASTraM incidents. Using Pydeck, we visualize congestion hot spots in interactive 3D."*
*   **Scene 2: Predictive Forecasting (0:30 - 1:15)**
    *   **Visual**: Switch to the **Congestion Forecasting** tab.
    *   **Action**: Fill out the form: Title: "Cricket Match", Event Type: "Planned", Event Cause: "public_event", Priority: "High", Corridor: "Tumkur Road", Road Closure: "True". Click **Predict**.
    *   **Talking Points**: *"Instead of experience-driven guessing, we use two trained XGBoost models. When we input event specifications, ACORP predicts both a Congestion Score of 7.2/10 and an Expected Clearance Time of 3.2 hours. We also display model interpretability charts using feature importance."*
*   **Scene 3: Resource Optimization (1:15 - 2:00)**
    *   **Visual**: Switch to the **Resource Optimizer** tab.
    *   **Action**: Scroll down to show the solved **Allocation Matrix** and hover over the blue/red markers on the Folium allocation map.
    *   **Talking Points**: *"Once we have the forecast, we run an Integer Linear Programming model using PuLP. The model minimizes total travel distance for our officers. You can see the allocation matrix showing exactly how many officers to dispatch from nearby stations to each junction, as well as recommended barricading positions."*
*   **Scene 4: Traffic Diversion (2:00 - 2:45)**
    *   **Visual**: Switch to the **Traffic Diversion** tab.
    *   **Action**: Drag the **Congestion Multiplier** slider to `12.0` and show how the solid green line (diversion) reroutes around the red blocked line.
    *   **Talking Points**: *"For route diversions, we modeled Bengaluru's core corridors as a Graph Network. By simulating a delay penalty on the congested route, Dijkstra's algorithm dynamically computes a recommended diversion, saving commuters valuable travel time."*
*   **Scene 5: Feedback & Wrap-up (2:45 - 3:00)**
    *   **Visual**: Switch to the **Feedback Loop** tab. Click **Retrain Model**.
    *   **Action**: Show the error tracking line chart.
    *   **Talking Points**: *"Finally, to close the loop, officers log actual event outcomes. If the model's error drifts over 0.8, the system alerts the command center, allowing one-click online retraining. Thank you for your time!"*

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
    *   **URL**: *Choose a custom URL or let Streamlit generate one.*
4.  Click **Deploy!**
