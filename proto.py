# --------------------------
# 1. IMPORTS (MUST BE AT TOP)
# --------------------------
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import datetime
from datetime import date, timedelta
import json
import os
from io import BytesIO
from PIL import Image
import hashlib
import sqlite3
from sqlite3 import Error

# --------------------------
# 2. PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# --------------------------
st.set_page_config(
    page_title="Lab Assistant Pro",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# 3. DATABASE FUNCTIONS (NO STREAMLIT HERE)
# --------------------------
def create_connection(db_file):
    """ Create a database connection """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        st.error(f"Database connection error: {e}")
    return conn

def initialize_db():
    """ Initialize database tables """
    conn = create_connection("lab_assistant.db")
    if conn is not None:
        try:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    registration_date TEXT
                )
            """)
            
            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    frequency TEXT,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Reagents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reagents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    location TEXT,
                    supplier TEXT,
                    catalog_number TEXT,
                    date_added TEXT,
                    expiry_date TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Experiments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    aim TEXT,
                    date TEXT,
                    reagents TEXT,
                    procedure TEXT,
                    observations TEXT,
                    notes TEXT,
                    results TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Buffers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    ph REAL,
                    components TEXT,
                    preparation TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
        except Error as e:
            st.error(f"Error initializing database: {e}")
        finally:
            conn.close()

# --------------------------
# 4. AUTHENTICATION FUNCTIONS
# --------------------------
def create_user(username, password, email="", full_name=""):
    """ Create new user """
    conn = create_connection("lab_assistant.db")
    if conn is not None:
        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO users (username, password, email, full_name, registration_date) VALUES (?, ?, ?, ?, ?)",
                (username, hashed_password, email, full_name, registration_date)
            )
            conn.commit()
            return True
        except Error as e:
            st.error(f"Error creating user: {e}")
            return False
        finally:
            conn.close()
    return False

def verify_user(username, password):
    """ Verify user credentials """
    conn = create_connection("lab_assistant.db")
    if conn is not None:
        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor = conn.execute(
                "SELECT id, username FROM users WHERE username = ? AND password = ?",
                (username, hashed_password)
            )
            user = cursor.fetchone()
            return user if user else None
        except Error as e:
            st.error(f"Error verifying user: {e}")
            return None
        finally:
            conn.close()
    return None

# --------------------------
# 5. UTILITY FUNCTIONS
# --------------------------
def get_table_download_link(df, filename):
    """Generates a link allowing the data in a given panda dataframe to be downloaded"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'

# --------------------------
# 6. MAIN APP PAGES
# --------------------------
def login_page():
    """ Login/registration page """
    st.title("🔬 Lab Assistant Pro - Login")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        menu = option_menu(None, ["Login", "Register"], 
                         icons=['box-arrow-in-right', 'person-plus'], 
                         menu_icon="cast", default_index=0, orientation="horizontal")
        
        if menu == "Login":
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Login")
                
                if submit_button:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = user[0]
                        st.session_state.current_page = "dashboard"
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        elif menu == "Register":
            with st.form("register_form"):
                st.subheader("Create Account")
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                email = st.text_input("Email (optional)")
                full_name = st.text_input("Full Name (optional)")
                submit_button = st.form_submit_button("Register")
                
                if submit_button:
                    if new_password != confirm_password:
                        st.error("Passwords don't match!")
                    elif len(new_password) < 6:
                        st.error("Password must be ≥6 characters")
                    else:
                        if create_user(new_username, new_password, email, full_name):
                            st.success("Account created! Please login.")
                        else:
                            st.error("Username already exists")
    else:
        st.success(f"Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.current_page = "login"
            st.rerun()
        dashboard_page()

def dashboard_page():
    """ User dashboard showing important tasks and quick access """
    st.title(f"👋 Welcome, {st.session_state.username}!")
    st.subheader("Your Lab Dashboard")
    
    # Get user's upcoming tasks
    conn = create_connection("lab_assistant.db")
    if conn is not None:
        try:
            # Upcoming tasks
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor = conn.execute(
                "SELECT title, description, due_date FROM tasks WHERE user_id = ? AND completed = 0 AND (due_date >= ? OR frequency != 'once') ORDER BY due_date LIMIT 5",
                (st.session_state.user_id, today)
            )
            upcoming_tasks = cursor.fetchall()
            
            # Recent experiments
            cursor = conn.execute(
                "SELECT title, date FROM experiments WHERE user_id = ? ORDER BY date DESC LIMIT 3",
                (st.session_state.user_id,)
            )
            recent_experiments = cursor.fetchall()
            
            # Low reagents
            cursor = conn.execute(
                "SELECT name, quantity, unit FROM reagents WHERE user_id = ? AND quantity < 10 ORDER BY quantity ASC LIMIT 3",
                (st.session_state.user_id,)
            )
            low_reagents = cursor.fetchall()
            
        except Error as e:
            st.error(f"Error fetching dashboard data: {e}")
        finally:
            conn.close()

    # Dashboard layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Upcoming Tasks")
        if upcoming_tasks:
            for task in upcoming_tasks:
                due_date = datetime.datetime.strptime(task[2], "%Y-%m-%d").strftime("%b %d") if task[2] else "No date"
                st.write(f"**{task[0]}** - *Due: {due_date}*")
                if task[1]:
                    st.caption(task[1])
        else:
            st.info("No upcoming tasks. Add some in the Lab Planner!")
        
        st.subheader("🧪 Recent Experiments")
        if recent_experiments:
            for exp in recent_experiments:
                exp_date = datetime.datetime.strptime(exp[1], "%Y-%m-%d").strftime("%b %d") if exp[1] else "No date"
                st.write(f"**{exp[0]}** - *{exp_date}*")
        else:
            st.info("No recent experiments recorded.")
    
    with col2:
        st.subheader("⚠️ Low Reagents")
        if low_reagents:
            for reagent in low_reagents:
                st.write(f"**{reagent[0]}** - {reagent[1]} {reagent[2]}")
        else:
            st.info("All reagents are sufficiently stocked.")
        
        st.subheader("Quick Actions")
        if st.button("🧪 New Experiment"):
            st.session_state.current_page = "protocol_generator"
            st.rerun()
        if st.button("🧪 New Buffer"):
            st.session_state.current_page = "buffer_helper"
            st.rerun()
        if st.button("📅 Add Task"):
            st.session_state.current_page = "lab_planner"
            st.rerun()
        if st.button("📊 Visualize Data"):
            st.session_state.current_page = "data_visualizer"
            st.rerun()

def dilution_calculator():
    """ Calculator for making laboratory dilutions """
    st.title("🧪 Dilution Calculator")
    
    st.markdown("""
    This calculator helps you prepare dilutions from stock solutions. Enter your parameters below.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        c1 = st.number_input("Stock Concentration (C1)", min_value=0.0, value=1.0, step=0.1)
        unit1 = st.selectbox("Unit", ["M", "mM", "µM", "nM", "g/L", "mg/mL", "µg/mL", "%"])
        v2 = st.number_input("Final Volume (V2)", min_value=0.0, value=100.0, step=1.0)
        unit2 = st.selectbox("Volume Unit", ["L", "mL", "µL"])
    
    with col2:
        c2 = st.number_input("Final Concentration (C2)", min_value=0.0, value=0.1, step=0.01)
        unit3 = st.selectbox("Final Unit", ["M", "mM", "µM", "nM", "g/L", "mg/mL", "µg/mL", "%"])
    
    if st.button("Calculate"):
        try:
            v1 = (c2 * v2) / c1
            st.success(f"**You need to dilute {v1:.2f} {unit2} of stock solution to {v2} {unit2} with solvent.**")
            
            # Show preparation instructions
            st.subheader("Preparation Instructions")
            st.write(f"1. Measure **{v1:.2f} {unit2}** of the stock solution ({c1} {unit1}).")
            st.write(f"2. Add solvent (e.g., water) to bring the total volume to **{v2} {unit2}**.")
            st.write(f"3. Mix thoroughly to ensure homogeneity.")
            
            # Save to history
            if 'dilution_history' not in st.session_state:
                st.session_state.dilution_history = []
            
            st.session_state.dilution_history.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "stock_conc": f"{c1} {unit1}",
                "final_conc": f"{c2} {unit3}",
                "final_vol": f"{v2} {unit2}",
                "stock_vol": f"{v1:.2f} {unit2}"
            })
            
        except ZeroDivisionError:
            st.error("Stock concentration cannot be zero!")
    
    # Show history
    if 'dilution_history' in st.session_state and st.session_state.dilution_history:
        st.subheader("Calculation History")
        history_df = pd.DataFrame(st.session_state.dilution_history)
        st.dataframe(history_df)
        
        if st.button("Clear History"):
            st.session_state.dilution_history = []
            st.rerun()

def solution_helper():
    """ Helper for preparing solutions of different concentrations """
    st.title("🧪 Solution Preparation Helper")
    
    method = st.radio("Preparation Method", 
                     ["Mass to Volume", "Volume to Volume", "Molar Solution"], 
                     horizontal=True)
    
    if method == "Mass to Volume":
        col1, col2 = st.columns(2)
        
        with col1:
            compound = st.text_input("Compound Name", "NaCl")
            mw = st.number_input("Molecular Weight (g/mol)", min_value=0.0, value=58.44)
            target_conc = st.number_input("Target Concentration", min_value=0.0, value=1.0)
            conc_unit = st.selectbox("Concentration Unit", ["M", "mM", "µM", "g/L", "mg/mL", "% (w/v)"])
        
        with col2:
            target_vol = st.number_input("Target Volume", min_value=0.0, value=100.0)
            vol_unit = st.selectbox("Volume Unit", ["L", "mL"])
            solvent = st.text_input("Solvent", "Water")
        
        if st.button("Calculate"):
            if conc_unit == "M":
                mass = target_conc * mw * (target_vol / 1000 if vol_unit == "mL" else target_vol)
            elif conc_unit == "mM":
                mass = (target_conc / 1000) * mw * (target_vol / 1000 if vol_unit == "mL" else target_vol)
            elif conc_unit == "µM":
                mass = (target_conc / 1e6) * mw * (target_vol / 1000 if vol_unit == "mL" else target_vol)
            elif conc_unit == "g/L":
                mass = target_conc * (target_vol / 1000 if vol_unit == "mL" else target_vol)
            elif conc_unit == "mg/mL":
                mass = target_conc * target_vol if vol_unit == "mL" else target_conc * target_vol * 1000
            elif conc_unit == "% (w/v)":
                mass = (target_conc / 100) * target_vol if vol_unit == "mL" else (target_conc / 100) * target_vol * 1000
            
            st.success(f"**You need {mass:.4f} g of {compound} to prepare the solution.**")
            
            st.subheader("Preparation Instructions")
            st.write(f"1. Weigh **{mass:.4f} g** of {compound} using an analytical balance.")
            st.write(f"2. Transfer the {compound} to a {target_vol} {vol_unit} volumetric flask.")
            st.write(f"3. Add {solvent} to about half the final volume and dissolve completely.")
            st.write(f"4. Fill to the mark with {solvent} and mix thoroughly.")
    
    elif method == "Volume to Volume":
        st.subheader("Volume to Volume Dilution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            stock_conc = st.number_input("Stock Concentration", min_value=0.0, value=1.0)
            stock_unit = st.selectbox("Stock Unit", ["M", "mM", "µM", "nM", "g/L", "mg/mL", "µg/mL", "%"])
            target_vol = st.number_input("Target Volume (mL)", min_value=0.1, value=100.0)
        
        with col2:
            target_conc = st.number_input("Target Concentration", min_value=0.0, value=0.1)
            target_unit = st.selectbox("Target Unit", ["M", "mM", "µM", "nM", "g/L", "mg/mL", "µg/mL", "%"])
            stock_vol = st.number_input("Stock Volume Available (mL)", min_value=0.1, value=50.0)
        
        if st.button("Calculate"):
            try:
                req_vol = (target_conc * target_vol) / stock_conc
                
                if req_vol > stock_vol:
                    st.error(f"Not enough stock solution! You need {req_vol:.2f} mL but only have {stock_vol} mL")
                else:
                    st.success(f"**Dilute {req_vol:.2f} mL of stock solution to {target_vol} mL**")
                    
                    st.subheader("Preparation Instructions")
                    st.write(f"1. Measure **{req_vol:.2f} mL** of the stock solution ({stock_conc} {stock_unit})")
                    st.write(f"2. Add solvent to bring the total volume to **{target_vol} mL**")
                    st.write(f"3. Mix thoroughly")
                    
            except ZeroDivisionError:
                st.error("Stock concentration cannot be zero!")
    
    elif method == "Molar Solution":
        st.subheader("Molar Solution Preparation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            compound = st.text_input("Compound Name", "NaCl")
            mw = st.number_input("Molecular Weight (g/mol)", min_value=0.0, value=58.44)
            molarity = st.number_input("Desired Molarity (M)", min_value=0.0, value=1.0)
        
        with col2:
            volume = st.number_input("Volume (L)", min_value=0.001, value=1.0)
            solvent = st.text_input("Solvent", "Water")
            temp = st.number_input("Temperature (°C)", min_value=0.0, value=25.0)
        
        if st.button("Prepare Solution"):
            try:
                mass = molarity * mw * volume
                
                st.success(f"**Dissolve {mass:.4f} g of {compound} in {volume} L of {solvent}**")
                
                st.subheader("Step-by-Step Instructions")
                st.write(f"1. Calculate molecular weight: {mw} g/mol")
                st.write(f"2. Weigh out **{mass:.4f} g** of {compound}")
                st.write(f"3. Add to a volumetric flask")
                st.write(f"4. Add {solvent} to about 80% of final volume and dissolve")
                st.write(f"5. Bring to final volume of {volume} L at {temp}°C")
                st.write(f"6. Mix thoroughly")
                
            except Exception as e:
                st.error(f"Error in calculation: {e}")

def buffer_helper():
    """ Helper for preparing buffers with different pH """
    st.title("🧪 Buffer Preparation Helper")
    
    buffer_type = st.selectbox("Select Buffer Type", 
                              ["Tris", "Phosphate", "Acetate", "HEPES", "PBS", "Custom"])
    
    if buffer_type == "Tris":
        st.subheader("Tris Buffer Preparation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_ph = st.slider("Target pH", 7.0, 9.0, 8.0, 0.1)
            concentration = st.number_input("Concentration (M)", min_value=0.01, value=0.1, step=0.01)
            volume = st.number_input("Volume (L)", min_value=0.01, value=1.0, step=0.1)
        
        with col2:
            temp = st.number_input("Temperature (°C)", min_value=4.0, value=25.0, step=0.1)
            adjust_with = st.radio("Adjust pH with", ["HCl", "NaOH"])
        
        if st.button("Calculate Recipe"):
            tris_mass = 121.14 * concentration * volume
            st.success(f"**Tris Buffer Recipe (pH {target_ph})**")
            
            st.write(f"1. Dissolve **{tris_mass:.2f} g** of Tris base in about {volume*0.8:.1f} L of water.")
            st.write(f"2. Adjust pH to {target_ph} with concentrated {adjust_with} solution.")
            st.write(f"3. Add water to bring the total volume to {volume} L.")
            
            # Save to database
            conn = create_connection("lab_assistant.db")
            if conn is not None:
                try:
                    components = json.dumps({
                        "Tris base": f"{tris_mass:.2f} g",
                        adjust_with: "for pH adjustment"
                    })
                    conn.execute(
                        "INSERT INTO buffers (user_id, name, ph, components, preparation) VALUES (?, ?, ?, ?, ?)",
                        (st.session_state.user_id, f"Tris {target_ph}", target_ph, components, 
                         f"Dissolve {tris_mass:.2f}g Tris, adjust pH with {adjust_with}, bring to {volume}L")
                    )
                    conn.commit()
                    st.success("Buffer recipe saved to your database!")
                except Error as e:
                    st.error(f"Error saving buffer: {e}")
                finally:
                    conn.close()
    
    elif buffer_type == "Phosphate":
        st.subheader("Phosphate Buffer Preparation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_ph = st.slider("Target pH", 5.8, 8.0, 7.0, 0.1)
            concentration = st.number_input("Concentration (M)", min_value=0.01, value=0.1, step=0.01)
            volume = st.number_input("Volume (L)", min_value=0.01, value=1.0, step=0.1)
        
        with col2:
            temp = st.number_input("Temperature (°C)", min_value=4.0, value=25.0, step=0.1)
            buffer_type = st.radio("Buffer Components", ["NaH2PO4/Na2HPO4", "KH2PO4/K2HPO4"])
        
        if st.button("Calculate Recipe"):
            if buffer_type == "NaH2PO4/Na2HPO4":
                mw1 = 119.98  # NaH2PO4
                mw2 = 141.96  # Na2HPO4
            else:
                mw1 = 136.09  # KH2PO4
                mw2 = 174.18  # K2HPO4
            
            # Simplified calculation (real calculation would use Henderson-Hasselbalch)
            ratio = 10**(target_ph - 6.86)  # pKa for phosphate buffer
            
            mass1 = (concentration * volume * mw1) / (1 + ratio)
            mass2 = (concentration * volume * mw2 * ratio) / (1 + ratio)
            
            st.success(f"**Phosphate Buffer Recipe (pH {target_ph})**")
            st.write(f"1. Dissolve **{mass1:.2f} g** of {buffer_type.split('/')[0]} and **{mass2:.2f} g** of {buffer_type.split('/')[1]} in about {volume*0.8:.1f} L water.")
            st.write(f"2. Adjust pH to {target_ph} if needed.")
            st.write(f"3. Bring to final volume of {volume} L.")
    
    elif buffer_type == "Custom":
        st.subheader("Custom Buffer Preparation")
        
        num_components = st.number_input("Number of Components", min_value=1, max_value=10, value=2)
        
        components = []
        for i in range(num_components):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                name = st.text_input(f"Component {i+1} Name", key=f"comp_name_{i}")
            with col2:
                amount = st.number_input("Amount", min_value=0.0, key=f"comp_amt_{i}")
            with col3:
                unit = st.selectbox("Unit", ["g", "mg", "mL", "µL", "M", "mM"], key=f"comp_unit_{i}")
            components.append(f"{amount} {unit} {name}")
        
        target_ph = st.number_input("Target pH", min_value=0.0, max_value=14.0, value=7.4, step=0.1)
        final_volume = st.number_input("Final Volume (mL)", min_value=1.0, value=100.0, step=1.0)
        preparation = st.text_area("Preparation Instructions", "1. Dissolve components in about 80% final volume...")
        
        if st.button("Save Custom Buffer"):
            conn = create_connection("lab_assistant.db")
            if conn is not None:
                try:
                    conn.execute(
                        "INSERT INTO buffers (user_id, name, ph, components, preparation) VALUES (?, ?, ?, ?, ?)",
                        (st.session_state.user_id, f"Custom Buffer pH {target_ph}", target_ph, 
                         json.dumps(components), preparation)
                    )
                    conn.commit()
                    st.success("Custom buffer saved to your database!")
                except Error as e:
                    st.error(f"Error saving buffer: {e}")
                finally:
                    conn.close()

def lab_planner():
    """ Lab planner for managing tasks and events """
    st.title("📅 Lab Planner")
    
    tab1, tab2, tab3 = st.tabs(["Daily Tasks", "Weekly/Monthly Tasks", "Calendar View"])
    
    # Helper function to get tasks
    def get_tasks(frequency=None, completed=False):
        conn = create_connection("lab_assistant.db")
        if conn is not None:
            try:
                query = "SELECT id, title, description, due_date, frequency, completed FROM tasks WHERE user_id = ?"
                params = [st.session_state.user_id]
                
                if frequency:
                    query += " AND frequency = ?"
                    params.append(frequency)
                
                if not completed:
                    query += " AND completed = 0"
                
                query += " ORDER BY due_date"
                cursor = conn.execute(query, tuple(params))
                return cursor.fetchall()
            except Error as e:
                st.error(f"Error fetching tasks: {e}")
            finally:
                conn.close()
        return []
    
    with tab1:
        st.subheader("Today's Tasks")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Add new task
        with st.expander("➕ Add New Task"):
            with st.form("add_task_form"):
                title = st.text_input("Task Title*")
                description = st.text_area("Description")
                due_date = st.date_input("Due Date", datetime.datetime.now())
                frequency = st.selectbox("Frequency", ["once", "daily", "weekly", "monthly"])
                submit_button = st.form_submit_button("Add Task")
                
                if submit_button and title:
                    conn = create_connection("lab_assistant.db")
                    if conn is not None:
                        try:
                            conn.execute(
                                "INSERT INTO tasks (user_id, title, description, due_date, frequency) VALUES (?, ?, ?, ?, ?)",
                                (st.session_state.user_id, title, description, due_date.strftime("%Y-%m-%d"), frequency)
                            )
                            conn.commit()
                            st.success("Task added successfully!")
                            st.rerun()
                        except Error as e:
                            st.error(f"Error adding task: {e}")
                        finally:
                            conn.close()

        # Display tasks
        tasks = get_tasks()
        
        if tasks:
            for task in tasks:
                task_id, title, desc, due_date, freq, completed = task
                due_date_str = datetime.datetime.strptime(due_date, "%Y-%m-%d").strftime("%b %d, %Y")
                
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"**{title}**")
                        if desc:
                            st.caption(desc)
                        st.caption(f"📅 Due: {due_date_str} | 🔁 {freq.capitalize()}")
                    with col2:
                        if st.button("✓", key=f"complete_{task_id}"):
                            conn = create_connection("lab_assistant.db")
                            if conn is not None:
                                try:
                                    conn.execute(
                                        "UPDATE tasks SET completed = 1 WHERE id = ?",
                                        (task_id,)
                                    )
                                    conn.commit()
                                    st.rerun()
                                except Error as e:
                                    st.error(f"Error updating task: {e}")
                                finally:
                                    conn.close()
        else:
            st.info("No tasks found. Add some tasks to get started!")
    
    with tab2:
        st.subheader("Recurring Tasks")
        
        frequency = st.radio("Task Frequency", ["weekly", "monthly"], horizontal=True)
        
        # Add new recurring task
        with st.expander("➕ Add New Recurring Task"):
            with st.form("add_recurring_task_form"):
                title = st.text_input("Task Title*")
                description = st.text_area("Description")
                due_date = st.date_input("Next Due Date", datetime.datetime.now())
                submit_button = st.form_submit_button("Add Task")
                
                if submit_button and title:
                    conn = create_connection("lab_assistant.db")
                    if conn is not None:
                        try:
                            conn.execute(
                                "INSERT INTO tasks (user_id, title, description, due_date, frequency) VALUES (?, ?, ?, ?, ?)",
                                (st.session_state.user_id, title, description, due_date.strftime("%Y-%m-%d"), frequency)
                            )
                            conn.commit()
                            st.success("Recurring task added successfully!")
                            st.rerun()
                        except Error as e:
                            st.error(f"Error adding task: {e}")
                        finally:
                            conn.close()
        
        # Display recurring tasks
        recurring_tasks = get_tasks(frequency)
        
        if recurring_tasks:
            for task in recurring_tasks:
                task_id, title, desc, due_date, freq, completed = task
                due_date_str = datetime.datetime.strptime(due_date, "%Y-%m-%d").strftime("%b %d, %Y")
                
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"**{title}**")
                        if desc:
                            st.caption(desc)
                        st.caption(f"📅 Next Due: {due_date_str} | 🔁 {freq.capitalize()}")
                    with col2:
                        if st.button("✓", key=f"complete_{task_id}"):
                            # For recurring tasks, update the due date instead of marking complete
                            if freq == "weekly":
                                new_date = (datetime.datetime.strptime(due_date, "%Y-%m-%d") + timedelta(weeks=1)).strftime("%Y-%m-%d")
                            else:  # monthly
                                new_date = (datetime.datetime.strptime(due_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
                            
                            conn = create_connection("lab_assistant.db")
                            if conn is not None:
                                try:
                                    conn.execute(
                                        "UPDATE tasks SET due_date = ? WHERE id = ?",
                                        (new_date, task_id)
                                    )
                                    conn.commit()
                                    st.rerun()
                                except Error as e:
                                    st.error(f"Error updating task: {e}")
                                finally:
                                    conn.close()
        else:
            st.info(f"No {frequency} tasks found")
    
    with tab3:
        st.subheader("Calendar View")
        
        # Create a calendar view using st.date_input
        selected_date = st.date_input("Select Date", datetime.datetime.now())
        
        # Get tasks for selected date
        conn = create_connection("lab_assistant.db")
        if conn is not None:
            try:
                date_str = selected_date.strftime("%Y-%m-%d")
                cursor = conn.execute(
                    "SELECT title, description FROM tasks WHERE user_id = ? AND due_date = ? AND completed = 0",
                    (st.session_state.user_id, date_str)
                )
                daily_tasks = cursor.fetchall()
                
                if daily_tasks:
                    st.write(f"### Tasks for {selected_date.strftime('%A, %B %d, %Y')}")
                    for task in daily_tasks:
                        with st.expander(task[0]):
                            st.write(task[1] if task[1] else "No description")
                else:
                    st.info(f"No tasks scheduled for {selected_date.strftime('%A, %B %d, %Y')}")
            except Error as e:
                st.error(f"Error fetching tasks: {e}")
            finally:
                conn.close()
        
        # Add quick task button
        with st.expander("➕ Add Task for Selected Date"):
            with st.form("quick_add_task_form"):
                quick_title = st.text_input("Task Title*")
                quick_desc = st.text_area("Description")
                submit_quick = st.form_submit_button("Add Task")
                
                if submit_quick and quick_title:
                    conn = create_connection("lab_assistant.db")
                    if conn is not None:
                        try:
                            conn.execute(
                                "INSERT INTO tasks (user_id, title, description, due_date, frequency) VALUES (?, ?, ?, ?, ?)",
                                (st.session_state.user_id, quick_title, quick_desc, date_str, "once")
                            )
                            conn.commit()
                            st.success("Task added successfully!")
                            st.rerun()
                        except Error as e:
                            st.error(f"Error adding task: {e}")
                        finally:
                            conn.close()

def protocol_generator():
    """ Protocol and experiment log generator """
    st.title("📝 Protocol Generator")
    
    with st.form("protocol_form"):
        st.subheader("Experiment Details")
        project_title = st.text_input("Project/Experiment Title*")
        aim = st.text_area("Aim/Objective*")
        date = st.date_input("Date", datetime.datetime.now())
        
        st.subheader("Reagents and Apparatus")
        num_reagents = st.number_input("Number of Reagents", min_value=1, max_value=50, value=3)
        
        reagents = []
        for i in range(num_reagents):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                name = st.text_input(f"Reagent {i+1} Name", key=f"reagent_name_{i}")
            with col2:
                amount = st.number_input("Amount", min_value=0.0, key=f"reagent_amt_{i}")
            with col3:
                unit = st.selectbox("Unit", ["g", "mg", "µg", "L", "mL", "µL", "M", "mM", "µM"], key=f"reagent_unit_{i}")
            reagents.append(f"{amount} {unit} {name}")
        
        apparatus = st.text_area("Apparatus/Equipment (comma separated)", "Beaker, Stirrer, pH meter, Balance")
        
        st.subheader("Procedure")
        num_steps = st.number_input("Number of Procedure Steps", min_value=1, max_value=50, value=5)
        
        procedure = []
        for i in range(num_steps):
            step = st.text_input(f"Step {i+1}", key=f"step_{i}")
            if step:
                procedure.append(step)
        
        st.subheader("Additional Information")
        observations = st.text_area("Observations (optional)")
        notes = st.text_area("Notes (optional)")
        results = st.text_area("Results (optional)")
        
        submit_button = st.form_submit_button("Generate Protocol")
        
        if submit_button and project_title and aim:
            # Save to database
            conn = create_connection("lab_assistant.db")
            if conn is not None:
                try:
                    conn.execute(
                        """INSERT INTO experiments 
                        (user_id, title, aim, date, reagents, procedure, observations, notes, results) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (st.session_state.user_id, project_title, aim, date.strftime("%Y-%m-%d"), 
                         json.dumps(reagents), json.dumps(procedure), observations, notes, results)
                    )
                    conn.commit()
                    st.success("Protocol saved successfully!")
                except Error as e:
                    st.error(f"Error saving protocol: {e}")
                finally:
                    conn.close()
            
            # Display protocol
            st.subheader(f"Protocol: {project_title}")
            st.write(f"**Date:** {date.strftime('%Y-%m-%d')}")
            
            st.write("### Aim")
            st.write(aim)
            
            st.write("### Reagents")
            for reagent in reagents:
                st.write(f"- {reagent}")
            
            st.write("### Apparatus")
            st.write(", ".join([item.strip() for item in apparatus.split(",")]))
            
            st.write("### Procedure")
            for i, step in enumerate(procedure, 1):
                st.write(f"{i}. {step}")
            
            if observations:
                st.write("### Observations")
                st.write(observations)
            
            if results:
                st.write("### Results")
                st.write(results)
            
            if notes:
                st.write("### Notes")
                st.write(notes)

def reagent_tracker():
    """ Reagent inventory tracker with full CRUD functionality """
    st.title("🧪 Reagent Tracker")
    
    tab1, tab2, tab3 = st.tabs(["View Inventory", "Add New Reagent", "Update Inventory"])
    
    # Helper function to get reagent data with error handling
    def get_reagents():
        try:
            conn = create_connection("lab_assistant.db")
            if conn is not None:
                cursor = conn.execute(
                    "SELECT id, name, quantity, unit, location, supplier, catalog_number, expiry_date, notes FROM reagents WHERE user_id = ? ORDER BY name",
                    (st.session_state.user_id,)
                )
                results = cursor.fetchall()
                conn.close()
                return results
            return []
        except Exception as e:
            st.error(f"Error loading reagents: {str(e)}")
            return []

    with tab1:
        st.subheader("Current Inventory")
        reagents = get_reagents()
        
        if reagents:
            try:
                # Create DataFrame with proper type handling
                df = pd.DataFrame(reagents, columns=[
                    "ID", "Name", "Quantity", "Unit", "Location", 
                    "Supplier", "Catalog #", "Expiry Date", "Notes"
                ])
                
                # Convert quantity to float and handle possible None values
                df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
                
                # Convert expiry date to datetime, handling None/empty values
                df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], errors='coerce')
                
                # Add status column
                df['Status'] = df['Quantity'].apply(
                    lambda x: "⚠️ Low Stock" if float(x) < 10 else "✅ In Stock"
                )
                
                # Display editable table
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "ID": None,
                        "Status": st.column_config.Column(disabled=True),
                        "Expiry Date": st.column_config.DateColumn(
                            "Expiry Date",
                            min_value=date.today(),
                            format="YYYY-MM-DD",
                            step=1
                        ),
                        "Quantity": st.column_config.NumberColumn(
                            "Quantity",
                            min_value=0,
                            step=0.1
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="reagent_editor"
                )
                
                # Handle edits
                if not edited_df.equals(df):
                    try:
                        conn = create_connection("lab_assistant.db")
                        for _, row in edited_df.iterrows():
                            expiry = row['Expiry Date'].strftime('%Y-%m-%d') if pd.notna(row['Expiry Date']) else None
                            conn.execute(
                                """UPDATE reagents SET
                                name=?, quantity=?, unit=?, location=?,
                                supplier=?, catalog_number=?, expiry_date=?, notes=?
                                WHERE id=? AND user_id=?""",
                                (row['Name'], row['Quantity'], row['Unit'], row['Location'],
                                 row['Supplier'], row['Catalog #'], expiry, row['Notes'],
                                 row['ID'], st.session_state.user_id)
                            )
                        conn.commit()
                        st.success("Inventory updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating inventory: {str(e)}")
                    finally:
                        if conn:
                            conn.close()
                
                # Export options
                st.subheader("Export Options")
                export_df = df.copy()
                export_df['Expiry Date'] = export_df['Expiry Date'].dt.strftime('%Y-%m-%d')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Export as CSV",
                        export_df.to_csv(index=False),
                        "reagent_inventory.csv",
                        "text/csv"
                    )
                with col2:
                    if st.button("🖨️ Print View"):
                        st.markdown(
                            f"<script>window.print()</script>",
                            unsafe_allow_html=True
                        )
                
                # Expiry alerts
                st.subheader("⚠️ Expiry Alerts")
                alerts = df[df['Expiry Date'] < (pd.to_datetime('today') + pd.Timedelta(days=30))]
                if not alerts.empty:
                    st.dataframe(alerts[['Name', 'Quantity', 'Unit', 'Expiry Date']])
                else:
                    st.info("No reagents expiring soon")
                    
            except Exception as e:
                st.error(f"Error displaying inventory: {str(e)}")
        else:
            st.info("No reagents found. Add some reagents to get started.")

    with tab2:
        st.subheader("Add New Reagent")
        with st.form("add_reagent_form", clear_on_submit=True):
            name = st.text_input("Name*")
            quantity = st.number_input("Quantity*", min_value=0.0, value=1.0, step=0.1)
            unit = st.selectbox("Unit*", ["g", "mg", "µg", "L", "mL", "µL"])
            location = st.text_input("Location*", "Room 123, Shelf A")
            supplier = st.text_input("Supplier")
            catalog_num = st.text_input("Catalog Number")
            expiry_date = st.date_input("Expiry Date (optional)")
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Reagent") and name:
                try:
                    conn = create_connection("lab_assistant.db")
                    conn.execute(
                        """INSERT INTO reagents 
                        (user_id, name, quantity, unit, location, supplier, 
                        catalog_number, expiry_date, notes, date_added)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (st.session_state.user_id, name, quantity, unit, location,
                         supplier, catalog_num, expiry_date.strftime('%Y-%m-%d') if expiry_date else None,
                         notes, datetime.datetime.now().strftime('%Y-%m-%d'))
                    )
                    conn.commit()
                    st.success("Reagent added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding reagent: {str(e)}")
                finally:
                    if conn:
                        conn.close()

    with tab3:
        st.subheader("Update Inventory")
        reagents = get_reagents()
        
        if reagents:
            reagent_list = [f"{r[1]} (ID: {r[0]})" for r in reagents]
            selected = st.selectbox("Select Reagent", reagent_list)
            
            if selected:
                reagent_id = int(selected.split("(ID: ")[1].replace(")", ""))
                reagent_data = next(r for r in reagents if r[0] == reagent_id)
                
                with st.form("update_form"):
                    name = st.text_input("Name", value=reagent_data[1])
                    quantity = st.number_input("Quantity", value=float(reagent_data[2]))
                    unit = st.selectbox("Unit", 
                                      ["g", "mg", "µg", "L", "mL", "µL"],
                                      index=["g", "mg", "µg", "L", "mL", "µL"].index(reagent_data[3]))
                    location = st.text_input("Location", value=reagent_data[4])
                    supplier = st.text_input("Supplier", value=reagent_data[5])
                    catalog_num = st.text_input("Catalog #", value=reagent_data[6])
                    expiry = st.date_input("Expiry Date", 
                                         value=pd.to_datetime(reagent_data[7]).date() if reagent_data[7] else None)
                    notes = st.text_area("Notes", value=reagent_data[8])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Update"):
                            try:
                                conn = create_connection("lab_assistant.db")
                                conn.execute(
                                    """UPDATE reagents SET
                                    name=?, quantity=?, unit=?, location=?,
                                    supplier=?, catalog_number=?, expiry_date=?, notes=?
                                    WHERE id=?""",
                                    (name, quantity, unit, location,
                                     supplier, catalog_num, expiry.strftime('%Y-%m-%d') if expiry else None,
                                     notes, reagent_id)
                                )
                                conn.commit()
                                st.success("Reagent updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating: {str(e)}")
                            finally:
                                if conn:
                                    conn.close()
                    with col2:
                        if st.form_submit_button("Delete"):
                            try:
                                conn = create_connection("lab_assistant.db")
                                conn.execute(
                                    "DELETE FROM reagents WHERE id=?",
                                    (reagent_id,)
                                )
                                conn.commit()
                                st.success("Reagent deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting: {str(e)}")
                            finally:
                                if conn:
                                    conn.close()
        else:
            st.info("No reagents available to update")

def data_visualizer():
    """ Data visualization tool with manual entry """
    st.title("📊 Data Visualizer")
    
    tab1, tab2 = st.tabs(["Upload Data", "Manual Entry"])
    
    with tab1:
        st.subheader("Upload Data File")
        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "txt"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file, sep='\t')
                
                st.success("File uploaded successfully!")
                st.write("Preview:")
                st.dataframe(df.head())
                
                # Data manipulation options
                st.subheader("Data Manipulation")
                cols = st.multiselect("Select columns to keep", df.columns.tolist(), default=df.columns.tolist())
                
                if cols:
                    df = df[cols]
                    st.dataframe(df.head())
                    
                    # Plotting options
                    st.subheader("Visualization Options")
                    plot_type = st.selectbox("Select Plot Type", 
                                           ["Line Plot", "Bar Plot", "Scatter Plot", "Histogram", "Box Plot"])
                    
                    if plot_type in ["Line Plot", "Bar Plot", "Scatter Plot"]:
                        x_axis = st.selectbox("X-axis", df.columns)
                        y_axis = st.selectbox("Y-axis", df.columns)
                        
                        if plot_type == "Line Plot":
                            fig, ax = plt.subplots()
                            sns.lineplot(data=df, x=x_axis, y=y_axis, ax=ax)
                            st.pyplot(fig)
                        elif plot_type == "Bar Plot":
                            fig, ax = plt.subplots()
                            sns.barplot(data=df, x=x_axis, y=y_axis, ax=ax)
                            st.pyplot(fig)
                        elif plot_type == "Scatter Plot":
                            fig, ax = plt.subplots()
                            sns.scatterplot(data=df, x=x_axis, y=y_axis, ax=ax)
                            st.pyplot(fig)
                    
                    elif plot_type == "Histogram":
                        col = st.selectbox("Select Column", df.columns)
                        bins = st.slider("Number of Bins", 5, 100, 20)
                        fig, ax = plt.subplots()
                        sns.histplot(data=df, x=col, bins=bins, ax=ax)
                        st.pyplot(fig)
                    
                    elif plot_type == "Box Plot":
                        col = st.selectbox("Select Column", df.columns)
                        fig, ax = plt.subplots()
                        sns.boxplot(data=df, x=col, ax=ax)
                        st.pyplot(fig)
                
            except Exception as e:
                st.error(f"Error processing file: {e}")
    
    with tab2:
        st.subheader("Manual Data Entry")
        
        # Initialize session state for manual data
        if 'manual_data' not in st.session_state:
            st.session_state.manual_data = pd.DataFrame(columns=["Sample", "Value1", "Value2"])
        
        # Data entry form
        with st.form("manual_entry_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sample = st.text_input("Sample ID")
            with col2:
                value1 = st.number_input("Measurement 1")
            with col3:
                value2 = st.number_input("Measurement 2")
            
            add_button = st.form_submit_button("Add Data Point")
            clear_button = st.form_submit_button("Clear All Data")
            
            if add_button and sample:
                new_row = {"Sample": sample, "Value1": value1, "Value2": value2}
                st.session_state.manual_data = pd.concat([
                    st.session_state.manual_data, 
                    pd.DataFrame([new_row])
                ], ignore_index=True)
                st.rerun()
            
            if clear_button:
                st.session_state.manual_data = pd.DataFrame(columns=["Sample", "Value1", "Value2"])
                st.rerun()
        
        # Display and edit data
        if not st.session_state.manual_data.empty:
            st.subheader("Current Data")
            
            # Allow editing of existing data
            edited_df = st.data_editor(
                st.session_state.manual_data,
                num_rows="dynamic",
                use_container_width=True
            )
            
            # Visualization options
            st.subheader("Visualization Options")
            plot_type = st.selectbox("Select Plot Type", 
                                   ["Scatter Plot", "Bar Chart", "Line Plot", "Histogram"])
            
            if plot_type == "Scatter Plot":
                fig, ax = plt.subplots()
                sns.scatterplot(data=edited_df, x="Value1", y="Value2", hue="Sample", ax=ax)
                st.pyplot(fig)
            
            elif plot_type == "Bar Chart":
                fig, ax = plt.subplots()
                edited_df.plot(kind="bar", x="Sample", y=["Value1", "Value2"], ax=ax)
                st.pyplot(fig)
            
            elif plot_type == "Line Plot":
                fig, ax = plt.subplots()
                sns.lineplot(data=edited_df, x="Sample", y="Value1", ax=ax)
                sns.lineplot(data=edited_df, x="Sample", y="Value2", ax=ax)
                st.pyplot(fig)
            
            elif plot_type == "Histogram":
                col = st.selectbox("Select Column", ["Value1", "Value2"])
                fig, ax = plt.subplots()
                sns.histplot(data=edited_df, x=col, kde=True, ax=ax)
                st.pyplot(fig)
            
            # Data export options
            st.subheader("Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download as CSV",
                    data=edited_df.to_csv(index=False).encode('utf-8'),
                    file_name="manual_data.csv",
                    mime="text/csv"
                )
            
            with col2:
                # PDF export would require additional libraries like reportlab
                st.button("🖨️ Print/PDF (Coming Soon)", disabled=True)
        else:
            st.info("Enter data points to begin visualization")

def help_section():
    """ Help and documentation section """
    st.title("❓ Help & Documentation")

    st.markdown("""
    ## Lab Assistant Pro - User Guide
    
    Welcome to Lab Assistant Pro, your all-in-one solution for laboratory management and experiment tracking.
    
    ### Features Overview
    
    1. **User Authentication**
       - Secure login and registration system to keep your data private
       - Each user has their own separate data space
    
    2. **Dashboard**
       - Overview of upcoming tasks
       - Quick access to recent experiments
       - Inventory alerts for low reagents
    
    3. **Dilution Calculator**
       - Calculate volumes needed for dilutions
       - Supports various concentration units
       - Saves calculation history
    
    4. **Solution Preparation Helper**
       - Guides for preparing solutions of specific concentrations
       - Supports mass-to-volume and molar preparations
    
    5. **Buffer Preparation Helper**
       - Recipes for common buffers (Tris, Phosphate, etc.)
       - Custom buffer creation
       - pH adjustment guidance
    
    6. **Lab Planner**
       - Task management with recurring options
       - Calendar view for scheduling
       - Experiment planning
    
    7. **Protocol Generator**
       - Structured templates for experiment documentation
       - Reagent and apparatus lists
       - Step-by-step procedure recording
    
    8. **Reagent Tracker**
       - Inventory management
       - Expiry date tracking
       - Location and supplier information
    
    9. **Data Visualizer**
       - Upload and visualize experimental data
       - Multiple plot types
       - Data manipulation tools
    
    ### Getting Started
    
    1. Register for an account or login if you already have one
    2. Explore the dashboard for an overview of your lab work
    3. Use the calculators and helpers for your experiments
    4. Track reagents and plan your work with the lab planner
    5. Document your experiments with the protocol generator
    
    ### Tips
    
    - Save frequently used buffer recipes for quick access
    - Set up recurring tasks for regular maintenance
    - Use the reagent tracker to avoid running out of supplies
    - Document experiments as you go for accurate records
    
    ### Support
    
    For any questions or issues, please contact support@labassistantpro.com
    """)

# --------------------------
# 7. MAIN APP FUNCTION
# --------------------------
def main():
    """ Main app controller """
    initialize_db()  # Initialize database
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"  # Default to dashboard after login
    
    # Navigation sidebar (only show when logged in)
    if st.session_state.logged_in:
        with st.sidebar:
            st.title(f"Welcome, {st.session_state.username}!")
            
            # Main navigation
            selected_page = option_menu(
                menu_title="Main Menu",
                options=["Dashboard", "Dilution Calculator", "Solution Helper", "Buffer Helper", 
                         "Lab Planner", "Protocol Generator", "Reagent Tracker", "Data Visualizer", "Help"],
                icons=["house", "calculator", "droplet", "eyedropper", "calendar", "journal-text", 
                      "flask", "graph-up", "question-circle"],
                default_index=0
            )
            
            # Map selection to page names
            page_mapping = {
                "Dashboard": "dashboard",
                "Dilution Calculator": "dilution_calculator",
                "Solution Helper": "solution_helper",
                "Buffer Helper": "buffer_helper",
                "Lab Planner": "lab_planner",
                "Protocol Generator": "protocol_generator",
                "Reagent Tracker": "reagent_tracker",
                "Data Visualizer": "data_visualizer",
                "Help": "help"
            }
            
            st.session_state.current_page = page_mapping.get(selected_page, "dashboard")
            
            st.markdown("---")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.user_id = None
                st.session_state.current_page = "login"
                st.rerun()
    
    # Page routing
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.current_page == "dashboard":
            dashboard_page()
        elif st.session_state.current_page == "dilution_calculator":
            dilution_calculator()
        elif st.session_state.current_page == "solution_helper":
            solution_helper()
        elif st.session_state.current_page == "buffer_helper":
            buffer_helper()
        elif st.session_state.current_page == "lab_planner":
            lab_planner()
        elif st.session_state.current_page == "protocol_generator":
            protocol_generator()
        elif st.session_state.current_page == "reagent_tracker":
            reagent_tracker()
        elif st.session_state.current_page == "data_visualizer":
            data_visualizer()
        elif st.session_state.current_page == "help":
            help_section()

# --------------------------
# 8. RUN THE APP
# --------------------------
if __name__ == "__main__":
    main()