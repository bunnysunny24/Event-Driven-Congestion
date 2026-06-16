import streamlit as st
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error
import plotly.express as px

# Title
st.markdown("<div class='main-title'>🔮 Congestion Forecasting Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Predict the traffic congestion impact of planned events and sudden road disruptions.</div>", unsafe_allow_html=True)

# Check session state
if 'df' not in st.session_state:
    st.warning("Please load the app from the main page.")
    st.stop()

df = st.session_state['df']

# --- MODEL TRAINING ---
@st.cache_resource
def train_forecasting_model(data):
    # Prepare copy
    train_df = data.copy()
    
    # Fill categorical NaNs
    cat_cols = ['event_type', 'event_cause', 'corridor', 'priority', 'zone']
    for col in cat_cols:
        train_df[col] = train_df[col].fillna('Unknown').astype(str)
        
    train_df['requires_road_closure'] = train_df['requires_road_closure'].astype(int)
    
    # Encoders
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    train_df[cat_cols] = encoder.fit_transform(train_df[cat_cols])
    
    # Define features and target
    features = cat_cols + ['requires_road_closure', 'hour', 'day_of_week']
    X = train_df[features]
    y = train_df['congestion_impact']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train XGBoost
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.08,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Metrics
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    
    # Feature importance
    importance = pd.DataFrame({
        'Feature': features,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    return model, encoder, mae, rmse, importance

# Run training
with st.spinner("Training predictive model..."):
    model, encoder, mae, rmse, feat_importance = train_forecasting_model(df)

# Show model health status in the sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Model Health Status")
st.sidebar.markdown(f"**Model Type:** XGBoost Regressor")
st.sidebar.markdown(f"**Cross-Val MAE:** `{mae:.3f}`")
st.sidebar.markdown(f"**Cross-Val RMSE:** `{rmse:.3f}`")
st.sidebar.markdown(f"**Dataset size:** `{len(df):,}` rows")

# --- UI LAYOUT ---
col_form, col_result = st.columns([1.2, 1.0])

with col_form:
    st.markdown("### 📝 Enter Incident/Event Specifications")
    
    with st.form("forecasting_form"):
        # Basic details
        event_title = st.text_input("Event/Incident Title", placeholder="e.g. Cricket Match, Protests at Freedom Park")
        
        # Categorical selectors
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            evt_type = st.selectbox("Event Type", options=['planned', 'unplanned'])
            evt_cause = st.selectbox("Event Cause", options=list(df['event_cause'].unique()))
            evt_priority = st.selectbox("Priority Level", options=['High', 'Low'])
        with col_f2:
            evt_corridor = st.selectbox("Corridor Affected", options=list(df['corridor'].dropna().unique()))
            evt_zone = st.selectbox("Zone", options=list(df['zone'].dropna().unique()) + ['Unknown'])
            road_closure = st.selectbox("Requires Road Closure?", options=[False, True])
            
        # DateTime picker
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            est_date = st.date_input("Estimated Date")
        with col_d2:
            est_time = st.time_input("Estimated Time")
            
        submit_btn = st.form_submit_button("🔮 Predict Congestion Impact")

# Save inputs in session state so Page 3 (Resources) and Page 4 (Diversions) can access it
if submit_btn:
    # Feature preparation
    est_datetime = pd.to_datetime(f"{est_date} {est_time}")
    hour = est_datetime.hour
    day_of_week = est_datetime.dayofweek
    
    input_data = pd.DataFrame([{
        'event_type': evt_type,
        'event_cause': evt_cause,
        'corridor': evt_corridor,
        'priority': evt_priority,
        'zone': evt_zone,
        'requires_road_closure': int(road_closure),
        'hour': hour,
        'day_of_week': day_of_week
    }])
    
    # Encode
    cat_cols = ['event_type', 'event_cause', 'corridor', 'priority', 'zone']
    input_data[cat_cols] = encoder.transform(input_data[cat_cols])
    
    # Predict
    predicted_impact = model.predict(input_data)[0]
    predicted_impact = float(np.clip(predicted_impact, 1.0, 10.0))
    
    # Store in session state
    st.session_state['last_prediction'] = {
        'title': event_title if event_title else "Unnamed Event",
        'type': evt_type,
        'cause': evt_cause,
        'corridor': evt_corridor,
        'priority': evt_priority,
        'zone': evt_zone,
        'road_closure': road_closure,
        'datetime': est_datetime,
        'impact_score': round(predicted_impact, 1)
    }

# --- DISPLAY RESULTS ---
with col_result:
    st.markdown("### 🔮 Predicted Impact Analysis")
    
    if 'last_prediction' in st.session_state:
        pred = st.session_state['last_prediction']
        
        # Color coding
        score = pred['impact_score']
        if score < 4.0:
            status_color = "#10B981" # Green
            status_text = "LOW IMPACT"
            alert_class = "success"
        elif score < 7.0:
            status_color = "#F59E0B" # Orange
            status_text = "MEDIUM IMPACT"
            alert_class = "warning"
        else:
            status_color = "#EF4444" # Red
            status_text = "CRITICAL HIGH IMPACT"
            alert_class = "error"
            
        # Display Glowing Score card
        st.markdown(f"""
        <div style='background-color: #121824; border: 2px solid {status_color}; border-radius: 12px; padding: 2rem; text-align: center; box-shadow: 0 0 15px rgba({",".join([str(int(status_color[i:i+2], 16)) for i in (1, 3, 5)] if status_color.startswith('#') else '255, 255, 255')}, 0.2);'>
            <div style='font-size: 0.9rem; color: #8A99AD; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;'>Predicted Congestion Index</div>
            <div style='font-size: 4.5rem; font-weight: 800; color: {status_color}; line-height: 1; margin: 1rem 0;'>{score} <span style='font-size: 1.5rem; font-weight: 400; color: #8A99AD;'>/ 10</span></div>
            <div style='background-color: rgba({",".join([str(int(status_color[i:i+2], 16)) for i in (1, 3, 5)] if status_color.startswith('#') else '255, 255, 255')}, 0.1); color: {status_color}; font-weight: 700; display: inline-block; padding: 0.5rem 1.5rem; border-radius: 20px; font-size: 1rem; border: 1px solid {status_color};'>
                {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Suggested Actions Alert
        st.markdown("<br>", unsafe_allow_html=True)
        if score < 4.0:
            st.success(f"💡 **BTP Advisory:** Standard monitoring required. Routine patrol units in {pred['corridor']} can handle it. No barricading needed.")
        elif score < 7.0:
            st.warning(f"⚠️ **BTP Advisory:** Moderate traffic spillover expected. Station 2-4 traffic wardens at key junctions in {pred['corridor']}. Update Variable Message Signs (VMS) nearby.")
        else:
            st.error(f"🚨 **BTP Advisory:** High potential for traffic gridlock on {pred['corridor']}. Deploy immediate barricading at approach corridors, initiate signal plan adjustments (BATCS), and activate traffic diversion routes immediately.")
            
        st.info("👉 **Proceed to the 'Resource Optimizer' page** to calculate optimal officer deployment and barricade locations for this event.")
        
    else:
        st.info("👈 Fill out the specifications form and click 'Predict Congestion Impact' to run the ML model.")

# --- FEATURE IMPORTANCE CHART ---
st.markdown("### 🔍 Model Interpretability (Explainable AI)")
fig_feat = px.bar(
    feat_importance,
    x='Importance',
    y='Feature',
    orientation='h',
    title='XGBoost Feature Importance Ranking (What drives congestion?)',
    template='plotly_dark',
    color='Importance',
    color_continuous_scale='Bluered_r'
)
fig_feat.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350)
st.plotly_chart(fig_feat, use_container_width=True)
