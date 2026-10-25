import streamlit as st
import pandas as pd
import json
import os
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(
    page_title="ChaiRakshak-AI (চাহ-ৰক্ষক) • Precision Drone Operations",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Injection (AgroTelemetry Precision Style)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@600;700&display=swap');
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        color: #005d42;
        font-weight: 700;
        font-size: 1.8rem;
        margin-bottom: 0px;
    }
    .sub-title {
        font-family: 'JetBrains Mono', monospace;
        color: #6e7a73;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# 3. Cached Data Loaders
@st.cache_data
def load_data():
    csv_file = "assam_tea_3year_ndvi_ndre.csv"
    geojson_file = "assam_estate_hotspots.geojson"
    
    df = pd.read_csv(csv_file) if os.path.exists(csv_file) else None
    
    with open(geojson_file, "r") as f:
        geo = json.load(f)
        
    return df, geo

df_temporal, geo_data = load_data()

# 4. Sidebar Navigation
st.sidebar.markdown("""
<div style="display:flex; align-items:center; gap:10px;">
    <div style="background:#005d42; color:white; width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:18px;">চ</div>
    <div>
        <div style="font-weight:bold; font-size:16px; color:#005d42;">ChaiRakshak-AI</div>
        <div style="font-size:10px; color:#6e7a73;">চাহ-ৰক্ষক • v2.6-PRO</div>
    </div>
</div>
<hr style="margin: 12px 0;">
""", unsafe_allow_html=True)

estate_names = [f["properties"]["estate"] for f in geo_data["features"]]
selected_estate = st.sidebar.selectbox("Select Target Estate", estate_names, index=0)

active_feature = next(f for f in geo_data["features"] if f["properties"]["estate"] == selected_estate)
p = active_feature["properties"]

st.sidebar.markdown(f"""
**Operational Status:**
- **District:** `{p['district']}`
- **Section Code:** `{p['section']}`
- **RTK Link:** `Locked (Fixed)`
- **Flight Altitude:** `{p.get('flight_alt', '2.5m AGL')}`
- **Flow Rate:** `{p.get('flow_rate', '1.2 L/min')}`
""")

# 5. Header Bar
st.markdown('<div class="main-title">ChaiRakshak-AI • UAV Precision Spot-Spraying Command Station</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">TRA Tocklai Compliance & DGCA Remote Pilot SOP Operations Hub</div>', unsafe_allow_html=True)

# 6. KPI Grid
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Chemical Reduction", f"{p['chemical_reduction_pct']}%", "vs Blanket Spray")
with col2:
    st.metric("Target Hotspot", f"{p['infected_area_sqm']:,} m²", f"{p['pct_infected']}% of block", delta_color="inverse")
with col3:
    st.metric("Total Cadastral Area", f"{(p['total_estate_sqm']/10000):.1f} ha", "Estate Boundary")
with col4:
    st.metric("Export MRL Risk", "0.0%", "EU & Japan Safe")

st.divider()

# 7. Map & Analytics Grid
map_col, stats_col = st.columns([1.7, 1.3])

with map_col:
    st.markdown(f"#### 📍 Targeted Spot-Spray Zone: {p['estate']}")
    coords = active_feature["geometry"]["coordinates"][0]
    c_lat = sum(pt[1] for pt in coords) / len(coords)
    c_lon = sum(pt[0] for pt in coords) / len(coords)

    m = folium.Map(
        location=[c_lat, c_lon],
        zoom_start=16,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )

    # Add Target Spot-Spray Polygon (Red/Amber)
    folium.GeoJson(
        active_feature,
        name="Targeted Infestation Hotspot",
        style_function=lambda x: {
            "fillColor": "#ba1a1a",
            "color": "#ffffff",
            "weight": 2.5,
            "fillOpacity": 0.75
        },
        tooltip=folium.Tooltip(f"<b>{p['pest_short']}</b><br>Area: {p['infected_area_sqm']:,} m²<br>NDVI: {p['current_ndvi']}")
    ).add_to(m)

    st_folium(m, width="100%", height=460)

with stats_col:
    st.markdown("#### 📊 46-Month Phenology Drift (2023–2026)")
    
    # Filter CSV data by district
    dist_map = {
        'Jorhat': 'Jorhat_Tocklai_Cinnamara',
        'Golaghat/Jorhat': 'Jorhat_Tocklai_Cinnamara',
        'Dibrugarh': 'Dibrugarh_Chabua',
        'Tinsukia': 'Tinsukia_Doomdooma',
        'Sivasagar': 'Sivasagar_Amguri',
        'Charaideo': 'Charaideo_Sonari'
    }
    csv_key = dist_map.get(p["district"], "Tinsukia_Doomdooma")
    
    if df_temporal is not None:
        sub_df = df_temporal[df_temporal["estate"] == csv_key].sort_values("date")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sub_df["date"], y=sub_df["ndvi"], mode="lines+markers", name="NDVI (Canopy)", line=dict(color="#047857", width=2.5)))
        fig.add_trace(go.Scatter(x=sub_df["date"], y=sub_df["ndre"], mode="lines", name="NDRE (Red Edge)", line=dict(color="#6366f1", width=1.5, dash="dash")))
        fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    **Agronomic Spot Prescription:**
    - **Pest Detected:** `{p['pest_type']}` ({int(p['confidence']*100)}% Match)
    - **Active Chemical:** `{p['chemical']}`
    - **Dosage Rate:** `{p['dosage_per_ha']}`
    - **Pre-Harvest Interval (PHI):** `{p['phi_days']} Days Withholding`
    """)

    # Direct Downloads
    st.download_button(
        label=f"📥 Download {p['section']} Drone Mission GeoJSON",
        data=json.dumps(active_feature, indent=2),
        file_name=f"ChaiRakshak_{p['estate'].replace(' ', '_')}.geojson",
        mime="application/json",
        use_container_width=True
    )
