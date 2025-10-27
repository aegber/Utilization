
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- Configuration ---
DB_FILE = "utilization.db"
WEEKLY_CAPACITY = 40

# --- Authentication ---
USER_CREDENTIALS = {
    "ariel": {"password": "password123", "role": "admin"},
    "alex": {"password": "teamwork", "role": "user"},
    "jamie": {"password": "securepass", "role": "user"}
}

# --- Initialize session state ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""

# --- Login ---
def login():
    st.title("🔐 Team Utilization Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = USER_CREDENTIALS[username]["role"]
        else:
            st.error("Invalid username or password")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- Database Setup ---
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS utilization (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        project TEXT,
        description TEXT,
        week TEXT,
        hours REAL
    )
""")
conn.commit()

# --- Sidebar: Data Entry ---
st.sidebar.header("📋 Submit Utilization")
with st.sidebar.form("util_form"):
    project = st.text_input("Project Name")
    description = st.text_input("Project Description")
    week = st.date_input("Week Ending", value=datetime.today())
    hours = st.number_input("Hours Worked", min_value=0.0, max_value=40.0, step=0.5)
    submitted = st.form_submit_button("Submit")
    if submitted:
        c.execute("INSERT INTO utilization (user, project, description, week, hours) VALUES (?, ?, ?, ?, ?)",
                  (st.session_state.username, project, description, week.strftime("%Y-%m-%d"), hours))
        conn.commit()
        st.success("Utilization submitted successfully!")

# --- Load Data ---
data = pd.read_sql_query("SELECT * FROM utilization", conn)
data["week"] = pd.to_datetime(data["week"])

# --- Filters ---
st.sidebar.header("🔍 Filters")
users = ["All"] + sorted(data["user"].unique().tolist())
projects = ["All"] + sorted(data["project"].unique().tolist())
selected_user = st.sidebar.selectbox("User", users)
selected_project = st.sidebar.selectbox("Project", projects)
date_range = st.sidebar.date_input("Date Range", [])

filtered = data.copy()
if selected_user != "All":
    filtered = filtered[filtered["user"] == selected_user]
if selected_project != "All":
    filtered = filtered[filtered["project"] == selected_project]
if len(date_range) == 2:
    filtered = filtered[(filtered["week"] >= pd.to_datetime(date_range[0])) & (filtered["week"] <= pd.to_datetime(date_range[1]))]

# --- Utilization Calculation ---
if not filtered.empty:
    summary = filtered.groupby(["user", "project", "description", "week"], as_index=False)["hours"].sum()
    summary["utilization"] = (summary["hours"] / WEEKLY_CAPACITY) * 100

    st.title("📈 Team Utilization Dashboard")
    st.dataframe(summary)

    fig = px.line(summary, x="week", y="utilization", color="project",
                  line_dash="user", markers=True,
                  title="Weekly Utilization by Project")
    st.plotly_chart(fig)

    csv = summary.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "utilization_summary.csv", "text/csv")

    if st.session_state.role == "admin":
        st.subheader("👥 Admin View: Total Team Utilization")
        team_summary = summary.groupby("week")["utilization"].mean().reset_index()
        fig2 = px.bar(team_summary, x="week", y="utilization", title="Average Team Utilization")
        st.plotly_chart(fig2)
else:
    st.info("No data available for the selected filters.")
