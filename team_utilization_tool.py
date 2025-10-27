
import streamlit as st
import pandas as pd
import hashlib
import plotly.express as px
import os

USER_FILE = "users.csv"
UTIL_FILE = "utilization.csv"

if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["username", "password", "role"]).to_csv(USER_FILE, index=False)

if not os.path.exists(UTIL_FILE):
    pd.DataFrame(columns=["username", "date", "project", "hours", "description"]).to_csv(UTIL_FILE, index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    users = pd.read_csv(USER_FILE)
    hashed = hash_password(password)
    user = users[(users.username == username) & (users.password == hashed)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

def register_user(username, password):
    users = pd.read_csv(USER_FILE)
    if username in users.username.values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), "user"]], columns=["username", "password", "role"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

def save_utilization(username, date, project, hours, description):
    df = pd.read_csv(UTIL_FILE)
    new_entry = pd.DataFrame([[username, date, project, hours, description]], columns=df.columns)
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(UTIL_FILE, index=False)

def load_utilization():
    return pd.read_csv(UTIL_FILE)

st.set_page_config(page_title="Team Utilization Tool", layout="wide")
st.title("🚀 Team Utilization Tool")

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
            st.session_state["user"] = username
            st.session_state["role"] = role
        else:
            st.error("Invalid credentials")

if "user" in st.session_state:
    st.sidebar.subheader("Utilization Entry")
    date = st.sidebar.date_input("Date")
    project = st.sidebar.text_input("Project Name")
    hours = st.sidebar.slider("Hours Worked", 0.0, 7.5, 0.5)
    description = st.sidebar.text_area("Project Description")
    if st.sidebar.button("Submit Utilization"):
        save_utilization(st.session_state["user"], date, project, hours, description)
        st.sidebar.success("Utilization submitted")

    df = load_utilization()

    if st.session_state["role"] == "admin":
        st.header("📊 Team Utilization Dashboard")
        st.dataframe(df)

        fig1 = px.bar(df, x="date", y="hours", color="username", title="Daily Hours per User")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.pie(df, names="project", values="hours", title="Project Utilization")
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.header("📈 My Utilization")
        user_df = df[df.username == st.session_state["user"]]
        st.dataframe(user_df)

        fig3 = px.line(user_df, x="date", y="hours", title="My Daily Utilization")
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.pie(user_df, names="project", values="hours", title="My Project Distribution")
        st.plotly_chart(fig4, use_container_width=True)
