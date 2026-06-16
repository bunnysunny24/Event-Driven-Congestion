import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import folium
from streamlit_folium import folium_static

# Title
st.markdown("<div class='main-title'>🗺️ Graph-Based Traffic Diversion Planner</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Simulate road closures and compute optimal traffic diversion routes using Graph Theory.</div>", unsafe_allow_html=True)

# Define Bengaluru sub-network graph nodes (key junctions)
junctions = {
    'Jalahalli Cross': {'lat': 13.0400, 'lon': 77.5181},
    'Yeshwanthpur': {'lat': 13.0232, 'lon': 77.5501},
    'Mekhri Circle': {'lat': 13.0084, 'lon': 77.5920},
    'Hebbal Flyover': {'lat': 13.0373, 'lon': 77.5947},
    'K R Puram': {'lat': 13.0040, 'lon': 77.6778},
    'Marathahalli': {'lat': 12.9562, 'lon': 77.6970},
    'Agara HSR': {'lat': 12.9219, 'lon': 77.6452},
    'Silk Board': {'lat': 12.9176, 'lon': 77.6228},
    'Bannerghatta Junction': {'lat': 12.9140, 'lon': 77.5990},
    'Nayandahalli': {'lat': 12.9446, 'lon': 77.5274},
    'K R Circle': {'lat': 12.9731, 'lon': 77.5855},
    'Queens Circle': {'lat': 12.9788, 'lon': 77.5995}
}

# Define edges (road corridors) with distance in km
roads = [
    ('Jalahalli Cross', 'Yeshwanthpur', {'name': 'Tumkur Road', 'distance': 4.2}),
    ('Yeshwanthpur', 'Mekhri Circle', {'name': 'Sankey Road', 'distance': 5.1}),
    ('Mekhri Circle', 'Hebbal Flyover', {'name': 'Bellary Road 1', 'distance': 3.5}),
    ('Hebbal Flyover', 'K R Puram', {'name': 'ORR North', 'distance': 10.2}),
    ('K R Puram', 'Marathahalli', {'name': 'ORR East 2', 'distance': 6.8}),
    ('Marathahalli', 'Agara HSR', {'name': 'ORR East 1', 'distance': 5.5}),
    ('Agara HSR', 'Silk Board', {'name': 'ORR East 1', 'distance': 2.3}),
    ('Silk Board', 'Bannerghatta Junction', {'name': 'ORR South', 'distance': 2.8}),
    ('Bannerghatta Junction', 'Nayandahalli', {'name': 'ORR West 1', 'distance': 8.5}),
    ('Nayandahalli', 'Yeshwanthpur', {'name': 'ORR West 2', 'distance': 9.2}),
    ('Yeshwanthpur', 'K R Circle', {'name': 'Suburban Connect', 'distance': 6.5}),
    ('K R Circle', 'Queens Circle', {'name': 'CBD Link', 'distance': 1.8}),
    ('Queens Circle', 'Mekhri Circle', {'name': 'Bellary Road 2', 'distance': 4.0}),
    ('K R Puram', 'Queens Circle', {'name': 'Old Madras Road', 'distance': 9.5}),
    ('Nayandahalli', 'K R Circle', {'name': 'Mysore Road', 'distance': 7.2}),
    ('Silk Board', 'Queens Circle', {'name': 'Hosur Road', 'distance': 8.2})
]

# Create NetworkX graph
@st.cache_resource
def build_base_graph():
    G = nx.Graph()
    for j_name, j_loc in junctions.items():
        G.add_node(j_name, lat=j_loc['lat'], lon=j_loc['lon'])
    for u, v, data in roads:
        G.add_edge(u, v, name=data['name'], distance=data['distance'], base_time=data['distance'] * 2.5) # assume 2.5 mins per km base (24 km/h)
    return G

G_base = build_base_graph()

# --- SIDEBAR INTERACTION ---
st.sidebar.header("🗺️ Routing Controls")

# Origin / Destination
origin = st.sidebar.selectbox("Start Junction (Origin)", options=list(junctions.keys()), index=0)
destination = st.sidebar.selectbox("End Junction (Destination)", options=list(junctions.keys()), index=4)

if origin == destination:
    st.error("Origin and Destination cannot be the same.")
    st.stop()

# Select blocked corridor
# Try to pre-fill from last prediction
default_blocked_idx = 0
if 'last_prediction' in st.session_state:
    last_corr = st.session_state['last_prediction']['corridor']
    # Find road edge corresponding to corridor
    for i, (u, v, data) in enumerate(roads):
        if data['name'] == last_corr:
            default_blocked_idx = i
            break

blocked_road_idx = st.sidebar.selectbox(
    "Corridor to Simulate Closure / Congestion",
    options=list(range(len(roads))),
    format_func=lambda idx: f"{roads[idx][2]['name']} ({roads[idx][0]} ↔ {roads[idx][1]})",
    index=default_blocked_idx
)

blocked_road = roads[blocked_road_idx]

# Apply congestion multiplier
congestion_factor = st.sidebar.slider("Congestion Multiplier (Delay Factor)", min_value=2.0, max_value=20.0, value=10.0, step=1.0)

# --- COMPUTE PATHS ---
G = G_base.copy()

# Add temporary travel times
for u, v in G.edges:
    G[u][v]['travel_time'] = G[u][v]['base_time']

# Apply penalty to blocked road
u_b, v_b, data_b = blocked_road
if G.has_edge(u_b, v_b):
    G[u_b][v_b]['travel_time'] = G[u_b][v_b]['base_time'] * congestion_factor

# 1. Normal shortest path (using G_base, ignoring blockages)
try:
    normal_path = nx.shortest_path(G_base, source=origin, target=destination, weight='base_time')
    normal_time = nx.shortest_path_length(G_base, source=origin, target=destination, weight='base_time')
    normal_dist = nx.shortest_path_length(G_base, source=origin, target=destination, weight='distance')
except nx.NetworkXNoPath:
    normal_path = []
    normal_time = 0
    normal_dist = 0

# 2. Diverted shortest path (using G, with penalized weight)
try:
    diverted_path = nx.shortest_path(G, source=origin, target=destination, weight='travel_time')
    # calculate total time on the actual graph
    diverted_time = nx.shortest_path_length(G, source=origin, target=destination, weight='travel_time')
    diverted_dist = nx.shortest_path_length(G, source=origin, target=destination, weight='distance')
except nx.NetworkXNoPath:
    diverted_path = []
    diverted_time = 0
    diverted_dist = 0

# Check if paths are identical (meaning no diversion could avoid the blockage)
paths_identical = normal_path == diverted_path

# --- UI VISUALIZATION ---
col_stats, col_desc = st.columns([1.0, 1.2])

with col_stats:
    st.markdown("#### ⚡ Route Comparison")
    
    # Calculate delayed normal path time
    if len(normal_path) > 1:
        delayed_normal_time = sum(G[normal_path[i]][normal_path[i+1]]['travel_time'] for i in range(len(normal_path)-1))
    else:
        delayed_normal_time = normal_time
        
    time_saved = delayed_normal_time - diverted_time if not paths_identical else 0

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='custom-card' style='border-left: 4px solid #EF4444;'>
            <div style='color: #EF4444; font-weight:700; font-size: 0.8rem; letter-spacing: 0.5px;'>WITHOUT DIVERSION</div>
            <div style='font-size: 1.8rem; font-weight: 800; color: #FFFFFF;'>{delayed_normal_time:.1f} <span style='font-size: 0.9rem;'>mins</span></div>
            <div style='font-size: 0.9rem; color: #8A99AD;'>Distance: {normal_dist:.1f} km</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Check if diversion is better or identical
        div_color = "#10B981" if not paths_identical else "#EF4444"
        div_label = "WITH DIVERSION" if not paths_identical else "NO ALTERNATIVE ROUTE"
        st.markdown(f"""
        <div class='custom-card' style='border-left: 4px solid {div_color};'>
            <div style='color: {div_color}; font-weight:700; font-size: 0.8rem; letter-spacing: 0.5px;'>{div_label}</div>
            <div style='font-size: 1.8rem; font-weight: 800; color: #FFFFFF;'>{diverted_time:.1f} <span style='font-size: 0.9rem;'>mins</span></div>
            <div style='font-size: 0.9rem; color: #8A99AD;'>Distance: {diverted_dist:.1f} km</div>
        </div>
        """, unsafe_allow_html=True)
        
    if not paths_identical:
        st.markdown(f"""
        <div style='background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 8px; padding: 0.8rem; margin-top: 1rem; text-align: center;'>
            <div style='color: #10B981; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;'>Travel Time Saved</div>
            <div style='font-size: 2.2rem; font-weight: 800; color: #10B981;'>{time_saved:.1f} mins</div>
            <div style='color: #8A99AD; font-size: 0.85rem; margin-top: 0.2rem;'>By dynamically rerouting away from the congested corridor <strong>{data_b['name']}</strong></div>
        </div>
        """, unsafe_allow_html=True)

with col_desc:
    st.markdown("#### 📋 Route Directions")
    
    st.markdown("**Normal Path:**")
    st.info(" → ".join(normal_path))
    
    st.markdown("**Recommended Diversion:**")
    if paths_identical:
        st.warning("⚠️ Rerouting impossible. Commuters must remain on primary corridor. Heavy traffic delays expected.")
    else:
        st.success(" → ".join(diverted_path))

# --- ROUTING MAP ---
st.markdown("### 🗺️ Dynamic Traffic Rerouting Map")

# Center coordinates
latitudes = [junctions[j]['lat'] for j in junctions]
longitudes = [junctions[j]['lon'] for j in junctions]
m = folium.Map(location=[np.mean(latitudes), np.mean(longitudes)], zoom_start=12.5, tiles="cartodbpositron" if st.get_option("theme.base") == "light" else "CartoDB dark_matter")

# 1. Add all junctions
for name, loc in junctions.items():
    color = 'green' if name == origin else 'red' if name == destination else 'blue'
    icon = 'play' if name == origin else 'stop' if name == destination else 'info-sign'
    folium.Marker(
        location=[loc['lat'], loc['lon']],
        icon=folium.Icon(color=color, icon=icon),
        popup=f"<b>Junction:</b> {name}"
    ).add_to(m)

# 2. Add all roads
for u, v, data in roads:
    u_loc = junctions[u]
    v_loc = junctions[v]
    is_blocked = (u == u_b and v == v_b) or (u == v_b and v == u_b)
    
    # Base color: gray
    color = '#475569'
    weight = 3
    opacity = 0.5
    
    if is_blocked:
        color = '#EF4444' # Glowing red for blocked edge
        weight = 8
        opacity = 0.9
        
    folium.PolyLine(
        locations=[[u_loc['lat'], u_loc['lon']], [v_loc['lat'], v_loc['lon']]],
        color=color,
        weight=weight,
        opacity=opacity,
        tooltip=f"{data['name']} ({u} ↔ {v})" + (" 🚨 CONGESTED" if is_blocked else "")
    ).add_to(m)

# 3. Overlay Normal Path (Dashed Orange Line)
if len(normal_path) > 1:
    points = [[junctions[j]['lat'], junctions[j]['lon']] for j in normal_path]
    folium.PolyLine(
        locations=points,
        color='#F59E0B',
        weight=5,
        opacity=0.8,
        dash_array='10, 10',
        tooltip="Original Route (Delayed)"
    ).add_to(m)

# 4. Overlay Diverted Path (Solid Green Line)
if len(diverted_path) > 1 and not paths_identical:
    points = [[junctions[j]['lat'], junctions[j]['lon']] for j in diverted_path]
    folium.PolyLine(
        locations=points,
        color='#10B981',
        weight=5,
        opacity=0.85,
        tooltip="Recommended Diversion Route"
    ).add_to(m)

# Render map
folium_static(m, width=1100, height=520)
