import streamlit as st
import pandas as pd
import os
from datetime import datetime
import hashlib
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

# Load users
users_df = pd.read_csv(USER_FILE)

# Load utilization
util_df = pd.read_csv(UTIL_FILE)

# Hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticate user
def authenticate(username, password):
    hashed = hash_password(password)
    user = users_df[(users_df.username == username) & (users_df.password == hashed)]
    if not user.empty:
        return user.iloc[0].role
    return None

# Register user
def register_user(username, password):
    if username in users_df.username.values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), "user"]], columns=["username", "password", "role"])
    new_user.to_csv(USER_FILE, mode='a', header=False, index=False)
    return True

# Save utilization entry
def save_utilization(username, project, date, percentage):
    new_entry = pd.DataFrame([[username, project, date, percentage]], columns=["username", "project", "date", "percentage"])
    new_entry.to_csv(UTIL_FILE, mode='a', header=False, index=False)

# Weekly summary
def weekly_summary(df):
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.strftime("Week of %d/%m")
    summary = df.groupby(["username", "project", "week"]).agg({"percentage": "sum"}).reset_index()
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
        if register_user(new_user, new_pass):
            st.success("User registered successfully")
        else:
            st.error("Username already exists")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        role = authenticate(username, password)
        if role:
            st.success(f"Logged in as {username} ({role})")

            if role == "user":
                st.subheader("Submit Daily Utilization (% per project)")
                project = st.text_input("Project Name")
                date = st.date_input("Date", datetime.today())
                percentage = st.slider("Utilization (%)", 0, 100)
                if st.button("Submit"):
                    save_utilization(username, project, date.strftime("%Y-%m-%d"), percentage)
                    st.success("Utilization submitted")

                user_data = util_df[util_df.username == username]
                if not user_data.empty:
                    summary = weekly_summary(user_data)
                    st.subheader("Your Weekly Utilization Summary")
                    st.dataframe(summary)

                    fig = px.line(summary, x="week", y="percentage", color="project", title="Weekly Utilization by Project")
                    st.plotly_chart(fig)

                    pie = summary.groupby("project").agg({"percentage": "sum"}).reset_index()
                    fig2 = px.pie(pie, names="project", values="percentage", title="Project Distribution")
                    st.plotly_chart(fig2)

            elif role == "admin":
                st.subheader("Admin Dashboard")
                summary = weekly_summary(util_df)
                st.dataframe(summary)

                fig = px.bar(summary, x="week", y="percentage", color="username", barmode="group", title="Team Weekly Utilization")
                st.plotly_chart(fig)

                pie = summary.groupby("project").agg({"percentage": "sum"}).reset_index()
                fig2 = px.pie(pie, names="project", values="percentage", title="Team Project Distribution")
                st.plotly_chart(fig2)

        else:
            st.error("Invalid credentials")
