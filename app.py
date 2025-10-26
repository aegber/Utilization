
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np

# --- Authentication ---
USER_CREDENTIALS = {"ariel": "password123"}

def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if USER_CREDENTIALS.get(username) == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
        else:
            st.sidebar.error("Invalid credentials")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- Database Setup ---
conn = sqlite3.connect("utilization.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS utilization (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, project TEXT, week_ending TEXT, hours_worked REAL, capacity REAL)")
conn.commit()

# --- Data Entry Form ---
st.sidebar.title("Enter Utilization Data")
with st.sidebar.form("entry_form"):
    name = st.text_input("Name")
    project = st.text_input("Project")
    week_ending = st.date_input("Week Ending", value=datetime.today())
    hours_worked = st.number_input("Hours Worked", min_value=0.0, max_value=168.0)
    capacity = st.number_input("Weekly Capacity", min_value=0.0, max_value=168.0, value=40.0)
    submitted = st.form_submit_button("Submit")
    if submitted:
        c.execute("INSERT INTO utilization (name, project, week_ending, hours_worked, capacity) VALUES (?, ?, ?, ?, ?)",
                  (name, project, week_ending.strftime("%Y-%m-%d"), hours_worked, capacity))
        conn.commit()
        st.success("Data submitted successfully!")

# --- Load Data ---
df = pd.read_sql_query("SELECT * FROM utilization", conn)

if df.empty:
    st.info("No data available yet.")
    st.stop()

# --- Data Processing ---
df["week_ending"] = pd.to_datetime(df["week_ending"])
df.sort_values("week_ending", inplace=True)
df["utilization"] = df["hours_worked"] / df["capacity"] * 100
weekly_avg = df.groupby("week_ending")["utilization"].mean().reset_index()

# --- Forecasting ---
X = np.arange(len(weekly_avg)).reshape(-1, 1)
y = weekly_avg["utilization"].values
model = LinearRegression().fit(X, y)
future_weeks = 4
future_X = np.arange(len(weekly_avg), len(weekly_avg) + future_weeks).reshape(-1, 1)
future_dates = [weekly_avg["week_ending"].max() + timedelta(weeks=i+1) for i in range(future_weeks)]
future_y = model.predict(future_X)

forecast_df = pd.DataFrame({"week_ending": future_dates, "utilization": future_y})
forecast_df["type"] = "Forecast"
weekly_avg["type"] = "Actual"
combined_df = pd.concat([weekly_avg, forecast_df])

# --- Plotly Chart ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=weekly_avg["week_ending"], y=weekly_avg["utilization"],
                         mode='lines+markers', name='Actual'))
fig.add_trace(go.Scatter(x=forecast_df["week_ending"], y=forecast_df["utilization"],
                         mode='lines+markers', name='Forecast', line=dict(dash='dash')))
fig.update_layout(title="Team Utilization Forecast", xaxis_title="Week Ending", yaxis_title="Utilization (%)")

# --- Display ---
st.title("Team Utilization Dashboard")
st.plotly_chart(fig)
st.dataframe(combined_df)

# --- CSV Export ---
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download Raw Data as CSV", csv, "team_utilization_data.csv", "text/csv")
