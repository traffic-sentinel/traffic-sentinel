Traffic Sentinel

Traffic Sentinel is a data-driven traffic intelligence system that predicts accident-prone locations and high-risk time periods using machine learning and spatio-temporal analysis.


Problem

Urban traffic systems in many cities lack predictive intelligence. Accidents often occur in recurring patterns, but current systems react after incidents rather than preventing them.



Solution

Traffic Sentinel analyzes historical traffic and accident data to:

- Predict accident risk levels  
- Identify high-risk locations (hotspots)  
- Detect time-based patterns (rush hours, night risk, etc.)  
- Support data-driven traffic planning and safety interventions  



Features (MVP)

- 🚨 Accident risk prediction model  
- ⏱️ Time-based risk analysis  
- 📍 Identification of high-risk zones  
- 📈 Data exploration and visualization  



Tech Stack

- Python  
- Pandas / NumPy  
- Scikit-learn  
- Matplotlib / Seaborn  
- Streamlit (planned for dashboard)  



Project Structure

traffic-sentinel/
│
├── data/          # datasets (not included in repo)
├── notebooks/     # exploratory analysis & experiments
├── src/           # core scripts and models
├── models/        # trained models (excluded)
├── app/           # dashboard (Streamlit)
├── README.md
└── requirements.txt

Usage

Run Jupyter notebooks for exploration:

```bash
jupyter notebook
```

(Upcoming) Run dashboard:

```bash
streamlit run app/app.py
```

Goal

To build a scalable traffic risk intelligence system that helps reduce accidents and improve urban mobility through predictive analytics.



Future Work

*Geospatial heatmaps of accident hotspots
*Real-time traffic data integration
*Advanced ML models (time series + deep learning)
*Smart traffic system integration

📜 License

This project is licensed under the MIT License.


👤 Author

Keith Ndiema Kissa— Computer Science (Mbarara University of Science and Technology)
