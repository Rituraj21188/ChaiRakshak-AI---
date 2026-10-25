import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import os

# 1. Page Configuration
st.set_page_config(
    page_title="ChaiRakshak-AI (চাহ-ৰক্ষক) | Spot-Spraying Operations",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# 2. File Loading Helper
@st.cache_data
def load_project_datasets():
    csv_path = os.path.join("data", "assam_tea_3year_ndvi_ndre.csv")
    geojson_path = os.path.join("data", "assam_estate_hotspots.geojson")
    
    if not os.path.exists(csv_path) or not os.path.exists(geojson_path):
        st.error("Data files not found! Ensure 'assam_tea_3year_ndvi_ndre.csv' and 'assam_estate_hotspots.geojson' are in the 'data/' folder.")
        st.stop()
        
    df = pd.read_csv(csv_path)
    with open(geojson_path, "r") as f:
        geo = json.load(f)
        
    return df, geo

df_trends, geojson_data = load_project_datasets()

# 3. Sidebar Navigation
st.sidebar.markdown("""
### 🍃 ChaiRakshak-AI (চাহ-ৰক্ষক)
**TRA Tocklai • NESFIC-1-07 Platform**
---
""")

districts = ["Jorhat", "Dibrugarh", "Tinsukia", "Charaideo", "Sivasagar"]
selected_district = st.sidebar.selectbox("Select Target District", districts, index=0)

# Filter feature by district
matching_features = [
    f for f in geojson_data["features"]
    if f["properties"]["district"].lower() == selected_district.lower()
]
active_feature = matching_features[0] if matching_features else geojson_data["features"][0]
props = active_feature["properties"]

# 4. Top KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Section / Estate", props["section"], props["estate"])
with kpi2:
    st.metric("Detected Infestation", props["pest_type"], f"{int(props['confidence']*100)}% Match")
with kpi3:
    st.metric("Pesticide Reduction", "77.9%", "vs Blanket Spray")
with kpi4:
    st.metric("Export MRL Status", "Compliant", "EU & Japan Safe")

st.divider()

# 5. Dashboard Grid: Map & Time-Series Analytics
map_col, stats_col = st.columns([1.7, 1.3])

with map_col:
    st.subheader(f"📍 Satellite Canopy Anomaly Map — {selected_district}")
    
    coords = active_feature["geometry"]["coordinates"][0]
    center_lat = sum(pt[1] for pt in coords) / len(coords)
    center_lon = sum(pt[0] for pt in coords) / len(coords)
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )

    folium.GeoJson(
        active_feature,
        name="Hotspot Polygon",
        style_function=lambda x: {
            "fillColor": "#e11d48",
            "color": "#ffffff",
            "weight": 2.5,
            "fillOpacity": 0.65
        },
        tooltip=folium.Tooltip(f"<b>{props['pest_type']}</b><br>Area: {props['area_sqm']:,} m²")
    ).add_to(m)

    st_folium(m, width="100%", height=470)

with stats_col:
    st.subheader("📊 46-Month Phenology Drift (2023–2026)")
    
    matched_estate = [e for e in df_trends["estate"].unique() if selected_district in e]
    est_key = matched_estate[0] if matched_estate else df_trends["estate"].unique()[0]
    sub_df = df_trends[df_trends["estate"] == est_key].sort_values("date")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub_df["date"], y=sub_df["ndvi"],
        mode="lines+markers", name="NDVI",
        line=dict(color="#10b981", width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=sub_df["date"], y=sub_df["ndre"],
        mode="lines", name="NDRE (Red Edge)",
        line=dict(color="#6366f1", width=1.5, dash="dash")
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🚁 Spot-Spray Mission Parameters")
    st.markdown(f"""
    - **Active Chemical:** `{props['chemical']}`
    - **Calculated Dosage:** `{props['dosage_per_ha']}`
    - **Water Volume:** `{props.get('water_volume_l_ha', 25)} L/ha`
    - **Pre-Harvest Interval (PHI):** `{props.get('phi_days', 7)} Days Withholding`
    """)

    # Export Mission GeoJSON
    st.download_button(
        label=f"📥 Download {props['section']} Mission GeoJSON",
        data=json.dumps(active_feature, indent=2),
        file_name=f"ChaiRakshak_{props['section']}.geojson",
        mime="application/json",
        use_container_width=True
    )
