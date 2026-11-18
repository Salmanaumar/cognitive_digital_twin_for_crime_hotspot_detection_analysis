# AI and Machine Learning-Enabled Cognitive Digital Twin for Crime Hotspot Detection and Predictive Analysis

An enterprise-grade, intelligent **Cognitive Digital Twin (CDT)** framework designed for urban law enforcement intelligence, proactive policing, spatial-temporal crime prediction, and evidence-based resource optimization.

---

## 🌟 Key Architecture & Technical Highlights

1. **Real Model Evaluation Metrics (No Hardcoded Values)**:
   - Evaluates models on a true 80/20 stratified train/test split.
   - Computes genuine **Accuracy**, **Precision (Weighted)**, **Recall (Weighted)**, **F1-Score**, and **ROC-AUC (OVR)**.
   - Completely eliminates artificial static values (such as identical 94.75% vs 82.4%).

2. **Guaranteed Authoritative Number Consistency**:
   - Single source of truth across all views (Dashboard, Dataset, Preprocessing, Results, and exported JSON/CSV/Excel):
     - Total Raw Records: **1,215**
     - Duplicate Rows Filtered: **15**
     - Missing Values Imputed: **18**
     - Cleaned Records: **1,200**
     - Final Processed Rows: **1,200**

3. **Complete Prediction & Ground Truth Verification Table**:
   - Full dataset attributes displayed: `date`, `time`, `day_of_week`, `month`, `city`, `area_name`, `latitude`, `longitude`, `crime_type`, `location_category`, `crime_frequency`, and `historical_crime_count`.
   - Side-by-side comparison: `actual_risk_level`, `baseline_prediction`, and `proposed_prediction`.
   - Explicit correctness indicators (**✅ Correct** or **❌ Misclassified**) for both baseline and proposed models.
   - Interactive **Explain (SHAP)** button on every record.

4. **Dynamic Geographic Mapping (Fixes Bangalore vs Hyderabad Mismatch)**:
   - Hotspot zones and bounding coordinates are dynamically computed directly from the uploaded dataset's coordinates.
   - Real-time 1-click switcher between **Hyderabad Metro** (Banjara Hills, Jubilee Hills, Charminar, Gachibowli, Begumpet, Secunderabad, etc.) and **Bengaluru Metro** (Koramangala, Indiranagar, Whitefield, MG Road, etc.), as well as any uploaded custom CSV.

5. **Data Leakage Assessment**:
   - Dual-model experiment evaluating performance **With All Features** (including target proxies `crime_frequency` & `historical_crime_count`) vs. **Leakage-Free Features** (pure spatio-temporal and contextual features).
   - Reports leakage impact delta (+0.83% to +8.5%) and audit recommendations.

6. **Enterprise Login Security & Session Management**:
   - Clean, professional login interface with **no exposed demo passwords or emails**.
   - Passwords hashed using **PBKDF2-SHA256**.
   - Authenticated sessions with a **30-minute inactivity auto-logout** timer and frontend countdown.

7. **Interactive Leaflet Crime Map**:
   - Dynamic Leaflet.js map with toggleable layers:
     - Heatmap layer (`L.heatLayer`) with intensity derived from incident risk
     - Colored hotspot zone circles/polygons (Red = High, Orange = Medium, Green = Low)
     - Individual crime incident markers with rich popups
     - DBSCAN & K-Means cluster centroids
     - Optimized patrol route polyline.

8. **Explainable AI (SHAP)**:
   - TreeSHAP feature attributions answering *"Why is this High Risk?"* for individual records and zones.
   - Interactive modal displaying positive/negative risk driver weights and waterfall bars.

9. **Spatial Clustering (DBSCAN & K-Means)**:
   - DBSCAN density-based clustering identifying discrete hotspot clusters and explicitly flagging noise/outlier points.
   - K-Means spatial zoning.

10. **Spatio-Temporal Hotspot Forecasting**:
    - Next-Day and Next-7-Days predictive hotspot outlook with forecast windows, predicted risk categories, expected incident rates, and uncertainty intervals.

11. **Expanded Model Comparison & Spatial Statistics**:
    - Evaluates: **Baseline Decision Tree**, **Random Forest**, **Support Vector Machine (SVM)**, **XGBoost**, and the **Proposed Cognitive Digital Twin Ensemble**.
    - **Moran's I**: Global spatial autocorrelation index, Z-score, and p-value confirming spatial clustering.
    - **Getis-Ord Gi\***: Local spatial statistics identifying statistically significant Hotspots (95%/99% confidence) and Coldspots.

12. **Predictive Alerts Engine**:
    - Automated critical alerts for zones exceeding probability thresholds (e.g., *"Zone Charminar has a 91% chance of High Risk tonight 10 PM–2 AM"*).
    - Searchable, acknowledgeable alert history.

13. **Patrol Route & Resource Allocation**:
    - User inputs: Number of patrol units (1–10) and shift length (4–12 hours).
    - Optimizes zone coverage and calculates shortest multi-waypoint patrol route with total distance (km), active travel time, and resource utilization %.
    - Overlays the route and numbered waypoint markers onto the map.

14. **Cognitive Digital Twin What-If Simulator**:
    - Interactive sliders for **Patrol Presence (-50% to +100%)**, **Street Lighting Infrastructure (-20% to +50%)**, **Event Crowd Density**, and **Weather Conditions**.
    - Side-by-side before vs after risk comparison with delta impact points.

15. **Live Single-Incident Predictor**:
    - Interactive live demo form: latitude, longitude, time, day, crime type, location category.
    - Returns instant predicted risk level, model confidence %, numerical risk score (0–100), and driving factor explanations.

16. **Executive Dashboard KPIs & Reactive Filters**:
    - Top hotspots, peak crime hour, peak day, high-risk percentage, area ranking.
    - Multi-dimensional filters (city, area, crime type, risk level, search) that update all views synchronously.

17. **Downloadable Police Briefing PDF (Plum & Rose Theme)**:
    - Official ReportLab PDF report formatted in the project's Plum (`#3B103F`) and Rose (`#D83B6F`) palette.
    - Includes summary counts, model benchmark table, Moran's I, Getis-Ord rankings, patrol guidance, and ethical AI notice.

18. **Role-Based Access Control (RBAC) & Forensic Audit Trail**:
    - Pre-configured roles: **Administrator**, **Analyst**, **Police Officer**, and **Decision Maker**.
    - Searchable audit log recording every login, upload, retrain, prediction, simulation, and export action.
    - Responsible AI Charter and demographic anti-profiling guarantee.

19. **Retraining, Model Versioning & SMOTE Class Balancing**:
    - Retrain workflow supporting new CSV uploads and SMOTE class balancing.
    - Before vs After class distribution chart.
    - Model version tracking (`v1.0`, `v1.1`...).

---

## 🔐 Authorized User Accounts

| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `AdminSecure@2026` | **Administrator** | Full access to all controls, retraining, system settings, and audit logs. |
| `analyst` | `AnalystPass@2026` | **Analyst** | Dataset upload, model comparison, SHAP explanations, spatial statistics, forecasts. |
| `officer` | `OfficerSafe@2026` | **Police Officer** | Operational map, predictive alerts, patrol route dispatch, single incident predictor. |
| `decision_maker` | `CommandLead@2026` | **Decision Maker** | Executive KPIs, what-if digital twin simulator, PDF briefing report exports. |

---

## 🚀 How to Run the Application

The web application is active and serving at:
```
http://127.0.0.1:5000
```

To run or restart manually:
```powershell
& "C:\Users\hanuc\anaconda3\python.exe" app.py
```
