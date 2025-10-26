import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# --- Authentication ---
USER_CREDENTIALS = {
    "ariel": {"password": "password123", "role": "admin"},
    "alex": {"password": "teamwork", "role": "user"},
    "jamie": {"password": "securepass", "role": "user"}
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.authenticated:
    st.title("🔐 Team Utilization Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = USER_CREDENTIALS[username]["role"]
        else:
            st.error("Invalid credentials")
    st.stop()

# --- Database Setup ---
conn = sqlite3.connect("utilization.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS utilization (user TEXT, project TEXT, description TEXT, week TEXT, hours REAL)")
conn.commit()
