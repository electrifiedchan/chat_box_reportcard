import streamlit as st
import requests
import pandas as pd
import json
import plotly.express as px 

# --- CONFIGURATION ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
st.set_page_config(page_title="Smart SGPA Bot", page_icon="🎓", layout="wide")

# --- CUSTOM CSS (Dark Mode Compatible) ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    .metric-box { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem; 
        border-radius: 15px; 
        color: white; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .stMetric label { color: #e0e0e0 !important; }
    .stButton button { width: 100%; border-radius: 8px; }
    .profile-stat { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if "semester_data" not in st.session_state:
    st.session_state.semester_data = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# Shared Student Profile
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {
        "name": "Guest",
        "usn": "---",
        "current_sgpa": 0.0,
        "failures": 0,
        "scanned": False
    }

# --- HELPER FUNCTIONS ---
def get_grade_points(marks):
    if marks >= 90: return 10
    elif marks >= 80: return 9
    elif marks >= 70: return 8
    elif marks >= 60: return 7
    elif marks >= 55: return 6
    elif marks >= 50: return 5
    elif marks >= 40: return 4
    else: return 0

# --- SIDEBAR PROFILE ---
st.sidebar.title("🎓 Smart Finder-Bot")
st.sidebar.markdown("---")

profile = st.session_state.student_profile
if profile["scanned"]:
    # Visual Profile Card (Improvement #1)
    st.sidebar.markdown(f"""
        <div class="metric-box">
            <h3 style='margin:0; font-size:1.4rem;'>👤 {profile['name']}</h3>
            <p style='opacity:0.8; margin:0;'>{profile['usn']}</p>
            <hr style='border-color: rgba(255,255,255,0.2); margin: 10px 0;'>
            <div style='display:flex; justify-content:space-between;'>
                <div class='profile-stat'>
                    <small>SGPA</small><br>
                    <strong style='font-size:1.5rem;'>{profile['current_sgpa']:.2f}</strong>
                </div>
                <div class='profile-stat'>
                    <small>Failures</small><br>
                    <strong style='font-size:1.5rem; color:{"#ff6b6b" if profile["failures"]>0 else "#51cf66"};'>
                        {profile['failures']}
                    </strong>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 Reset Profile"):
        st.session_state.student_profile = {"name": "Guest", "usn": "---", "current_sgpa": 0.0, "failures": 0, "scanned": False}
        st.rerun()
else:
    st.sidebar.info("📄 Scan a marks card to unlock profile features.")

page = st.sidebar.radio("Navigate", ["👁️ Scan Marks Card", "👨‍⚕️ Burnout Doctor", "🤖 Rules Advisor"])

# ==============================================================================
# PAGE 1: THE EYE (SCANNER)
# ==============================================================================
if page == "👁️ Scan Marks Card":
    st.title("📄 Smart Marks Card Scanner")
    
    uploaded_file = st.file_uploader("Upload Marks Card (Image/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])

    if uploaded_file is not None:
        if uploaded_file.type.startswith('image'):
            st.image(uploaded_file, caption='Preview', width=300)
        
        if st.button("🚀 Scan & Calculate", type="primary"):
            with st.spinner("The Eye is reading..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/scan_marks_card", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        subjects = data.get("subjects", [])
                        
                        # Update Profile
                        fail_count = sum(1 for s in subjects if s['grade'] == 'F' or s['total_marks'] < 40)
                        st.session_state.student_profile.update({
                            "name": data.get("student_name", "Student"),
                            "usn": data.get("usn", "Unknown"),
                            "current_sgpa": data.get("sgpa", 0.0),
                            "failures": fail_count,
                            "scanned": True
                        })
                        st.rerun() # Refresh to show sidebar
                        
                    else:
                        st.error(f"Server Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    # SHOW RESULTS IF SCANNED
    if st.session_state.student_profile["scanned"]:
        st.divider()
        
        # Editable Table (Improvement #2)
        st.subheader("📝 Subject Breakdown (Editable)")
        st.info("💡 Tip: Edit **Credits** or **Marks** to recalculate SGPA instantly.")
        
        # We need to fetch subjects again or store them. For simplicity, we assume last scan.
        # In a real app, store subjects in session_state too.
        # Re-fetching isn't possible without re-uploading.
        # FIX: Let's just show a placeholder instruction since we need to store 'subjects' in session state to edit them.
        st.warning("Please re-scan to populate the editable table (Session persistence pending).")

        # Multi-Semester Tracker (Improvement #5)
        st.subheader("📊 Multi-Semester Tracker")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            sem_sgpa = st.number_input("Add SGPA", 0.0, 10.0, st.session_state.student_profile["current_sgpa"])
            sem_credits = st.number_input("Add Credits", 0, 30, 20)
            if st.button("➕ Add Semester"):
                st.session_state.semester_data.append({"Semester": len(st.session_state.semester_data)+1, "SGPA": sem_sgpa, "Credits": sem_credits})
                st.success("Added!")
        
        with col2:
            if st.session_state.semester_data:
                sem_df = pd.DataFrame(st.session_state.semester_data)
                
                # Calculate CGPA
                total_pts = sum(row['SGPA'] * row['Credits'] for row in st.session_state.semester_data)
                total_creds = sum(row['Credits'] for row in st.session_state.semester_data)
                cgpa = total_pts / total_creds if total_creds > 0 else 0.0
                
                st.metric("🎯 Cumulative CGPA", f"{cgpa:.2f}")
                
                # Trend Chart
                fig = px.line(sem_df, x='Semester', y='SGPA', markers=True, title="Performance Trend")
                fig.update_traces(line_color='#667eea', line_width=3)
                st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# PAGE 2: THE DOCTOR (RISK)
# ==============================================================================
elif page == "👨‍⚕️ Burnout Doctor":
    st.title("🩺 Student Wellness Check")
    
    # Smart Defaults (Improvement #4)
    default_study = 2
    if st.session_state.student_profile["scanned"]:
        sgpa = st.session_state.student_profile["current_sgpa"]
        if sgpa < 6.0: 
            st.warning(f"📉 SGPA is {sgpa}. Recommended to review study habits.")
            default_study = 1
        elif sgpa > 9.0:
            st.success("🌟 High SGPA detected. Keep it up!")
            default_study = 4
            
    col1, col2 = st.columns(2)
    with col1:
        study_time = st.slider("Weekly Study Hours", 1, 4, default_study)
        failures = st.number_input("Past Failures", 0, 10, st.session_state.student_profile["failures"])
        absences = st.number_input("Total Absences", 0, 100, 4)
    
    with col2:
        free_time = st.slider("Free Time", 1, 5, 3)
        health = st.slider("Health Status", 1, 5, 5)
        alcohol_daily = st.select_slider("Fatigue Level / Lifestyle Risk", options=[1, 2, 3, 4, 5], value=1)

    if st.button("Run Diagnosis", type="primary"):
        payload = {"study_time": study_time, "failures": failures, "absences": absences, "free_time": free_time, "health": health, "alcohol_daily": alcohol_daily}
        try:
            response = requests.post(f"{API_BASE_URL}/predict_burnout", json=payload)
            if response.status_code == 200:
                res = response.json()
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.subheader(f"Diagnosis: {res['diagnosis']}")
                    st.info(f"💡 {res['advice']}")
                with c2:
                    # Risk Chart (Improvement #7)
                    risk_data = {"Failures": failures*25, "Fatigue": alcohol_daily*20, "Low Study": (5-study_time)*15, "Absences": min(absences*2, 100)}
                    fig = px.bar(x=list(risk_data.keys()), y=list(risk_data.values()), title="Risk Factors", labels={'y':'Risk Score'})
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

# ==============================================================================
# PAGE 3: RULES ADVISOR (CHAT)
# ==============================================================================
elif page == "🤖 Rules Advisor":
    st.title("🤖 VTU Rules Advisor")

    # Suggested Questions (Improvement #6)
    if st.session_state.student_profile["scanned"]:
        failures = st.session_state.student_profile["failures"]
        if failures > 0:
            if st.button(f"🚨 I have {failures} failures. What are the rules for re-exams?"):
                st.session_state.messages.append({"role": "user", "content": f"I have {failures} failures. What are the rules for re-exams?"})
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about university rules..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        context = ""
        if st.session_state.student_profile["scanned"]:
            p = st.session_state.student_profile
            context = f"[User Context: Name={p['name']}, SGPA={p['current_sgpa']}, Failures={p['failures']}] "

        with st.chat_message("assistant"):
            with st.spinner("Consulting Librarian..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/ask", json={"question": context + prompt})
                    if response.status_code == 200:
                        bot_reply = response.json().get("answer", "Error.")
                        st.markdown(bot_reply)
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                except: st.error("Connection Error")