import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk
import folium
from streamlit_folium import folium_static

# Title
st.markdown("<div class='main-title'>🚦 ASTraM Historical Explorer</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Analyze historical traffic incidents and planned events registered in Bengaluru.</div>", unsafe_allow_html=True)

# Check if data exists in session state
if 'df' not in st.session_state:
    st.warning("Please load the app from the main page.")
    st.stop()

df = st.session_state['df']

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filters")

# 1. Date filter
min_date = df['date'].min()
max_date = df['date'].max()
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# 2. Event type (Planned / Unplanned)
event_types = st.sidebar.multiselect(
    "Event Type",
    options=list(df['event_type'].unique()),
    default=list(df['event_type'].unique())
)

# 3. Event Cause
causes = st.sidebar.multiselect(
    "Event Cause",
    options=list(df['event_cause'].unique()),
    default=['accident', 'public_event', 'vehicle_breakdown', 'water_logging', 'construction', 'tree_fall']
)

# 4. Corridor
selected_corridors = st.sidebar.multiselect(
    "Select Corridors",
    options=list(df['corridor'].dropna().unique()),
    default=[] # Empty means all
)

# 5. Zone
selected_zones = st.sidebar.multiselect(
    "Select Zones",
    options=list(df['zone'].dropna().unique()),
    default=[] # Empty means all
)

# 6. Priority
priorities = st.sidebar.multiselect(
    "Priority",
    options=list(df['priority'].dropna().unique()),
    default=list(df['priority'].dropna().unique())
)

# Apply filters
filtered_df = df.copy()

if len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]

if event_types:
    filtered_df = filtered_df[filtered_df['event_type'].isin(event_types)]

if causes:
    filtered_df = filtered_df[filtered_df['event_cause'].isin(causes)]

if selected_corridors:
    filtered_df = filtered_df[filtered_df['corridor'].isin(selected_corridors)]

if selected_zones:
    filtered_df = filtered_df[filtered_df['zone'].isin(selected_zones)]

if priorities:
    filtered_df = filtered_df[filtered_df['priority'].isin(priorities)]

# --- METRIC CARDS ---
col1, col2, col3, col4 = st.columns(4)

total_events = len(filtered_df)
planned_pct = (filtered_df['event_type'] == 'planned').mean() * 100 if total_events > 0 else 0.0
avg_congestion = filtered_df['congestion_impact'].mean() if total_events > 0 else 0.0
closure_pct = (filtered_df['requires_road_closure'] == True).mean() * 100 if total_events > 0 else 0.0

with col1:
    st.markdown(f"""
    <div class='custom-card'>
        <div class='metric-label'>Total Incidents</div>
        <div class='metric-value'>{total_events:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='custom-card'>
        <div class='metric-label'>Planned Events %</div>
        <div class='metric-value'>{planned_pct:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='custom-card'>
        <div class='metric-label'>Avg Congestion Index</div>
        <div class='metric-value'>{avg_congestion:.2f} / 10</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='custom-card'>
        <div class='metric-label'>Road Closures</div>
        <div class='metric-value'>{closure_pct:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- MAPS ---
st.markdown("### 🗺️ Spatiotemporal Distribution Map")

tab1, tab2 = st.tabs(["🔥 3D Congestion Density (Pydeck)", "📍 Interactive Incident Markers (Folium)"])

with tab1:
    if not filtered_df.empty:
        # Pydeck Hexagon Layer for 3D wow effect
        view_state = pdk.ViewState(
            latitude=12.9716, # Bangalore center
            longitude=77.5946,
            zoom=11,
            pitch=50,
            bearing=-27.36
        )
        
        hexagon_layer = pdk.Layer(
            "HexagonLayer",
            data=filtered_df[['longitude', 'latitude', 'congestion_impact']],
            get_position="[longitude, latitude]",
            radius=200,
            elevation_scale=50,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
            coverage=1,
            auto_highlight=True,
            color_range=[
                [0, 242, 254, 50],
                [0, 242, 254, 150],
                [79, 172, 254, 200],
                [255, 75, 75, 230],
                [255, 0, 0, 255]
            ]
        )
        
        r = pdk.Deck(
            layers=[hexagon_layer],
            initial_view_state=view_state,
            tooltip={"text": "Incidents count in area"},
            map_style="mapbox://styles/mapbox/dark-v9"
        )
        st.pydeck_chart(r)
    else:
        st.info("No data available for the selected filters.")

with tab2:
    if not filtered_df.empty:
        # Render a subset of high-congestion events to keep map responsive
        map_df = filtered_df.sort_values(by='congestion_impact', ascending=False).head(200)
        
        m = folium.Map(location=[12.9716, 77.5946], zoom_start=12, tiles="cartodbpositron" if st.get_option("theme.base") == "light" else "CartoDB dark_matter")
        
        # Color coding for causes
        color_map = {
            'accident': 'red',
            'public_event': 'blue',
            'procession': 'purple',
            'protest': 'darkpurple',
            'vehicle_breakdown': 'green',
            'water_logging': 'orange',
            'construction': 'cadetblue',
            'tree_fall': 'darkgreen',
            'others': 'gray'
        }
        
        for idx, row in map_df.iterrows():
            cause = row['event_cause']
            color = color_map.get(cause, 'gray')
            
            popup_html = f"""
            <div style='font-family: sans-serif; font-size: 12px; color: #1E293B;'>
                <b>ID:</b> {row['id']}<br>
                <b>Type:</b> {row['event_type']}<br>
                <b>Cause:</b> {row['event_cause'].upper()}<br>
                <b>Priority:</b> {row['priority']}<br>
                <b>Impact Score:</b> {row['congestion_impact']}/10<br>
                <b>Corridor:</b> {row['corridor']}<br>
                <b>Time:</b> {row['start_datetime'].strftime('%Y-%m-%d %H:%M')}<br>
                <b>Description:</b> {row['description'] if pd.notna(row['description']) else 'N/A'}
            </div>
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)
            
        folium_static(m, width=1100, height=500)
    else:
        st.info("No data available for the selected filters.")

# --- ANALYTICS CHARTS ---
st.markdown("### 📊 Spatiotemporal Traffic Analytics")

col_a, col_b = st.columns(2)

with col_a:
    # 1. Event count by cause
    cause_df = filtered_df['event_cause'].value_counts().reset_index()
    cause_df.columns = ['Cause', 'Count']
    fig_cause = px.bar(
        cause_df, 
        x='Count', 
        y='Cause', 
        orientation='h',
        title='Incidents Distribution by Event Cause',
        template='plotly_dark',
        color='Count',
        color_continuous_scale='Turbo'
    )
    fig_cause.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
    st.plotly_chart(fig_cause, use_container_width=True)

with col_b:
    # 2. Hourly Heatmap (Day of Week vs Hour)
    if not filtered_df.empty:
        heatmap_df = filtered_df.groupby(['day_name', 'hour']).size().unstack(fill_value=0)
        # Order days
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_df = heatmap_df.reindex(days_order)
        
        fig_heat = px.imshow(
            heatmap_df,
            labels=dict(x="Hour of Day", y="Day of Week", color="Incidents Count"),
            x=list(heatmap_df.columns),
            y=list(heatmap_df.index),
            title='Temporal Congestion Heatmap (Hour vs Day)',
            template='plotly_dark',
            color_continuous_scale='Purples'
        )
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No data to display temporal heatmap.")

# 3. Corridor severity ranking (full width)
st.markdown("#### 🏆 Top 15 Congested Corridors")
if not filtered_df.empty:
    corridor_severity = filtered_df.groupby('corridor')['congestion_impact'].agg(['count', 'mean']).reset_index()
    corridor_severity.columns = ['Corridor', 'Incident Count', 'Average Congestion Index']
    corridor_severity = corridor_severity[corridor_severity['Corridor'] != 'Non-corridor']
    corridor_severity = corridor_severity.sort_values(by='Average Congestion Index', ascending=False).head(15)
    
    fig_corr = px.bar(
        corridor_severity,
        x='Average Congestion Index',
        y='Corridor',
        orientation='h',
        color='Incident Count',
        title='Average Congestion Index by Major Corridor (Top 15)',
        template='plotly_dark',
        color_continuous_scale='Reds'
    )
    fig_corr.update_layout(yaxis={'categoryorder': 'total ascending'}, height=450)
    st.plotly_chart(fig_corr, use_container_width=True)
