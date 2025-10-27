import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime, timedelta
import plotly.express as px

# File paths
USER_FILE = "users.csv"
UTIL_FILE = "utilization.csv"

# Initialize user file
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["username", "password", "role"]).to_csv(USER_FILE, index=False)

# Initialize utilization file
if not os.path.exists(UTIL_FILE):
    pd.DataFrame(columns=["username", "project", "date", "percentage"]).to_csv(UTIL_FILE, index=False)

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticate user
def authenticate(username, password):
    users = pd.read_csv(USER_FILE)
    hashed = hash_password(password)
    user = users[(users.username == username) & (users.password == hashed)]
    if not user.empty:
        return user.iloc[0].role
    return None

# Register user
def register_user(username, password):
    users = pd.read_csv(USER_FILE)
    if username in users.username.values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), "user"]], columns=["username", "password", "role"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

# Save utilization
def save_utilization(username, project, date, percentage):
    df = pd.read_csv(UTIL_FILE)
    new_entry = pd.DataFrame([[username, project, date, percentage]], columns=["username", "project", "date", "percentage"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(UTIL_FILE, index=False)

# Weekly summary
def weekly_summary(df):
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%d/%m"))
    summary = df.groupby(["username", "project", "week"]).agg({"percentage": "sum"}).reset_index()
    return summary

# Main app
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

st.title("Team Utilization Tool")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if not st.session_state.logged_in:
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
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("User registered. Please login.")
            else:
                st.error("Username already exists.")
else:
    st.sidebar.write(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    st.subheader("Submit Utilization")
    project = st.text_input("Project Name")
    date = st.date_input("Date", datetime.today())
    percentage = st.slider("Utilization (%)", 0, 100, 0)
    if st.button("Submit"):
        save_utilization(st.session_state.username, project, date.strftime("%Y-%m-%d"), percentage)
        st.success("Utilization submitted.")

    df = pd.read_csv(UTIL_FILE)
    user_data = df[df.username == st.session_state.username] if st.session_state.role == "user" else df
    summary = weekly_summary(user_data)

    st.subheader("Weekly Utilization Summary")
    st.dataframe(summary)

    if not summary.empty:
        fig1 = px.bar(summary, x="week", y="percentage", color="project", barmode="stack",
                     title="Weekly Utilization by Project")
        st.plotly_chart(fig1)

        fig2 = px.pie(summary, names="project", values="percentage", title="Project Distribution")
        st.plotly_chart(fig2)
