import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from datetime import date

# ============================================================
# ⚙️ Setup
# ============================================================
st.set_page_config("My Health Tracker", page_icon="⚕️", layout="centered")

st.title("⚕️ My Health Tracker")
st.caption("Track your weight, body fat, and blood pressure trends over time")

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "health_data.db")
os.makedirs(DB_DIR, exist_ok=True)


# ============================================================
# 🧱 Database Setup
# ============================================================
def init_db():
    """Create the SQLite databse and weights table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for weights
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            weight REAL NOT NULL,
            body_fat REAL,
            notes TEXT    
        )

    """)

    # Table for blood pressure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_pressure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            systolic INTEGER NOT NULL,
            diastolic INTEGER NOT NULL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_weight(entry_date, weight, body_fat, notes):
    """Insert a new record into the weights table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weights (date, weight, body_fat, notes)
        VALUES (?,?,?,?)
    """, (entry_date,weight,body_fat,notes)
    )
    conn.commit()
    conn.close()

def insert_bp(entry_date, systolic, diastolic, notes):
    """Insert a new record into the blood pressure table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO blood_pressure (date, systolic, diastolic, notes)
        VALUES (?,?,?,?)
    """, (entry_date,systolic,diastolic,notes))
    conn.commit()
    conn.close()


def load_weights():
    """Load all weight records from the database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM weights ORDER BY date ASC", conn)
    conn.close()
    return df

def load_bp():
    """Load all blood pressure records from the database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM blood_pressure ORDER BY date ASC", conn)
    conn.close()
    return df

# Initialize Database
init_db()

# ============================================================
# 🧭 Sidebar Navigation
# ============================================================

section = st.sidebar.radio(
    "Select Section",
    ["⚖️ Weight Tracker", "🩺 Blood Pressure Tracker"]
)


# ============================================================
# ⚖️ Weight Tracker Section
# ============================================================

if section == "⚖️ Weight Tracker":
    st.header("⚖️ Weight Tracker")

    # ---------- Input Form ----------
    with st.expander("➕ Add New Entry", expanded=True):
        entry_date = st.date_input("Date", value=date.today())
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.1f")
        bodyfat = st.number_input("Body Fat %", min_value=0.0, step=0.1, format="%.1f")
        notes = st.text_area("Notes", placeholder="Optional notes...")
        add_button = st.button("Add Weight Entry")

        if add_button and weight > 0:
            insert_weight(entry_date.isoformat(), weight, bodyfat if bodyfat > 0 else None, notes)
            st.success(f"Added {weight:.1f} kg on {entry_date}")
        elif add_button:
            st.warning("Please enter a valid weight before saving.")

    # ---------- Data Display ----------
    data = load_weights()

    if not data.empty:
        data["date"] = pd.to_datetime(data["date"])
        data = data.rename(columns={
            "date":"Date", 
            "weight":"Weight",
            "body_fat":"Body Fat %",
            "notes":"Notes"
        })

        targetWeight = 100

        minWeight = data["Weight"].min() if data["Weight"].min() < targetWeight else targetWeight
        maxWeight = data["Weight"].max()
        
        minTargetBodyFat = 11
        maxTargetBodyFat = 20
        minBodyFat = data["Body Fat %"].min() if data["Body Fat %"].min() < minTargetBodyFat else minTargetBodyFat
        maxBodyFat = data["Body Fat %"].max()

        # ---------- Chart ----------
        st.subheader("📊 Weight Trend Over Time")
        fig = px.line(
            data,
            x="Date",
            y=["Weight"],
            markers=True,
            labels={"value": "Weight (kg)", "variable": "Metric"},
            color_discrete_map={"Weight": "#1f77b4"},
        )
        fig.update_layout(height=400, hovermode="x unified")
        fig.update_layout(yaxis_range=[(minWeight-10),(maxWeight+10)])
        fig.update_layout(showlegend=False)
        fig.add_hline(y=targetWeight, line_color="green")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Body Fat % Trend Over Time")
        fig = px.line(
            data,
            x="Date",
            y=["Body Fat %"],
            markers=True,
            labels={"value": "Body Fat (%)", "variable": "Metric"},
            color_discrete_map={"Body Fat %": "#F54927"},
        )
        fig.update_layout(height=400, hovermode="x unified")
        fig.update_layout(yaxis_range=[(minBodyFat-5),(maxBodyFat+5)])
        fig.add_hrect(
            y0=minTargetBodyFat, y1=maxTargetBodyFat, 
            line_width=0, fillcolor="green", opacity=0.2)
        fig.update_layout(showlegend=False)    
        st.plotly_chart(fig, use_container_width=True)

        # ---------- Stats ----------
        st.subheader("📈 Summary Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Latest Weight", f"{data.iloc[-1]['Weight']:.1f} kg")
        col2.metric("Average", f"{data['Weight'].mean():.1f} kg")
        if len(data) > 1:
            change = data.iloc[-1]['Weight'] - data.iloc[0]['Weight']
            col3.metric("Change", f"{change:+.1f} kg")
        else:
            col3.metric("Change", "N/A")

        # ---------- Table ----------
        st.subheader("🧾 Weight Log")
        st.dataframe(data[["Date", "Weight", "Body Fat %", "Notes"]].sort_values("Date", ascending=False), use_container_width=True)

        # ---------- Export ----------
        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Download CSV", csv, "weight_log.csv", "text/csv")

    else:
        st.info("No data yet. Add your first entry above!")

# ============================================================
# 🩺 Blood Pressure Tracker Section
# ============================================================

elif section == "🩺 Blood Pressure Tracker":
    st.header("🩺 Blood Pressure Tracker")

    # ---------- Input Form ----------
    with st.expander("➕ Add New Reading", expanded=True):
        entry_date = st.date_input("Date", value=date.today(), key="bp_date")
        systolic = st.number_input("Systolic (mmHg)", min_value=0, step=1)
        diastolic = st.number_input("Diastolic (mmHg)", min_value=0, step=1)
        notes = st.text_area("Notes", placeholder="Optional notes (e.g. morning, post-workout)")
        add_bp_button = st.button("Add BP Reading")

        if add_bp_button and systolic > 0 and diastolic > 0:
            insert_bp(entry_date.isoformat(), systolic, diastolic, notes)
            st.success(f"✅ Added BP reading {systolic}/{diastolic} mmHg on {entry_date}")
        elif add_bp_button:
            st.warning("Please enter valid blood pressure values before saving.")

    # ---------- Data Display ----------
    data_bp = load_bp()

    if not data_bp.empty:
        data_bp["date"] = pd.to_datetime(data_bp["date"])
        data_bp = data_bp.rename(columns={"date": "Date", "systolic": "Systolic", "diastolic": "Diastolic", "notes": "Notes"})

        minTargetSystolic = 100
        maxTargetSystolic = 120
        minTargetDiastolic = 60
        maxTargetDiastolic = 80

        minSystolic = data_bp["Systolic"].min()
        maxSystolic = data_bp["Systolic"].max()
        minDiastolic = data_bp["Diastolic"].min() if data_bp["Diastolic"].min() < minTargetDiastolic else minTargetDiastolic
        maxDiastolic = data_bp["Diastolic"].max()

        # ---------- Chart ----------
        st.subheader("📊 Blood Pressure Trends")
        fig_bp = px.line(
            data_bp,
            x="Date",
            y=["Systolic", "Diastolic"],
            markers=True,
            labels={"value": "mmHg", "variable": "Pressure"},
            color_discrete_map={"Systolic": "#ef4444", "Diastolic": "#3b82f6"},
        )
        fig_bp.update_layout(height=400, hovermode="x unified")
        fig_bp.update_layout(yaxis_range=[(minDiastolic-5),(maxSystolic+10)])
        fig_bp.add_hrect(y0=minTargetSystolic, y1=maxTargetSystolic, line_width=0, fillcolor="red", opacity=0.2)
        fig_bp.add_hrect(y0=minTargetDiastolic, y1=maxTargetDiastolic, line_width=0, fillcolor="blue", opacity=0.2)
        st.plotly_chart(fig_bp, use_container_width=True)

        # ---------- Stats ----------
        st.subheader("📈 Summary Stats")
        col1, col2 = st.columns(2)
        col1.metric("Avg Systolic", f"{data_bp['Systolic'].mean():.0f} mmHg")
        col2.metric("Avg Diastolic", f"{data_bp['Diastolic'].mean():.0f} mmHg")

        # ---------- Table ----------
        st.subheader("🧾 Blood Pressure Log")
        st.dataframe(
            data_bp[["Date", "Systolic", "Diastolic", "Notes"]].sort_values("Date", ascending=False),
            use_container_width=True,
        )

        # ---------- Export ----------
        csv_bp = data_bp.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Download BP CSV", csv_bp, "blood_pressure_log.csv", "text/csv")

    else:
        st.info("No blood pressure readings yet. Add your first entry above!")

st.caption("💾 Entries are saved in a local SQLite database (`data/health_data.db`).")
