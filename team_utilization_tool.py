import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime, timedelta
import plotly.express as px

# File paths
USER_FILE = "users.csv"
UTIL_FILE = "utilization.csv"

# Initialize files if they don't exist
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["username", "password", "role"]).to_csv(USER_FILE, index=False)

if not os.path.exists(UTIL_FILE):
    pd.DataFrame(columns=["username", "date", "project", "percentage"]).to_csv(UTIL_FILE, index=False)

# Hashing passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load users
def load_users():
    return pd.read_csv(USER_FILE)

# Save new user
def save_user(username, password, role="user"):
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), role]], columns=["username", "password", "role"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

# Authenticate user
def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)
    user = users[(users["username"] == username) & (users["password"] == hashed)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

# Save utilization entry
def save_utilization(username, date, project, percentage):
    df = pd.read_csv(UTIL_FILE)
    new_entry = pd.DataFrame([[username, date, project, percentage]], columns=["username", "date", "project", "percentage"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(UTIL_FILE, index=False)

# Load utilization data
def load_utilization():
    return pd.read_csv(UTIL_FILE)

# Weekly utilization summary
def weekly_summary(df):
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%d/%m"))
    summary = df.groupby(["username", "project", "week"]).agg({"percentage": "sum"}).reset_index()
    summary["percentage"] = summary["percentage"].clip(upper=100)
    return summary

# App UI
st.title("Team Utilization Tool")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type='password')
    if st.button("Register"):
        if save_user(new_user, new_pass):
            st.success("User registered successfully")
        else:
            st.error("Username already exists")

elif choice == "Login":
    st.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        role = authenticate(username, password)
        if role:
            st.success(f"Logged in as {username} ({role})")
            df = load_utilization()

            if role == "user":
                st.subheader("Submit Daily Utilization (% per project)")
                date = st.date_input("Date", datetime.today())
                project = st.text_input("Project Name")
                percentage = st.slider("Utilization (%)", 0, 100)
                if st.button("Submit"):
                    save_utilization(username, date.strftime("%Y-%m-%d"), project, percentage)
                    st.success("Utilization submitted")

                st.subheader("Your Weekly Utilization Summary")
                user_data = df[df["username"] == username]
                summary = weekly_summary(user_data)
                st.dataframe(summary)

                if not summary.empty:
                    fig = px.line(summary, x="week", y="percentage", color="project", title="Weekly Utilization by Project")
                    st.plotly_chart(fig)
                    pie_data = summary.groupby("project")["percentage"].sum().reset_index()
                    pie_fig = px.pie(pie_data, names="project", values="percentage", title="Project Distribution")
                    st.plotly_chart(pie_fig)

            elif role == "admin":
                st.subheader("Team Weekly Utilization Summary")
                summary = weekly_summary(df)
                st.dataframe(summary)

                if not summary.empty:
                    fig = px.bar(summary, x="week", y="percentage", color="username", barmode="group", title="Team Weekly Utilization")
                    st.plotly_chart(fig)
                    pie_data = summary.groupby("project")["percentage"].sum().reset_index()
                    pie_fig = px.pie(pie_data, names="project", values="percentage", title="Team Project Distribution")
                    st.plotly_chart(pie_fig)
        else:
            st.error("Invalid credentials")
