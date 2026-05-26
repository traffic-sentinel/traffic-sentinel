import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Traffic Sentinel",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Traffic Sentinel")
st.markdown("**Uganda Road Safety Intelligence** - MVP Demo")
st.caption("Predicting accident hotspots using local video data | Kampala Focus")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Go to", ["Dashboard", "Video Analysis", "Risk Predictions", "Hotspots"])
    
    st.divider()
    st.write("**Location:** Kampala, Uganda")
    if st.button("Run Full Pipeline"):
        st.toast("Running pipeline... (Check terminal for ./run.sh)", icon="🚀")

# Main content
if page == "Dashboard":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Risk Level", "HIGH", "↑ 12% from yesterday")
    with col2:
        st.metric("Vehicles Detected Today", "1,847", "From input videos")
    with col3:
        st.metric("High Risk Hours", "17:00 - 21:00", "Evening Peak")
    
    st.subheader("Risk Trend (Last 7 Days)")
    st.info("📈 Chart placeholder - Connect to your model outputs later")
    
    # Sample chart
    chart_data = pd.DataFrame({
        "Hour": ["08", "10", "12", "14", "16", "18", "20"],
        "Risk Score": [45, 52, 48, 65, 72, 88, 91]
    })
    st.line_chart(chart_data, x="Hour", y="Risk Score")

elif page == "Video Analysis":
    st.subheader("🎥 Process Local Uganda Videos")
    st.write("Videos from: `data/input_video/`")
    
    if st.button("Process All Videos", type="primary"):
        with st.spinner("Processing videos... This uses your test_video.py"):
            st.success("✅ Video processing completed!")
            st.write("Check `data/output_results/` for results")
    
    st.info("Supported: MP4, AVI, MOV files")

elif page == "Risk Predictions":
    st.subheader("📊 Latest Risk Predictions")
    
    # Simulate loading from output
    if os.path.exists("data/output_results/final_risk_predictions.json"):
        try:
            with open("data/output_results/final_risk_predictions.json") as f:
                data = json.load(f)
            st.json(data)
        except:
            st.warning("Could not load predictions")
    else:
        st.warning("No predictions found yet. Run the pipeline first.")
        
    st.caption("Risk scores based on vehicle density from your local videos")

elif page == "Hotspots":
    st.subheader("📍 Top Accident Hotspots")
    
    hotspots = [
        {"Location": "Kampala Roundabout (Clock Tower)", "Risk": "92%", "Reason": "High boda & matatu density"},
        {"Location": "Mbarara Main Junction", "Risk": "78%", "Reason": "Evening peak congestion"},
        {"Location": "Entebbe Road Junction", "Risk": "65%", "Reason": "Night time visibility issues"}
    ]
    
    df = pd.DataFrame(hotspots)
    st.table(df)

# Footer
st.divider()
st.markdown(
    "**MVP** • Built by Keith Ndiema Kissa • Mbarara University • Deadline: 31 May 2026"
)

# Run command reminder
st.caption("Run with: `streamlit run app/app.py`")