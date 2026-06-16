import streamlit as st
import pandas as pd
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="ASTraM Congestion Optimizer & Resource Planner (ACORP)",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling injection
st.markdown("""
<style>
    /* Gradient backgrounds */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(10, 14, 23) 0%, rgb(18, 24, 36) 90.1%);
    }
    
    /* Gaps and alignments */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-title {
        background: -webkit-linear-gradient(45deg, #00F2FE, #4FACFE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #8A99AD;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Premium card containers */
    .custom-card {
        background-color: #121824;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .custom-card:hover {
        border-color: #00F2FE;
        transform: translateY(-2px);
    }
    
    /* Glowing metrics */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00F2FE;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #8A99AD;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Load data function (cached)
@st.cache_data
def load_astram_data():
    # Portable path: look for CSV in the same directory as app.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find the CSV file (supports the original long filename or a renamed version)
    csv_candidates = [f for f in os.listdir(base_dir) if f.endswith('.csv')]
    if csv_candidates:
        file_path = os.path.join(base_dir, csv_candidates[0])
    else:
        # Check in a 'data' subdirectory as fallback
        data_dir = os.path.join(base_dir, 'data')
        if os.path.isdir(data_dir):
            csv_candidates = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            if csv_candidates:
                file_path = os.path.join(data_dir, csv_candidates[0])
            else:
                st.error("No CSV dataset found. Please place the ASTraM CSV file in the project root or a 'data/' folder.")
                st.stop()
        else:
            st.error("No CSV dataset found. Please place the ASTraM CSV file in the project root or a 'data/' folder.")
            st.stop()
    
    df = pd.read_csv(file_path)
    
    # 1. Clean datetime columns
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['closed_datetime'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
    df['end_datetime'] = pd.to_datetime(df['end_datetime'], errors='coerce')
    
    # Fill missing start datetime with created_date if necessary
    missing_start = df['start_datetime'].isna()
    if missing_start.any():
        df.loc[missing_start, 'start_datetime'] = pd.to_datetime(df.loc[missing_start, 'created_date'], errors='coerce')
        
    # Drop rows without valid start_datetime or coordinates
    df = df.dropna(subset=['start_datetime', 'latitude', 'longitude'])
    
    # Clean coordinate outliers (ensure they are in Bangalore bounds roughly)
    df = df[(df['latitude'] > 12.0) & (df['latitude'] < 14.0)]
    df = df[(df['longitude'] > 77.0) & (df['longitude'] < 78.0)]
    
    # 2. Time feature engineering
    df['hour'] = df['start_datetime'].dt.hour
    df['day_of_week'] = df['start_datetime'].dt.dayofweek
    df['day_name'] = df['start_datetime'].dt.day_name()
    df['is_weekend'] = df['day_of_week'].isin([5, 6])
    df['month'] = df['start_datetime'].dt.month
    df['date'] = df['start_datetime'].dt.date
    
    # Calculate duration
    df['duration_hours'] = (df['closed_datetime'] - df['start_datetime']).dt.total_seconds() / 3600.0
    df['duration_hours'] = df['duration_hours'].fillna(1.0)
    df['duration_hours'] = df['duration_hours'].clip(lower=0.2, upper=8.0)
    
    # 3. Congestion impact score construction
    # We will construct a synthetic Congestion Impact Index based on:
    # - Priority: High = 4, Low = 1
    # - Requires Road Closure: True = 4, False = 0
    # - Event Cause weights: accident = 3, public_event = 3, water_logging = 3, construction = 2, tree_fall = 2, breakdown = 1, others = 1
    cause_weights = {
        'accident': 3.0, 'public_event': 4.0, 'procession': 3.0, 'protest': 3.0, 'vip_movement': 4.0,
        'water_logging': 3.0, 'construction': 2.0, 'tree_fall': 2.0, 'pot_holes': 1.5,
        'vehicle_breakdown': 1.0, 'road_conditions': 1.5, 'congestion': 2.0, 'others': 1.0, 'Debris': 1.0, 'debris': 1.0
    }
    df['cause_weight'] = df['event_cause'].map(cause_weights).fillna(1.0)
    df['priority_weight'] = df['priority'].map({'High': 3.0, 'Low': 1.0}).fillna(1.0)
    df['closure_weight'] = df['requires_road_closure'].map({True: 3.0, False: 0.0}).fillna(0.0)
    
    # Raw Score
    df['raw_impact'] = df['cause_weight'] + df['priority_weight'] + df['closure_weight']
    
    # Scale raw impact to a 1 - 10 scale (Congestion Impact Score)
    min_val, max_val = df['raw_impact'].min(), df['raw_impact'].max()
    df['congestion_impact'] = 1.0 + 9.0 * (df['raw_impact'] - min_val) / (max_val - min_val)
    df['congestion_impact'] = df['congestion_impact'].round(1)
    
    return df

# Initialize session state for data sharing across pages
if 'df' not in st.session_state:
    st.session_state['df'] = load_astram_data()

# Define navigation structure
pg_explorer = st.Page("pages/1_📊_Explorer.py", title="Historical Explorer", icon="📊")
pg_forecast = st.Page("pages/2_🔮_Forecasting.py", title="Congestion Forecasting", icon="🔮")
pg_resources = st.Page("pages/3_👮_Resources.py", title="Resource Optimizer", icon="👮")
pg_diversions = st.Page("pages/4_🗺_Diversions.py", title="Traffic Diversion", icon="🗺️")
pg_learning = st.Page("pages/5_📈_Post_Event_Learning.py", title="Feedback Loop", icon="📈")

pg = st.navigation([pg_explorer, pg_forecast, pg_resources, pg_diversions, pg_learning])

# Shared sidebar content (renders across all pages)
with st.sidebar:
    st.markdown("### 🚦 ACORP Decision Pipeline")
    st.markdown("""
    <div style='background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 10px; font-family: monospace; font-size: 11px; line-height: 1.4; color: #8A99AD;'>
    &nbsp;&nbsp;Historical Data<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
    &nbsp;&nbsp;XGBoost Prediction<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
    &nbsp;&nbsp;Resource Opt (PuLP)<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
    &nbsp;&nbsp;Diversions (NetworkX)<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
    &nbsp;&nbsp;Feedback Learning<br>
    </div>
    """, unsafe_allow_html=True)

pg.run()
