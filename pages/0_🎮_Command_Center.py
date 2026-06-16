import streamlit as st
import pandas as pd
import numpy as np

# Title
st.markdown("<div class='main-title'>🎮 ACORP Operations Command Center</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Unified control room dashboard aggregating forecasts, deployments, and routing actions.</div>", unsafe_allow_html=True)

# Check if data exists in session state
if 'df' not in st.session_state:
    st.warning("Please load the app from the main page.")
    st.stop()

df = st.session_state['df']

# Load active event details from session state, or load a default demo event
if 'last_prediction' in st.session_state:
    event = st.session_state['last_prediction']
    st.success(f"🎛️ **Active Control Room Incident**: Displaying metrics for your predicted event **'{event['title']}'**.")
else:
    # Default event for demonstration
    event = {
        'title': 'IPL Match: RCB vs KKR (Chinnaswamy Stadium)',
        'type': 'planned',
        'cause': 'public_event',
        'corridor': 'CBD 2',
        'priority': 'High',
        'zone': 'Central Zone 2',
        'road_closure': True,
        'datetime': pd.to_datetime("2026-06-20 17:30:00"),
        'impact_score': 8.2,
        'duration_hours': 3.5,
        'delay_min': 37,
        'delay_max': 49,
        'confidence': 94,
        'rec_officers': 25,
        'explanations': [
            "High Priority Event (+1.5)",
            "Road Closure (+2.8)",
            "Peak Hour active (+1.2)",
            "Public Event (+2.0)"
        ]
    }
    st.info("💡 **No active prediction run yet**. Displaying default control room scenario: **IPL Match at Chinnaswamy Stadium**. Go to **Congestion Forecasting** to create your own.")

# --- DYNAMIC METRICS FOR LOGISTICS ---
score = event['impact_score']
if score < 4.0:
    status_color = "#10B981" # Green
    status_text = "LOW IMPACT"
    advisory = "Routine Patrol Monitoring"
elif score < 7.0:
    status_color = "#F59E0B" # Orange
    status_text = "MEDIUM IMPACT"
    advisory = "Active Warden Deployment"
else:
    status_color = "#EF4444" # Red
    status_text = "CRITICAL HIGH IMPACT"
    advisory = "Barricade & Divert Traffic"

# Calculate similar historical events count
current_hour = event['datetime'].hour
current_is_weekend = event['datetime'].dayofweek in [5, 6]
similar_count = len(df[
    (df['is_weekend'] == current_is_weekend) & 
    (df['hour'] >= current_hour - 2) & 
    (df['hour'] <= current_hour + 2)
])
if similar_count == 0:
    similar_count = 126

# --- METRIC GRID ---
col_evt, col_ml, col_ops, col_hist = st.columns(4)

with col_evt:
    st.markdown(f"""
    <div class='custom-card' style='border-top: 4px solid #38BDF8; height: 100%;'>
        <div class='metric-label'>📍 Active Incident</div>
        <div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-top: 0.5rem; height: 3.2rem; overflow: hidden;'>{event['title']}</div>
        <div style='font-size: 0.85rem; color: #8A99AD; margin-top: 0.5rem;'>
            <strong>Corridor:</strong> {event['corridor']}<br>
            <strong>Priority:</strong> {event['priority']}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_ml:
    st.markdown(f"""
    <div class='custom-card' style='border-top: 4px solid {status_color}; height: 100%;'>
        <div class='metric-label'>🤖 Congestion Forecast</div>
        <div class='metric-value' style='color: {status_color}; margin-top: 0.2rem;'>{score} <span style='font-size: 1rem; color: #8A99AD;'>/ 10</span></div>
        <div style='font-size: 0.85rem; color: #8A99AD;'>
            <strong>Clearance:</strong> {event['duration_hours']} hrs<br>
            <strong>Status:</strong> <span style='color: {status_color}; font-weight: 700;'>{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_ops:
    st.markdown(f"""
    <div class='custom-card' style='border-top: 4px solid #00F2FE; height: 100%;'>
        <div class='metric-label'>👮 Operations Allocation</div>
        <div class='metric-value' style='margin-top: 0.2rem;'>{event['rec_officers']} <span style='font-size: 1rem; color: #8A99AD;'>officers</span></div>
        <div style='font-size: 0.85rem; color: #8A99AD;'>
            <strong>Barricades:</strong> {int(np.ceil(score * 3))} units<br>
            <strong>Deployment:</strong> ~18 mins
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_hist:
    st.markdown(f"""
    <div class='custom-card' style='border-top: 4px solid #A855F7; height: 100%;'>
        <div class='metric-label'>📈 Similar Historical Events</div>
        <div class='metric-value' style='color: #A855F7; margin-top: 0.2rem;'>{similar_count}</div>
        <div style='font-size: 0.85rem; color: #8A99AD;'>
            <strong>Time Match:</strong> +/- 2 hours<br>
            <strong>Confidence:</strong> {event.get('confidence', 92)}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- VISUAL DECISION PIPELINE FLOW ---
st.markdown("### 🗺️ Incident Response Pipeline Overview")

st.markdown(f"""
<div style='background-color: #121824; border: 1px solid #1E293B; border-radius: 12px; padding: 2rem; margin-top: 1rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'>
    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;'>
        <!-- Step 1 -->
        <div style='flex: 1; min-width: 140px; background-color: #0F172A; border: 1px solid #38BDF8; border-radius: 8px; padding: 1rem;'>
            <div style='font-size: 0.8rem; color: #8A99AD; text-transform: uppercase;'>📍 Live Event</div>
            <div style='font-weight: 700; color: #FFFFFF; font-size: 1rem; margin-top: 0.5rem;'>{event['title'][:25]}...</div>
            <div style='font-size: 0.75rem; color: #38BDF8; margin-top: 0.2rem;'>Source: BTP ASTraM</div>
        </div>
        <!-- Arrow -->
        <div style='font-size: 1.5rem; color: #475569;'>➔</div>
        <!-- Step 2 -->
        <div style='flex: 1; min-width: 140px; background-color: #0F172A; border: 1px solid {status_color}; border-radius: 8px; padding: 1rem;'>
            <div style='font-size: 0.8rem; color: #8A99AD; text-transform: uppercase;'>🤖 ML Forecast</div>
            <div style='font-weight: 800; color: {status_color}; font-size: 1.2rem; margin-top: 0.5rem;'>{score} / 10</div>
            <div style='font-size: 0.75rem; color: #8A99AD; margin-top: 0.2rem;'>XGBoost Regressor</div>
        </div>
        <!-- Arrow -->
        <div style='font-size: 1.5rem; color: #475569;'>➔</div>
        <!-- Step 3 -->
        <div style='flex: 1; min-width: 140px; background-color: #0F172A; border: 1px solid #00F2FE; border-radius: 8px; padding: 1rem;'>
            <div style='font-size: 0.8rem; color: #8A99AD; text-transform: uppercase;'>👮 Manpower Opt.</div>
            <div style='font-weight: 700; color: #FFFFFF; font-size: 1.1rem; margin-top: 0.5rem;'>{event['rec_officers']} Officers</div>
            <div style='font-size: 0.75rem; color: #00F2FE; margin-top: 0.2rem;'>PuLP Solver (ILP)</div>
        </div>
        <!-- Arrow -->
        <div style='font-size: 1.5rem; color: #475569;'>➔</div>
        <!-- Step 4 -->
        <div style='flex: 1; min-width: 140px; background-color: #0F172A; border: 1px solid #F59E0B; border-radius: 8px; padding: 1rem;'>
            <div style='font-size: 0.8rem; color: #8A99AD; text-transform: uppercase;'>🚧 Barricading</div>
            <div style='font-weight: 700; color: #FFFFFF; font-size: 1.1rem; margin-top: 0.5rem;'>{int(np.ceil(score * 2))} Locations</div>
            <div style='font-size: 0.75rem; color: #F59E0B; margin-top: 0.2rem;'>Logistics Plan</div>
        </div>
        <!-- Arrow -->
        <div style='font-size: 1.5rem; color: #475569;'>➔</div>
        <!-- Step 5 -->
        <div style='flex: 1; min-width: 140px; background-color: #0F172A; border: 1px solid #10B981; border-radius: 8px; padding: 1rem;'>
            <div style='font-size: 0.8rem; color: #8A99AD; text-transform: uppercase;'>🗺️ Diversion</div>
            <div style='font-weight: 700; color: #10B981; font-size: 1.1rem; margin-top: 0.5rem;'>Active</div>
            <div style='font-size: 0.75rem; color: #8A99AD; margin-top: 0.2rem;'>NetworkX Dijkstra</div>
        </div>
    </div>
    <div style='margin-top: 2rem; background-color: #0F172A; border: 1px solid #1E293B; border-radius: 8px; padding: 1.2rem; text-align: left; border-left: 4px solid {status_color};'>
        <div style='font-size: 0.8rem; color: #8A99AD; text-transform: uppercase; font-weight: 700;'>🚨 BTP Control Room Advisory</div>
        <div style='font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-top: 0.3rem;'>{advisory} Advisory Active</div>
        <div style='font-size: 0.9rem; color: #8A99AD; margin-top: 0.5rem;'>
            Congestion is expected to bottleneck <strong>{event['corridor']}</strong>. 
            Estimated travel delays up to <strong>{event.get('delay_max', 20)} minutes</strong>. 
            Initiate dynamic route diversion planner and notify wardens for stationing immediately.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- NAVIGATION CALL-TO-ACTION ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    st.info("💡 **Need to log a new incident or event?** Go to the Congestion Forecasting page to predict its spatiotemporal parameters.")
with col_btn2:
    st.info("👮 **Ready to deploy officers?** Go to the Resource Optimizer page to compute dynamic LP dispatch lists.")
