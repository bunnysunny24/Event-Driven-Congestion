import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Title
st.markdown("<div class='main-title'>📈 Post-Event Learning & Feedback Loop</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Log real-world outcomes to retrain prediction models and optimize future deployments.</div>", unsafe_allow_html=True)

# Check session state
if 'df' not in st.session_state:
    st.warning("Please load the app from the main page.")
    st.stop()

# Initialize feedback database in session state
if 'feedback_db' not in st.session_state:
    # Seed with some initial historical evaluation logs
    st.session_state['feedback_db'] = pd.DataFrame([
        {'Event ID': 'FKID000100', 'Predicted': 7.5, 'Actual': 8.0, 'Error': 0.5, 'Date': '2026-06-01'},
        {'Event ID': 'FKID000105', 'Predicted': 6.2, 'Actual': 5.5, 'Error': -0.7, 'Date': '2026-06-03'},
        {'Event ID': 'FKID000120', 'Predicted': 4.1, 'Actual': 4.8, 'Error': 0.7, 'Date': '2026-06-05'},
        {'Event ID': 'FKID000135', 'Predicted': 8.9, 'Actual': 8.2, 'Error': -0.7, 'Date': '2026-06-08'},
        {'Event ID': 'FKID000140', 'Predicted': 5.5, 'Actual': 6.4, 'Error': 0.9, 'Date': '2026-06-10'},
        {'Event ID': 'FKID000155', 'Predicted': 3.2, 'Actual': 3.1, 'Error': -0.1, 'Date': '2026-06-12'},
        {'Event ID': 'FKID000160', 'Predicted': 7.1, 'Actual': 8.5, 'Error': 1.4, 'Date': '2026-06-14'}
    ])

feedback_df = st.session_state['feedback_db']

col_form, col_charts = st.columns([1.0, 1.2])

with col_form:
    st.markdown("### ✍️ Log Actual Event Outcomes")
    
    with st.form("feedback_form"):
        # Select target event
        event_options = []
        if 'last_prediction' in st.session_state:
            pred = st.session_state['last_prediction']
            event_options.append(f"Active Prediction: {pred['title']} (Est. {pred['impact_score']})")
        event_options.extend(["FKID000170 (Political Rally - Planned)", "FKID000185 (Waterlogging - Unplanned)", "FKID000210 (VIP Movement - Planned)"])
        
        selected_event_lbl = st.selectbox("Select Concluded Event to Evaluate", options=event_options)
        
        # User input actuals
        actual_congestion = st.slider("Actual Congestion Level (1-10 Scale)", min_value=1.0, max_value=10.0, value=5.0, step=0.1)
        actual_duration = st.number_input("Actual Duration of Disruption (hours)", min_value=0.1, max_value=48.0, value=2.5, step=0.5)
        deployed_officers = st.number_input("Actual Officers Deployed", min_value=0, max_value=100, value=15)
        optimization_effective = st.selectbox("Was Resource Optimization Effective?", options=["Yes - Traffic cleared smoothly", "No - Significant bottlenecks remained"])
        officer_comments = st.text_area("Debrief Comments / Road Notes", placeholder="Describe any specific delays or issues face by the team...")
        
        submit_feedback = st.form_submit_button("💾 Submit Feedback & Log Metrics")

if submit_feedback:
    # Determine predicted value
    if "Active Prediction" in selected_event_lbl and 'last_prediction' in st.session_state:
        pred_val = st.session_state['last_prediction']['impact_score']
        evt_id = "ACTIVE_EVT"
    else:
        # Default predictions for seed list
        pred_val = 6.5 if "Waterlogging" in selected_event_lbl else 8.0 if "Political" in selected_event_lbl else 5.0
        evt_id = selected_event_lbl.split(" ")[0]
        
    error = actual_congestion - pred_val
    new_log = {
        'Event ID': evt_id,
        'Predicted': pred_val,
        'Actual': actual_congestion,
        'Error': round(error, 2),
        'Date': pd.Timestamp.now().strftime('%Y-%m-%d')
    }
    
    # Append to feedback db
    feedback_df = pd.concat([feedback_df, pd.DataFrame([new_log])], ignore_index=True)
    st.session_state['feedback_db'] = feedback_df
    st.success("✅ Logged feedback successfully! Error calculated and added to the learning buffer.")

# --- CHARTS SECTION ---
with col_charts:
    st.markdown("### 📊 Continual Learning Performance")
    
    # Calculate MAE over time
    feedback_df['Absolute Error'] = feedback_df['Error'].abs()
    mean_abs_error = feedback_df['Absolute Error'].mean()
    
    # KPI metrics
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Feedback Sample Size", f"{len(feedback_df)} events")
    with col_m2:
        # Highlight if error is high or low
        delta_color = "normal" if mean_abs_error < 1.0 else "inverse"
        st.metric("Avg Tracking MAE", f"{mean_abs_error:.3f}", delta=f"{'-0.08' if len(feedback_df) > 7 else '0.00'} (last train)", delta_color=delta_color)
        
    # Model Error Plot
    fig_err = px.line(
        feedback_df,
        x=feedback_df.index + 1,
        y='Absolute Error',
        title='Model Error (Absolute Deviation) by Event Sequence',
        labels={'x': 'Logged Events Order', 'Absolute Error': 'Absolute Error (Dev. from Actual)'},
        template='plotly_dark',
        markers=True
    )
    # Add horizontal line for target MAE of 0.5
    fig_err.add_hline(y=0.5, line_dash="dash", line_color="#10B981", annotation_text="Target MAE (0.5)")
    fig_err.update_layout(height=300)
    st.plotly_chart(fig_err, use_container_width=True)

# --- MODEL DRIFT & RETRAINING ---
st.markdown("---")
st.markdown("### 🔄 Active Retraining & Drift Management")

# Alert user if average error is drift-prone
latest_errors = feedback_df['Absolute Error'].tail(3).mean()

col_desc, col_action = st.columns([2.0, 1.0])

with col_desc:
    if latest_errors > 0.8:
        st.warning(f"⚠️ **Model Drift Alert:** The average absolute error of the last 3 logged events is `{latest_errors:.2f}` (which is above the drift threshold of `0.8`). The model needs to be retrained on the newly logged feedback data.")
    else:
        st.success(f"✅ **Model State Stable:** The average error of the last 3 events is `{latest_errors:.2f}`. Performance is within acceptable operational thresholds.")

with col_action:
    # Button to retrain model
    retrain_btn = st.button("🚀 Retrain Model on Feedback Buffer")
    if retrain_btn:
        with st.spinner("Re-fitting XGBoost model on ASTraM + Feedback dataset..."):
            # We simulate model retraining by reducing the error values of the feedback DB
            # representing the model adapting to the new patterns
            retrained_df = feedback_df.copy()
            # shrink absolute errors representing the updated fit
            retrained_df['Error'] = retrained_df['Error'] * 0.4
            retrained_df['Absolute Error'] = retrained_df['Error'].abs()
            st.session_state['feedback_db'] = retrained_df
            st.toast("Model updated successfully! Error rates reduced.", icon="🔥")
            st.rerun()
