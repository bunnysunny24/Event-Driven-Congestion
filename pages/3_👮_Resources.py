import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import pulp

# Title
st.markdown("<div class='main-title'>👮 Manpower & Barricade Optimizer</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Use Linear Programming to optimize the deployment of traffic officers and barricades during disruptions.</div>", unsafe_allow_html=True)

# Check session state for last predicted event, otherwise use a default
if 'last_prediction' in st.session_state:
    event = st.session_state['last_prediction']
    st.success(f"✅ Loaded active event from Forecasting Engine: **{event['title']}** (Impact Score: **{event['impact_score']}**)")
else:
    # Default event for demonstration
    event = {
        'title': 'Cricket Match at M Chinnaswamy Stadium',
        'type': 'planned',
        'cause': 'public_event',
        'corridor': 'CBD 2',
        'priority': 'High',
        'zone': 'Central Zone 2',
        'road_closure': True,
        'datetime': pd.to_datetime("2026-06-20 16:00:00"),
        'impact_score': 8.5
    }
    st.info("💡 No active event predicted yet. Displaying sample event: **Cricket Match at Chinnaswamy Stadium** (Central Zone). Go to 'Congestion Forecasting' to predict your own event.")

# Define locations (lat/lons) for junctions and police stations near the event zone
# Let's map it based on the zone of the event
zone = event['zone']

# Define some realistic coordinates for Bangalore
# Stations (source of officers)
stations = {
    'Cubbon Park Station': {'lat': 12.9738, 'lon': 77.5960, 'capacity': 40},
    'Halasuru Gate Station': {'lat': 12.9698, 'lon': 77.5898, 'capacity': 30},
    'Shivajinagar Station': {'lat': 12.9863, 'lon': 77.5985, 'capacity': 35},
    'Sadashivanagar Station': {'lat': 13.0068, 'lon': 77.5795, 'capacity': 25},
    'HSR Layout Station': {'lat': 12.9116, 'lon': 77.6389, 'capacity': 30}
}

# Target Junctions (requires officers)
junctions = {
    'Queens Statue Circle': {'lat': 12.9788, 'lon': 77.5995, 'base_req': 5},
    'Mekhri Circle': {'lat': 13.0084, 'lon': 77.5920, 'base_req': 4},
    'K R Circle': {'lat': 12.9731, 'lon': 77.5855, 'base_req': 3},
    'Anil Kumble Circle': {'lat': 12.9758, 'lon': 77.6067, 'base_req': 4},
    'Hudson Circle': {'lat': 12.9691, 'lon': 77.5880, 'base_req': 3}
}

# If the event is in a different zone, let's shift coordinates to show relevancy
if zone == 'North Zone 1' or event['corridor'] == 'Bellary Road 1' or event['corridor'] == 'Bellary Road 2':
    stations = {
        'Hebbala Station': {'lat': 13.0373, 'lon': 77.5947, 'capacity': 40},
        'Kodigehalli Station': {'lat': 13.0634, 'lon': 77.5933, 'capacity': 30},
        'Yelahanka Station': {'lat': 13.0998, 'lon': 77.5943, 'capacity': 35},
        'Jalahalli Station': {'lat': 13.0450, 'lon': 77.5380, 'capacity': 25},
        'Sadashivanagar Station': {'lat': 13.0068, 'lon': 77.5795, 'capacity': 30}
    }
    junctions = {
        'Hebbal Flyover Junction': {'lat': 13.0373, 'lon': 77.5947, 'base_req': 6},
        'Mekhri Circle': {'lat': 13.0084, 'lon': 77.5920, 'base_req': 4},
        'Jalahalli Cross SM Circle': {'lat': 13.0400, 'lon': 77.5181, 'base_req': 3},
        'Yelahanka Circle': {'lat': 13.0998, 'lon': 77.5943, 'base_req': 4},
        'Veerannapalya Junction': {'lat': 13.0426, 'lon': 77.6186, 'base_req': 3}
    }

# Compute travel cost matrix (distance in km)
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

costs = {}
for s_name, s_loc in stations.items():
    costs[s_name] = {}
    for j_name, j_loc in junctions.items():
        costs[s_name][j_name] = haversine_distance(s_loc['lat'], s_loc['lon'], j_loc['lat'], j_loc['lon'])

# Scale junction requirements based on the predicted Congestion Impact Score
impact_factor = event['impact_score'] / 5.0 # baseline scale is 5
closure_multiplier = 1.6 if event['road_closure'] else 1.0

scaled_requirements = {}
for j_name, j_loc in junctions.items():
    req = int(np.ceil(j_loc['base_req'] * impact_factor * closure_multiplier))
    scaled_requirements[j_name] = req

# --- LINEAR PROGRAMMING OPTIMIZATION ---
st.markdown("### ⚙️ Optimization Setup")

st.markdown(r"""
Using **Integer Linear Programming (ILP)**, we allocate available traffic officers from nearby police stations to target junctions.
- **Objective**: Minimize total transit overhead (person-kilometers traveled).
- **Constraints**:
  1. Officers allocated to each junction $\ge$ Required coverage.
  2. Officers drawn from each station $\le$ Station available capacity.
""")

# Define PuLP Problem
prob = pulp.LpProblem("ManpowerAllocation", pulp.LpMinimize)

# Decision Variables: x_s_j = number of officers sent from station s to junction j
x = {}
for s_name in stations:
    for j_name in junctions:
        x[(s_name, j_name)] = pulp.LpVariable(f"x_{s_name.replace(' ', '_')}_{j_name.replace(' ', '_')}", lowBound=0, cat='Integer')

# Objective Function: Minimize sum of distance * officers
prob += pulp.lpSum(costs[s_name][j_name] * x[(s_name, j_name)] for s_name in stations for j_name in junctions)

# Constraints
# 1. Junction Requirements met
for j_name in junctions:
    prob += pulp.lpSum(x[(s_name, j_name)] for s_name in stations) >= scaled_requirements[j_name]

# 2. Station Capacity limits
for s_name in stations:
    prob += pulp.lpSum(x[(s_name, j_name)] for j_name in junctions) <= stations[s_name]['capacity']

# Solve
status = prob.solve()

# --- OPTIMIZATION RESULTS ---
col_stats, col_tbl = st.columns([1.0, 1.2])

with col_stats:
    st.markdown("#### 📊 Optimization Metrics")
    
    if pulp.LpStatus[status] == "Optimal":
        st.success("🎯 **Optimization Status: OPTIMAL SOLUTION FOUND**")
        total_deployed = sum(int(x[(s_name, j_name)].varValue) for s_name in stations for j_name in junctions)
        total_distance_traveled = sum(costs[s_name][j_name] * int(x[(s_name, j_name)].varValue) for s_name in stations for j_name in junctions)
        
        st.metric("Total Officers Deployed", f"{total_deployed} officers")
        st.metric("Total Deployment Overhead", f"{total_distance_traveled:.2f} person-km")
        
        # Calculate man-hours using predicted duration
        duration = event.get('duration_hours', 2.0)
        total_man_hours = total_deployed * duration
        st.metric("Total Personnel Effort", f"{total_man_hours:.1f} officer-hours ({duration} hrs)")
        
        # Barricading requirements
        num_barricades = int(np.ceil(event['impact_score'] * 4.0))
        st.metric("Recommended Barricades Deployed", f"{num_barricades} units")
    else:
        st.error("❌ **Optimization Status: INFEASIBLE / FAILED**")
        st.warning("Junction demand exceeds available police station capacity. Shift personnel from other zones.")

with col_tbl:
    st.markdown("#### 📋 Allocation Matrix")
    if pulp.LpStatus[status] == "Optimal":
        # Create a dataframe showing station -> junction allocations
        matrix = []
        for s_name in stations:
            row = {'Police Station': s_name}
            for j_name in junctions:
                val = int(x[(s_name, j_name)].varValue)
                row[j_name] = val
            row['Total Sent'] = sum(int(x[(s_name, j)].varValue) for j in junctions)
            matrix.append(row)
            
        matrix_df = pd.DataFrame(matrix)
        
        # Add a requirement row at the bottom
        req_row = {'Police Station': '🚨 REQUIRED'}
        for j_name in junctions:
            req_row[j_name] = scaled_requirements[j_name]
        req_row['Total Sent'] = sum(scaled_requirements.values())
        matrix_df = pd.concat([matrix_df, pd.DataFrame([req_row])], ignore_index=True)
        
        st.dataframe(matrix_df, hide_index=True)

# --- VISUAL DEPLOYMENT MAP ---
st.markdown("### 🗺️ Resource Allocation & Barricade Map")

if pulp.LpStatus[status] == "Optimal":
    # Center map on target junctions
    mean_lat = np.mean([loc['lat'] for loc in junctions.values()])
    mean_lon = np.mean([loc['lon'] for loc in junctions.values()])
    
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=13, tiles="cartodbpositron" if st.get_option("theme.base") == "light" else "CartoDB dark_matter")
    
    # 1. Add Target Junctions (Red circles)
    for j_name, j_loc in junctions.items():
        req = scaled_requirements[j_name]
        folium.CircleMarker(
            location=[j_loc['lat'], j_loc['lon']],
            radius=8 + req,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.4,
            popup=f"<b>Junction:</b> {j_name}<br><b>Required Officers:</b> {req}"
        ).add_to(m)
        
    # 2. Add Police Stations (Blue icons)
    for s_name, s_loc in stations.items():
        sent = sum(int(x[(s_name, j)].varValue) for j in junctions)
        folium.Marker(
            location=[s_loc['lat'], s_loc['lon']],
            icon=folium.Icon(color='blue', icon='user'),
            popup=f"<b>Station:</b> {s_name}<br><b>Capacity:</b> {s_loc['capacity']}<br><b>Officers Deployed:</b> {sent}"
        ).add_to(m)
        
    # 3. Add deployment flows (Polyline arcs with thickness depending on volume)
    for s_name in stations:
        for j_name in junctions:
            val = int(x[(s_name, j_name)].varValue)
            if val > 0:
                s_loc = stations[s_name]
                j_loc = junctions[j_name]
                # Draw dashed line
                folium.PolyLine(
                    locations=[[s_loc['lat'], s_loc['lon']], [j_loc['lat'], j_loc['lon']]],
                    color='#38BDF8',
                    weight=1 + val,
                    opacity=0.7,
                    tooltip=f"{s_name} → {j_name}: {val} officers",
                    dash_array='5, 5'
                ).add_to(m)
                
    # 4. Add Barricade Suggestions (Shield icons at high-priority ingress/egress points near junctions)
    # We will simulate 3 specific spots
    barricade_spots = [
        {'name': 'Barricade A (Approach North)', 'lat': mean_lat + 0.005, 'lon': mean_lon + 0.004},
        {'name': 'Barricade B (Approach South)', 'lat': mean_lat - 0.006, 'lon': mean_lon - 0.003},
        {'name': 'Barricade C (Approach West)', 'lat': mean_lat + 0.003, 'lon': mean_lon - 0.007}
    ]
    for spot in barricade_spots:
        folium.Marker(
            location=[spot['lat'], spot['lon']],
            icon=folium.Icon(color='orange', icon='minus-sign'),
            popup=f"<b>Suggested Barricade:</b> {spot['name']}<br>Deploy: {int(np.ceil(num_barricades/3))} units"
        ).add_to(m)
        
    folium_static(m, width=1100, height=500)
else:
    st.warning("No allocation map to show since optimization failed.")
