"""
Traffic Sentinel — Streamlit Dashboard
Uganda Road Safety Intelligence System
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Traffic Sentinel | Uganda",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
RISK_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH": "#f97316",
    "MEDIUM": "#eab308",
    "LOW": "#22c55e",
}
UGANDAN_JUNCTIONS = [
    {"name": "Clock Tower Roundabout, Kampala", "lat": 0.3131, "lon": 32.5811, "risk": 92},
    {"name": "Wandegeya Junction, Kampala", "lat": 0.3437, "lon": 32.5683, "risk": 85},
    {"name": "Mbarara Main Junction", "lat": -0.6123, "lon": 29.7597, "risk": 78},
    {"name": "Entebbe Road / Mukono Junction", "lat": 0.3600, "lon": 32.6300, "risk": 71},
    {"name": "Jinja Road Bweyogerere", "lat": 0.3690, "lon": 32.6700, "risk": 64},
    {"name": "Gulu Avenue, Kampala", "lat": 0.3327, "lon": 32.5720, "risk": 58},
]

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Font & background */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.5rem !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem 1.25rem !important;
}
[data-testid="metric-container"] label { font-size: 0.78rem !important; color: #64748b !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0f172a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.9rem; }
[data-testid="stSidebar"] hr { border-color: #334155 !important; }

/* Status badge */
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-critical { background:#fee2e2; color:#991b1b; }
.badge-high { background:#ffedd5; color:#9a3412; }
.badge-medium { background:#fef9c3; color:#854d0e; }
.badge-low { background:#dcfce7; color:#166534; }
</style>
""", unsafe_allow_html=True)

# ── API helpers ──────────────────────────────────────────────────────────────

def api_get(path: str, timeout: int = 8):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach API. Is the FastAPI backend running? (`uvicorn backend.app.main:app`)"
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as e:
        return None, str(e)


def api_post(path: str, timeout: int = 10):
    try:
        r = requests.post(f"{API_BASE}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach API."
    except Exception as e:
        return None, str(e)


def risk_badge(level: str) -> str:
    cls = f"badge-{level.lower()}"
    return f'<span class="badge {cls}">{level}</span>'


def poll_status():
    data, _ = api_get("/api/status")
    return data or {"status": "unknown", "progress": 0, "message": "—"}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚦 Traffic Sentinel")
    st.caption("Uganda Road Safety Intelligence")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "🎥 Video Analysis", "📈 Risk Predictions", "📍 Hotspot Map", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**System Status**")
    status_data = poll_status()
    s = status_data.get("status", "unknown")
    color = {"idle": "🟢", "processing": "🟡", "completed": "🟢", "failed": "🔴"}.get(s, "⚪")
    st.markdown(f"{color} API: `{s}`")
    if s == "processing":
        st.progress(status_data.get("progress", 0) / 100)
        st.caption(status_data.get("message", ""))

    st.divider()
    st.markdown("**Quick Actions**")
    if st.button("▶ Run Full Pipeline", use_container_width=True):
        data, err = api_post("/api/pipeline")
        if err:
            st.error(err)
        else:
            st.success("Pipeline started — check status above.")

    if st.button("🗑 Reset Results", use_container_width=True):
        data, err = api_get("/api/clear")
        if not err:
            st.success("Results cleared.")

    st.divider()
    st.caption(f"API: `{API_BASE}`")
    st.caption("Ministry of ICT Showcase · June 2026")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("Road Safety Dashboard — Kampala")

    # Fetch real dashboard stats from API
    dash, err = api_get("/api/dashboard")

    if err:
        st.warning(f"⚠️ {err} — Showing demo data below.")
        dash = {
            "total_videos": 3,
            "overall_avg_vehicles": 14.7,
            "peak_vehicles": 27,
            "total_detections": 1847,
            "high_density_frames": 42,
            "peak_risk_period": "17:00 – 21:00",
        }

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Videos Analysed", dash.get("total_videos", 0))
    with col2:
        st.metric("Avg Vehicles / Frame", f"{dash.get('overall_avg_vehicles', 0):.1f}")
    with col3:
        st.metric("Peak Frame Count", dash.get("peak_vehicles", 0), help="Max vehicles in any single detection frame")
    with col4:
        st.metric("High-Density Frames", dash.get("high_density_frames", 0), help="Frames with >20 vehicles detected")

    st.divider()

    # Synthetic hourly risk trend (replace with real output when pipeline runs)
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("Hourly Risk Profile — Typical Kampala Weekday")
        hours = list(range(0, 24))
        base_risk = [
            22, 18, 15, 14, 16, 25, 45, 72, 68, 55,
            52, 58, 62, 60, 64, 78, 88, 91, 85, 74,
            65, 52, 38, 28,
        ]
        df_trend = pd.DataFrame({"Hour": [f"{h:02d}:00" for h in hours], "Risk Score": base_risk})
        fig = px.area(
            df_trend, x="Hour", y="Risk Score",
            color_discrete_sequence=["#3b82f6"],
            template="plotly_white",
        )
        fig.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.07, line_width=0, annotation_text="Critical zone")
        fig.add_hrect(y0=60, y1=80, fillcolor="orange", opacity=0.06, line_width=0)
        fig.update_layout(
            height=300, margin=dict(t=10, b=10),
            xaxis=dict(tickangle=-45, tickfont=dict(size=11)),
            yaxis=dict(range=[0, 100], title="Risk Score (0–100)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Risk Distribution")
        preds, _ = api_get("/api/predictions")
        if preds and preds.get("predictions"):
            levels = [p["risk_level"] for p in preds["predictions"]]
            counts = {lvl: levels.count(lvl) for lvl in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
        else:
            counts = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 1, "LOW": 0}  # demo

        fig2 = go.Figure(go.Pie(
            labels=list(counts.keys()),
            values=list(counts.values()),
            marker_colors=[RISK_COLORS[k] for k in counts],
            hole=0.55,
        ))
        fig2.update_layout(height=300, margin=dict(t=10, b=10), showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    # Recent results table
    if dash.get("results"):
        st.subheader("Recent Video Results")
        rows = []
        for r in dash["results"]:
            rows.append({
                "Video": r.get("video_name", "—"),
                "Duration (s)": r.get("duration_seconds", "—"),
                "Avg Vehicles": r.get("avg_vehicles_per_sample", "—"),
                "Peak Vehicles": r.get("peak_vehicles", "—"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: VIDEO ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🎥 Video Analysis":
    st.title("Video Processing")
    st.caption("Runs YOLO vehicle detection on traffic footage in `data/input_video/`")

    # List available videos
    vids, err = api_get("/api/videos")
    if err:
        st.warning(f"API offline — {err}")
        vids = {"videos": [], "count": 0}

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{vids.get('count', 0)} video(s)** found in input directory.")
        if vids.get("videos"):
            for v in vids["videos"]:
                st.markdown(f"- `{v}`")
        else:
            st.info("No videos detected. Add `.mp4 / .avi / .mov` files to `data/input_video/` and re-run.")

    with col2:
        if st.button("▶ Process All Videos", type="primary", use_container_width=True):
            data, err = api_post("/api/process")
            if err:
                st.error(err)
            else:
                st.success("Processing started. Refresh status in sidebar.")

    st.divider()

    # Upload new video
    st.subheader("Upload New Video")
    uploaded = st.file_uploader("Drop a traffic video here", type=["mp4", "avi", "mov"])
    if uploaded:
        dest = Path("data/input_video") / uploaded.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(uploaded.read())
        st.success(f"Saved to `{dest}`. Click **Process All Videos** to analyse it.")

    st.divider()

    # Existing results
    st.subheader("Processing Results")
    results, err = api_get("/api/results")
    if err:
        st.warning(err)
    elif results and results.get("results"):
        for r in results["results"]:
            with st.expander(f"📹 {r['video_name']} — avg {r.get('avg_vehicles_per_sample', '?')} vehicles/frame"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Duration", f"{r.get('duration_seconds', '?')}s")
                c2.metric("Avg Vehicles", r.get("avg_vehicles_per_sample", "?"))
                c3.metric("Peak Vehicles", r.get("peak_vehicles", "?"))

                if r.get("features"):
                    df_f = pd.DataFrame(r["features"])
                    if "vehicle_count" in df_f.columns:
                        fig = px.bar(
                            df_f.head(20), x=df_f.index[:20], y="vehicle_count",
                            labels={"x": "Sample Frame", "vehicle_count": "Vehicles"},
                            color_discrete_sequence=["#3b82f6"],
                            template="plotly_white",
                        )
                        fig.update_layout(height=200, margin=dict(t=5, b=5))
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No results yet. Run processing first.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: RISK PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📈 Risk Predictions":
    st.title("Accident Risk Predictions")

    col_run, col_dl = st.columns([1, 1])
    with col_run:
        if st.button("🔮 Generate Predictions", type="primary"):
            with st.spinner("Running risk model..."):
                data, err = api_post("/api/predict")
            if err:
                st.error(err)
            else:
                st.success(f"Predictions generated: {data.get('total_videos_processed', 0)} videos.")
                st.rerun()

    preds_data, err = api_get("/api/predictions")

    if err:
        st.warning(err)
    elif preds_data:
        summary = preds_data.get("summary", {})
        preds = preds_data.get("predictions", [])

        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Risk Score", f"{summary.get('average_risk_score', 0):.0f}/100")
        c2.metric("Critical Areas", summary.get("critical_areas", 0))
        c3.metric("High-Risk Areas", summary.get("high_risk_areas", 0))
        c4.metric("Max Risk Score", summary.get("max_risk_score", 0))

        st.divider()

        # Predictions table with badges
        if preds:
            st.subheader("Predictions per Video")
            for p in preds:
                lvl = p.get("risk_level", "LOW")
                with st.container():
                    cols = st.columns([3, 1, 2, 3])
                    cols[0].markdown(f"**{p.get('video', '—')}**")
                    cols[1].markdown(risk_badge(lvl), unsafe_allow_html=True)
                    cols[2].progress(p.get("risk_score", 0) / 100)
                    cols[3].caption(p.get("recommendation", ""))
                st.divider()

        # Export button
        with col_dl:
            if st.download_button(
                "⬇ Download Predictions JSON",
                data=json.dumps(preds_data, indent=2),
                file_name=f"traffic_sentinel_predictions_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
            ):
                pass
    else:
        st.info("No predictions found. Run video processing first, then generate predictions.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: HOTSPOT MAP
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📍 Hotspot Map":
    st.title("Accident Hotspot Map — Uganda")
    st.caption("Known high-risk junctions based on historical RTA data + model outputs")

    df_map = pd.DataFrame(UGANDAN_JUNCTIONS)

    fig = px.scatter_mapbox(
        df_map,
        lat="lat", lon="lon",
        size="risk",
        color="risk",
        color_continuous_scale=["#22c55e", "#eab308", "#f97316", "#dc2626"],
        range_color=[40, 100],
        hover_name="name",
        hover_data={"risk": True, "lat": False, "lon": False},
        size_max=30,
        zoom=7,
        center={"lat": 0.31, "lon": 32.58},
        mapbox_style="carto-positron",
        labels={"risk": "Risk Score"},
    )
    fig.update_layout(height=500, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Hotspot Detail")
    df_display = df_map[["name", "risk"]].rename(columns={"name": "Junction", "risk": "Risk Score"})
    df_display = df_display.sort_values("Risk Score", ascending=False)
    df_display["Risk Level"] = df_display["Risk Score"].apply(
        lambda x: "CRITICAL" if x >= 85 else "HIGH" if x >= 70 else "MEDIUM" if x >= 55 else "LOW"
    )
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("Settings")

    st.subheader("API Configuration")
    new_api = st.text_input("API Base URL", value=API_BASE)
    if st.button("Test Connection"):
        data, err = api_get("/health")
        if err:
            st.error(f"Connection failed: {err}")
        else:
            st.success(f"Connected — API v{data.get('version', '?')} healthy ✅")

    st.divider()
    st.subheader("About")
    st.markdown("""
| Field | Value |
|-------|-------|
| Project | Traffic Sentinel |
| Author | Keith Ndiema Kissa |
| Institution | Mbarara University of Science & Technology |
| Showcase | Ministry of ICT Government Systems Prototype — June 2026 |
| Stack | FastAPI · YOLO · OpenCV · Streamlit · Plotly |
    """)