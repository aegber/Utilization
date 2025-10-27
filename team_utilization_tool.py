" + __import__('textwrap').dedent('''
import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime
import plotly.express as px

# File paths
USER_FILE = "users.csv"
UTIL_FILE = "utilization.csv"

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["username", "password", "role"])

def save_user(username, password, role="user"):
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), role]], columns=["username", "password", "role"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)
    user = users[(users["username"] == username) & (users["password"] == hashed)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

def save_utilization(username, project, date, percentage):
    if os.path.exists(UTIL_FILE):
        df = pd.read_csv(UTIL_FILE)
    else:
        df = pd.DataFrame(columns=["username", "project", "date", "percentage"])
    new_entry = pd.DataFrame([[username, project, date, percentage]], columns=["username", "project", "date", "percentage"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(UTIL_FILE, index=False)

def weekly_summary(df):
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%d/%m"))
    summary = df.groupby(["username", "project", "week"]).agg({"percentage": "sum"}).reset_index()
    return summary

# UI Components
def login_ui():
    st.title("Team Utilization Tool")
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = authenticate(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.success(f"Logged in as {username} ({role})")
            else:
                st.error("Invalid credentials")

    elif choice == "Register":
        st.subheader("Register")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            if save_user(new_user, new_pass):
                st.success("User registered successfully")
            else:
                st.error("Username already exists")

def user_dashboard():
    st.title("Submit Utilization")
    project = st.text_input("Project Name")
    date = st.date_input("Date", datetime.today())
    percentage = st.slider("Utilization (%)", 0, 100, 0)
    if st.button("Submit"):
        save_utilization(st.session_state.username, project, date.strftime("%Y-%m-%d"), percentage)
        st.success("Utilization submitted")

    if os.path.exists(UTIL_FILE):
        df = pd.read_csv(UTIL_FILE)
        df = df[df["username"] == st.session_state.username]
        summary = weekly_summary(df)
        st.subheader("Weekly Utilization Summary")
        st.dataframe(summary)

        fig = px.line(summary, x="week", y="percentage", color="project", title="Weekly Utilization by Project")
        st.plotly_chart(fig)

        pie_data = summary.groupby("project")["percentage"].sum().reset_index()
        fig2 = px.pie(pie_data, names="project", values="percentage", title="Project Distribution")
        st.plotly_chart(fig2)

def admin_dashboard():
    st.title("Admin Dashboard")
    if os.path.exists(UTIL_FILE):
        df = pd.read_csv(UTIL_FILE)
        summary = weekly_summary(df)
        st.subheader("Team Weekly Utilization Summary")
        st.dataframe(summary)

        fig = px.bar(summary, x="week", y="percentage", color="username", barmode="group", title="Team Utilization per Week")
        st.plotly_chart(fig)

        pie_data = summary.groupby("project")["percentage"].sum().reset_index()
        fig2 = px.pie(pie_data, names="project", values="percentage", title="Team Project Distribution")
        st.plotly_chart(fig2)

# Main App
if not st.session_state.logged_in:
    login_ui()
else:
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        user_dashboard()
''') + 
