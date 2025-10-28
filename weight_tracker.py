import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ---------- Setup ----------
st.set_page_config("MyWeight Tracker", page_icon="⚖️", layout="centered")

st.title("⚖️ MyWeight Tracker")
st.caption("Track your weight trends over time")

# ---------- Data Storage ----------
# For now, we'll store data in Streamlit session state (resets on app restart)
if "weight_log" not in st.session_state:
    st.session_state.weight_log = pd.DataFrame(columns=["Date", "Weight", "Body Fat %", "Notes"])

# ---------- Input Form ----------
with st.expander("➕ Add New Entry", expanded=True):
    entry_date = st.date_input("Date", value=date.today())
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.1f")
    bodyfat = st.number_input("Body Fat %", min_value=0.0, step=0.1, format="%.1f")
    notes = st.text_area("Notes", placeholder="Optional notes...")
    add_button = st.button("Add Entry")

    if add_button and weight > 0:
        new_row = pd.DataFrame({
            "Date": [entry_date],
            "Weight": [weight],
            "Body Fat %": [bodyfat if bodyfat > 0 else None],
            "Notes": [notes]
        })
        st.session_state.weight_log = pd.concat([st.session_state.weight_log, new_row], ignore_index=True)
        st.success(f"Added {weight:.1f} kg on {entry_date}")
    elif add_button:
        st.warning("Please enter a valid weight before saving.")

# ---------- Data Display ----------
data = st.session_state.weight_log.sort_values("Date")

if not data.empty:
    # Compute a simple trend line (rolling average)
    data["Trend"] = data["Weight"].rolling(window=3).mean()

    # ---------- Chart ----------
    st.subheader("📊 Weight Trend Over Time")
    fig = px.line(
        data,
        x="Date",
        y=["Weight", "Trend"],
        markers=True,
        labels={"value": "Weight (kg)", "variable": "Metric"},
        color_discrete_map={"Weight": "#1f77b4", "Trend": "#ff7f0e"},
    )
    fig.update_layout(height=400, hovermode="x unified")
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

