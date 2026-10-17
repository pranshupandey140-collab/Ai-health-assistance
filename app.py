# app.py
"""
AI Healthcare Assistant — single-file Streamlit demo.
Educational information only; this app does not diagnose or prescribe.
Doctor entries are clearly labelled demo placeholders.
"""

from datetime import datetime
from collections import Counter
import io
import textwrap

import pandas as pd
import plotly.express as px
import streamlit as st
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(
    page_title="CareLens | AI Health Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- STYLE ---------------------------------
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(circle at 15% 0%, #14253d 0%, #0b1220 38%, #080d17 100%); color: #e5edf8; }
.stAppHeader, [data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.25rem; padding-bottom: 2.5rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #101a2b 0%, #0b1220 100%); border-right: 1px solid #26364c; }
.hero { padding: 1.5rem 1.7rem; border-radius: 22px; background: linear-gradient(120deg, #172554 0%, #164e63 58%, #065f46 100%); border: 1px solid #31566d; color: white; margin-bottom: 1rem; box-shadow: 0 14px 40px rgba(0,0,0,.25); }
.hero h1 { color: white; margin: 0; font-size: clamp(1.65rem, 3vw, 2.35rem); }
.hero p { color: #d8f3f5; margin: .5rem 0 0 0; font-size: 1rem; }
div[data-testid="stMetric"] { background: linear-gradient(145deg, #131f32, #101827); border: 1px solid #2a3b52; padding: 14px 16px; border-radius: 16px; box-shadow: 0 6px 20px rgba(0,0,0,.16); }
div[data-testid="stMetricLabel"] { color: #a9bdd4; }
div[data-testid="stMetricValue"] { color: #f4f8ff; }
div[data-testid="stTabs"] button { font-weight: 650; color: #c6d5e8; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #67e8f9; border-bottom-color: #22d3ee; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stNumberInput input { background: #101a2b !important; color: #e5edf8 !important; border-color: #33465f !important; }
[data-testid="stDataFrame"] { border: 1px solid #293b52; border-radius: 12px; overflow: hidden; }
.small-muted { color: #a9bdd4; font-size: .88rem; }
div.stButton > button, div.stDownloadButton > button { border-radius: 11px; border: 1px solid #35516e; font-weight: 650; }
hr { border-color: #293b52; }
</style>
""", unsafe_allow_html=True)

# ------------------------- SYMPTOM DATA -------------------------------
SYMPTOM_DB = {
    "Fever": {
        "keywords": ["fever", "temperature", "high temperature", "feverish"],
        "conditions": ["Viral illness", "Flu", "Other infection"],
        "specialties": ["General Medicine"],
        "advice": "If possible, measure your temperature with a thermometer and note the reading and time. Rest and drink fluids if you can. Seek medical advice if symptoms persist or worsen.",
        "home_check": "Use a digital thermometer according to its instructions. Record the temperature and time; feeling warm alone cannot confirm a fever.",
        "urgent": False,
    },
    "Cough": {
        "keywords": ["cough", "coughing"],
        "conditions": ["Respiratory infection", "Allergy", "Asthma"],
        "specialties": ["General Medicine", "Pulmonology", "ENT"],
        "advice": "Avoid smoke and other irritants. Drink fluids if safe for you. Seek medical care for a persistent or worsening cough.",
        "home_check": "Note when the cough started, whether it is dry or produces mucus, and whether you also have fever or breathing difficulty.",
        "urgent": False,
    },
    "Headache": {
        "keywords": ["headache", "head pain", "migraine"],
        "conditions": ["Tension headache", "Migraine", "Other causes"],
        "specialties": ["General Medicine", "Neurology"],
        "advice": "Rest somewhere quiet and drink water if appropriate. A sudden, extremely severe headache, confusion, weakness, or speech trouble needs emergency assessment.",
        "home_check": "Note when it began, severity, and any other symptoms. Do not delay urgent care for a sudden severe headache or neurological symptoms.",
        "urgent": True,
    },
    "Chest pain": {
        "keywords": ["chest pain", "chest tightness", "pain in chest"],
        "conditions": ["Heart-related cause", "Lung-related cause", "Muscle or digestive cause"],
        "specialties": ["Emergency Medicine", "Cardiology"],
        "advice": "New, severe, or persistent chest pain may be an emergency. Call 112 in India; do not wait for this app to assess it.",
        "home_check": "Do not try to rule out a serious cause at home. Stop exertion and seek emergency help for new, severe, or persistent pain.",
        "urgent": True,
    },
    "Shortness of breath": {
        "keywords": ["shortness of breath", "breathless", "difficulty breathing", "can't breathe", "cannot breathe", "breathing difficulty"],
        "conditions": ["Asthma or airway condition", "Heart or lung condition", "Infection"],
        "specialties": ["Emergency Medicine", "Pulmonology", "Cardiology"],
        "advice": "Sudden or severe breathing difficulty requires emergency care. Call 112 in India.",
        "home_check": "Do not rely on a home check if breathing is difficult. Sit upright if that helps and seek urgent help for sudden or severe symptoms.",
        "urgent": True,
    },
    "Skin rash": {
        "keywords": ["rash", "skin rash", "itchy skin", "itching"],
        "conditions": ["Skin irritation", "Allergy", "Skin infection"],
        "specialties": ["Dermatology", "General Medicine"],
        "advice": "Avoid suspected irritants. Facial or tongue swelling, or breathing difficulty, needs emergency care.",
        "home_check": "Note when it began and any new foods, medicines, soaps, or products. Do not delay care if swelling or breathing problems occur.",
        "urgent": False,
    },
    "Joint pain": {
        "keywords": ["joint pain", "painful joint", "knee pain", "wrist pain"],
        "conditions": ["Strain", "Arthritis", "Inflammation"],
        "specialties": ["General Medicine", "Orthopedics", "Rheumatology"],
        "advice": "Avoid activities that worsen the pain. A hot, swollen joint with fever needs prompt medical assessment.",
        "home_check": "Note which joint is affected, swelling, injury, and whether movement worsens pain. Avoid forcing painful movement.",
        "urgent": False,
    },
    "Back pain": {
        "keywords": ["back pain", "lower back pain", "backache"],
        "conditions": ["Muscle strain", "Spinal condition", "Other causes"],
        "specialties": ["General Medicine", "Orthopedics"],
        "advice": "Avoid heavy lifting. New bladder or bowel problems, numbness around the groin, or leg weakness need emergency assessment.",
        "home_check": "Note the location, onset, and any injury. Seek urgent help for new weakness, numbness around the groin, or bladder/bowel changes.",
        "urgent": False,
    },
    "Sore throat": {
        "keywords": ["sore throat", "throat pain", "painful throat"],
        "conditions": ["Viral infection", "Tonsillitis", "Irritation"],
        "specialties": ["General Medicine", "ENT"],
        "advice": "Rest and drink fluids if safe. Difficulty breathing or swallowing saliva needs urgent care.",
        "home_check": "Note whether you have fever, cough, or trouble swallowing. Do not delay care for breathing difficulty or inability to swallow saliva.",
        "urgent": False,
    },
    "Abdominal pain": {
        "keywords": ["abdominal pain", "stomach pain", "belly pain", "tummy pain"],
        "conditions": ["Digestive illness", "Constipation", "Other abdominal conditions"],
        "specialties": ["General Medicine", "Gastroenterology"],
        "advice": "Severe or worsening pain, fainting, blood in vomit or stool, or a rigid abdomen needs urgent assessment.",
        "home_check": "Note the location, when it started, and any vomiting or bowel changes. Severe or worsening pain needs urgent assessment.",
        "urgent": False,
    },
    "Diarrhea": {
        "keywords": ["diarrhea", "diarrhoea", "loose motion", "loose motions"],
        "conditions": ["Gastrointestinal infection", "Food-related illness", "Medication effects"],
        "specialties": ["General Medicine", "Gastroenterology"],
        "advice": "Oral rehydration solution may help prevent dehydration when used as directed. Seek care for blood, severe dehydration, or persistent symptoms.",
        "home_check": "Keep track of episodes and whether you can keep fluids down. Watch for very little urine, marked dizziness, or blood in stool.",
        "urgent": False,
    },
    "Dizziness": {
        "keywords": ["dizziness", "dizzy", "lightheaded", "light headed"],
        "conditions": ["Dehydration", "Inner-ear condition", "Blood pressure changes"],
        "specialties": ["General Medicine", "ENT", "Neurology"],
        "advice": "Sit or lie down to reduce fall risk. Dizziness with weakness, speech trouble, chest pain, or fainting needs urgent care.",
        "home_check": "Sit down and note when it started and any associated symptoms. Avoid driving while dizzy.",
        "urgent": False,
    },
    "Toothache": {
        "keywords": ["toothache", "tooth pain", "dental pain"],
        "conditions": ["Tooth decay", "Gum disease", "Dental infection"],
        "specialties": ["Dentistry"],
        "advice": "Arrange a dental assessment. Facial swelling or trouble swallowing or breathing needs urgent care.",
        "home_check": "Note which tooth hurts and whether there is swelling or fever. Avoid placing aspirin directly on the tooth or gums.",
        "urgent": False,
    },
    "Fatigue": {
        "keywords": ["fatigue", "tired", "tiredness", "weakness", "low energy"],
        "conditions": ["Sleep problems", "Anemia", "Other medical conditions"],
        "specialties": ["General Medicine"],
        "advice": "If fatigue persists, worsens, or affects daily life, consult a healthcare professional.",
        "home_check": "Record how long it has lasted, sleep, and other symptoms. Sudden severe weakness or confusion needs urgent assessment.",
        "urgent": False,
    },
    "Frequent urination": {
        "keywords": ["frequent urination", "urinating often", "pee frequently", "frequent pee"],
        "conditions": ["Urinary infection", "High blood sugar", "Other urinary conditions"],
        "specialties": ["General Medicine", "Urology", "Endocrinology"],
        "advice": "Seek assessment if this persists, is painful, or comes with fever or excessive thirst.",
        "home_check": "Note frequency, pain, fever, and unusual thirst. A home observation cannot identify the cause.",
        "urgent": False,
    },
    "Blurred vision": {
        "keywords": ["blurred vision", "blurry vision", "vision suddenly blurred"],
        "conditions": ["Refractive error", "Eye condition", "Other causes"],
        "specialties": ["Ophthalmology", "Emergency Medicine"],
        "advice": "Sudden vision loss or sudden visual changes need urgent medical assessment.",
        "home_check": "Do not delay urgent assessment for sudden vision changes. Avoid driving if your vision is affected.",
        "urgent": True,
    },
    "Anxiety": {
        "keywords": ["anxiety", "anxious", "panic", "panic attack"],
        "conditions": ["Stress response", "Anxiety condition", "Other causes"],
        "specialties": ["Mental Health", "General Medicine"],
        "advice": "A qualified professional can help if distress persists. Do not assume new or severe physical symptoms are anxiety.",
        "home_check": "If it feels safe, sit somewhere calm and try slow, comfortable breathing. Seek urgent care for severe physical symptoms or immediate danger.",
        "urgent": False,
    },
    "Ear pain": {
        "keywords": ["ear pain", "earache", "pain in ear"],
        "conditions": ["Ear infection", "Wax or irritation", "Referred pain"],
        "specialties": ["ENT", "General Medicine"],
        "advice": "Do not insert objects into the ear. Seek care for severe or persistent pain.",
        "home_check": "Note which ear hurts and whether there is fever or discharge. Do not put objects or unprescribed drops in the ear.",
        "urgent": False,
    },
}

SPECIALTIES = sorted({sp for item in SYMPTOM_DB.values() for sp in item["specialties"]})
STATES_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
    "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

DEMO_DOCTORS = pd.DataFrame([
    {"Doctor Name": "DEMO — replace with verified data", "State": "Karnataka", "District": "Bengaluru Urban", "Specialty": "General Medicine", "Verified": "No — demo"},
    {"Doctor Name": "DEMO — replace with verified data", "State": "Delhi", "District": "New Delhi", "Specialty": "Cardiology", "Verified": "No — demo"},
    {"Doctor Name": "DEMO — replace with verified data", "State": "Maharashtra", "District": "Mumbai", "Specialty": "Dermatology", "Verified": "No — demo"},
    {"Doctor Name": "DEMO — replace with verified data", "State": "Tamil Nadu", "District": "Chennai", "Specialty": "Pulmonology", "Verified": "No — demo"},
    {"Doctor Name": "DEMO — replace with verified data", "State": "Uttar Pradesh", "District": "Lucknow", "Specialty": "Orthopedics", "Verified": "No — demo"},
])

def load_doctors():
    try:
        df = pd.read_csv("data/doctors.csv")
        required = {"Doctor Name", "State", "District", "Specialty"}
        if required.issubset(df.columns):
            if "Verified" not in df.columns:
                df["Verified"] = "Not specified"
            return df, "Loaded data/doctors.csv"
    except (FileNotFoundError, pd.errors.EmptyDataError, OSError, UnicodeDecodeError):
        pass
    return DEMO_DOCTORS.copy(), "Demo placeholder records are displayed. They are not real recommendations."

def detect_symptoms(free_text, selected):
    haystack = (free_text or "").lower()
    found = set(selected or [])
    for name, data in SYMPTOM_DB.items():
        for keyword in data["keywords"]:
            if keyword in haystack:
                found.add(name)
                break
    # Stable database order makes results predictable.
    return [name for name in SYMPTOM_DB if name in found]

def analyze(symptoms):
    conditions = sorted({c for s in symptoms for c in SYMPTOM_DB[s]["conditions"]})
    specialties = sorted({sp for s in symptoms for sp in SYMPTOM_DB[s]["specialties"]})
    advice = [SYMPTOM_DB[s]["advice"] for s in symptoms]
    home_checks = [SYMPTOM_DB[s]["home_check"] for s in symptoms]
    urgent = any(SYMPTOM_DB[s]["urgent"] for s in symptoms)
    return conditions, specialties, advice, home_checks, urgent

def make_pdf(symptoms, conditions, specialties, advice, home_checks, title="CareLens Health Summary"):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    page_w, page_h = letter
    left, y, line_h = 48, page_h - 52, 15

    def line(text, bold=False):
        nonlocal y
        if y < 65:
            pdf.showPage()
            y = page_h - 52
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 11 if not bold else 12)
        for piece in textwrap.wrap(str(text), width=92) or [""]:
            if y < 65:
                pdf.showPage()
                y = page_h - 52
                pdf.setFont("Helvetica", 11)
            pdf.drawString(left, y, piece[:125])
            y -= line_h

    pdf.setFillColorRGB(0.05, 0.28, 0.38)
    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawString(left, y, title)
    y -= 27
    pdf.setFillColorRGB(0, 0, 0)
    line("Created: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    line("Educational information only — not a diagnosis or treatment plan.")
    y -= 5
    line("Detected symptoms", True)
    for item in symptoms:
        line("- " + item)
    y -= 5
    line("Possible explanations (not a diagnosis)", True)
    for item in conditions:
        line("- " + item)
    y -= 5
    line("Relevant specialties", True)
    for item in specialties:
        line("- " + item)
    y -= 5
    line("General advice", True)
    for item in advice:
        line("- " + item)
    y -= 5
    line("At-home observations (not diagnostic tests)", True)
    for item in home_checks:
        line("- " + item)
    y -= 5
    line("For sudden/severe symptoms, seek urgent medical care. In India, call 112 for emergencies.")
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

def init_state():
    defaults = {
        "history": [],
        "latest_result": None,
        "free_text": "",
        "selected_symptoms": [],
        "chat_messages": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()
doctors, doctor_message = load_doctors()

# ----------------------------- SIDEBAR --------------------------------
with st.sidebar:
    st.markdown("## 🩺 CareLens")
    st.caption("Personal health education dashboard")
    st.markdown("---")
    st.markdown("### Quick safety note")
    st.warning("This app cannot diagnose or prescribe. For sudden/severe symptoms, seek urgent help. In India call 112.")
    st.markdown("### At-home checks")
    st.write("Use a thermometer for temperature readings. Record when symptoms started and what changes. These observations do not identify a disease.")
    st.markdown("---")
    if st.button("🧹 Clear session history", use_container_width=True):
        st.session_state.history = []
        st.session_state.latest_result = None
        st.rerun()

# -------------------------------- HERO --------------------------------
st.markdown("""
<div class="hero">
  <h1>🩺 CareLens — AI Healthcare Assistant</h1>
  <p>Symptom education · At-home observations · Interactive analytics · PDF reports</p>
</div>
""", unsafe_allow_html=True)
st.caption("Educational support only · Not a trained diagnostic AI, medical device, or substitute for a clinician.")
st.warning("🚨 SAFETY FIRST: CareLens cannot diagnose, rule out emergencies, or prescribe. For sudden/severe chest pain, severe breathing difficulty, stroke-like symptoms, heavy bleeding, or loss of consciousness, call 112 in India or your local emergency number. Do not wait for an app response.")

tab_dashboard, tab_checker, tab_timeline, tab_chatbot, tab_doctors, tab_about = st.tabs([
    "📊 Dashboard", "🩹 Symptom Checker", "🕒 Symptom Timeline", "💬 CareLens Chat", "🔎 Doctor Finder", "ℹ️ About"
])

# ----------------------------- DASHBOARD ------------------------------
with tab_dashboard:
    st.subheader("Your health insights")
    history = st.session_state.history
    total_checks = len(history)
    unique_symptoms = len({s for entry in history for s in entry["symptoms"]})
    total_symptom_mentions = sum(len(entry["symptoms"]) for entry in history)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Symptom checks", total_checks)
    m2.metric("Unique symptoms", unique_symptoms)
    m3.metric("Symptom mentions", total_symptom_mentions)
    m4.metric("Guide entries", len(SYMPTOM_DB))

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Symptom guide coverage")
        coverage = pd.DataFrame({
            "Symptom": list(SYMPTOM_DB.keys()),
            "Listed explanations": [len(v["conditions"]) for v in SYMPTOM_DB.values()],
            "Specialties": [len(v["specialties"]) for v in SYMPTOM_DB.values()],
        })
        fig = px.bar(coverage, x="Symptom", y="Listed explanations", color="Specialties",
                     title="Guide coverage by symptom", template="plotly_dark")
        fig.update_layout(xaxis_tickangle=-35, margin=dict(l=10, r=10, t=55, b=10), legend_title="Specialties", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Symptom frequency in this session")
        if history:
            counts = Counter(s for entry in history for s in entry["symptoms"])
            freq_df = pd.DataFrame({"Symptom": list(counts.keys()), "Mentions": list(counts.values())})
            fig2 = px.pie(freq_df, names="Symptom", values="Mentions", hole=0.48,
                          title="Your analysed symptoms", template="plotly_dark")
            fig2.update_layout(margin=dict(l=10, r=10, t=55, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Run a symptom check to populate your personal session chart.")

    if history:
        st.markdown("#### Recent checks")
        history_df = pd.DataFrame([
            {"Time": h["time"], "Symptoms": ", ".join(h["symptoms"]), "Duration": h.get("duration", "Not recorded"), "Self-rated severity": h.get("severity", "Not recorded"), "Possible explanations": ", ".join(h["conditions"])}
            for h in reversed(history[-10:])
        ])
        st.dataframe(history_df, use_container_width=True, hide_index=True)

        st.markdown("#### ☁ Symptom word cloud")
        try:
            from wordcloud import WordCloud
            words = " ".join(s.lower() for entry in history for s in entry["symptoms"])
            cloud = WordCloud(width=1000, height=420, background_color="white",
                              colormap="viridis", collocations=False).generate(words)
            cloud_fig, cloud_ax = plt.subplots(figsize=(12, 4.5))
            cloud_ax.imshow(cloud, interpolation="bilinear")
            cloud_ax.axis("off")
            st.pyplot(cloud_fig, use_container_width=True)
            plt.close(cloud_fig)
        except ImportError:
            st.info("Word cloud is optional. Install it with: python -m pip install wordcloud")
    else:
        st.info("Your dashboard charts will update after you analyse symptoms.")

# ----------------------------- SYMPTOM CHECKER ------------------------
with tab_checker:
    st.subheader("Describe what you are experiencing")
    st.write("Select symptoms or describe them in your own words. The app only recognizes terms included in its small symptom guide.")
    selected = st.multiselect(
        "Select symptoms",
        options=list(SYMPTOM_DB.keys()),
        key="selected_symptoms",
        help="You can select more than one symptom.",
    )
    free_text = st.text_area(
        "Or describe your symptoms",
        key="free_text",
        placeholder="Example: I have a fever and cough since yesterday.",
        height=120,
    )
    meta1, meta2 = st.columns(2)
    with meta1:
        duration = st.selectbox("How long have you had these symptoms?", ["Just started", "Less than 24 hours", "1–3 days", "4–7 days", "More than a week", "Comes and goes"], key="symptom_duration")
    with meta2:
        severity = st.select_slider("How severe do they feel? (your own rating)", options=["Mild", "Moderate", "Severe"], value="Moderate", key="symptom_severity")
    st.caption("Severity is your personal description, not a medical score. Severe or rapidly worsening symptoms need prompt professional assessment.")
    if st.button("🔍 Analyse symptoms", type="primary", use_container_width=True):
        detected = detect_symptoms(free_text, selected)
        if not detected:
            st.session_state.latest_result = None
            st.warning("I could not match those words to this demo's symptom guide. Try selecting a symptom above or use a common term such as fever, cough, or headache.")
        else:
            conditions, specialties, advice, home_checks, urgent = analyze(detected)
            result = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration,
                "severity": severity,
                "symptoms": detected,
                "conditions": conditions,
                "specialties": specialties,
                "advice": advice,
                "home_checks": home_checks,
                "urgent": urgent,
            }
            st.session_state.latest_result = result
            st.session_state.history.append(result)
            st.rerun()

    result = st.session_state.latest_result
    if result:
        st.markdown("---")
        st.subheader("Your symptom summary")
        if result["urgent"]:
            st.error("⚠️ One or more selected symptoms can require urgent assessment. If symptoms are sudden or severe, seek emergency care. In India, call 112.")
        else:
            st.info("This is general educational information, not a diagnosis. Consult a qualified healthcare professional if symptoms persist, worsen, or worry you.")
        a, b = st.columns(2)
        with a:
            st.markdown("#### 🩹 Symptoms recognised")
            for item in result["symptoms"]:
                st.write("• " + item)
            st.markdown("#### 🧭 Relevant specialties")
            st.write(", ".join(result["specialties"]) or "No specialty listed")
        with b:
            st.markdown("#### 🔎 Possible explanations")
            st.write(", ".join(result["conditions"]))
            st.caption("These are examples, not a prediction of what condition you have.")
        st.markdown("#### 🏠 Safe at-home observations")
        for item in result["home_checks"]:
            st.write("• " + item)
        st.markdown("#### 📌 General guidance")
        for item in result["advice"]:
            st.write("• " + item)

        report = make_pdf(result["symptoms"], result["conditions"], result["specialties"], result["advice"], result["home_checks"])
        st.download_button(
            "📄 Download this summary as PDF",
            data=report,
            file_name="carelens_health_summary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    if st.session_state.history:
        all_history = st.session_state.history
        all_symptoms = [s for entry in all_history for s in entry["symptoms"]]
        all_conditions = sorted({c for entry in all_history for c in entry["conditions"]})
        all_specialties = sorted({sp for entry in all_history for sp in entry["specialties"]})
        all_advice = sorted({a for entry in all_history for a in entry["advice"]})
        all_home = sorted({h for entry in all_history for h in entry["home_checks"]})
        history_pdf = make_pdf(all_symptoms, all_conditions, all_specialties, all_advice, all_home,
                               title="CareLens — Session History")
        st.download_button(
            "📚 Download full session history (PDF)",
            data=history_pdf,
            file_name="carelens_session_history.pdf",
            mime="application/pdf",
        )

# ----------------------------- DOCTOR DIRECTORY -----------------------
with tab_doctors:
    st.subheader("🔎 Doctor finder")
    st.info(doctor_message + " Sample records are not real doctor recommendations. Confirm credentials and current availability independently.")
    st.markdown("#### Search for care near you")
    find_col1, find_col2 = st.columns([2, 1])
    with find_col1:
        search_location = st.text_input("City, area or PIN code", placeholder="e.g., Bengaluru, Karnataka")
    with find_col2:
        search_specialty = st.selectbox("Specialty to search", ["General physician"] + SPECIALTIES, key="external_doctor_specialty")
    if search_location.strip():
        import urllib.parse
        query = urllib.parse.quote_plus(f"{search_specialty} near {search_location.strip()}")
        st.markdown(f"[Search current nearby results on Google Maps](https://www.google.com/maps/search/{query}) · [Search on Practo](https://www.practo.com/search/doctors?results_type=doctor&q={query})")
    else:
        st.caption("Enter a location to create external search links. CareLens does not verify live listings or your location automatically.")
    st.markdown("#### Filter the local CSV / demo directory")
    d1, d2, d3 = st.columns(3)
    state_list = sorted(doctors["State"].dropna().astype(str).unique().tolist()) if "State" in doctors else []
    state = d1.selectbox("State / UT", ["All"] + state_list)
    if state == "All":
        districts = sorted(doctors["District"].dropna().astype(str).unique().tolist()) if "District" in doctors else []
    else:
        districts = sorted(doctors.loc[doctors["State"].astype(str) == state, "District"].dropna().astype(str).unique().tolist())
    district = d2.selectbox("District", ["All"] + districts)
    specialties_in_data = sorted(doctors["Specialty"].dropna().astype(str).unique().tolist()) if "Specialty" in doctors else []
    specialty = d3.selectbox("Specialty", ["All"] + specialties_in_data)

    filtered = doctors.copy()
    if state != "All":
        filtered = filtered[filtered["State"].astype(str) == state]
    if district != "All":
        filtered = filtered[filtered["District"].astype(str) == district]
    if specialty != "All":
        filtered = filtered[filtered["Specialty"].astype(str) == specialty]
    st.metric("Matching records", len(filtered))
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.markdown("**External directories — verify current details and credentials:**")
    st.markdown("- [National Medical Commission](https://www.nmc.org.in/)")
    st.markdown("- [Practo](https://www.practo.com/)")
    st.markdown("- [Ayushman Bharat Digital Mission](https://abdm.gov.in/)")

# -------------------------- SYMPTOM TIMELINE --------------------------
with tab_timeline:
    st.subheader("🕒 Your symptom timeline")
    st.write("Track what you recorded over this Streamlit session. This is a personal log—not a clinical record or prediction.")
    if st.session_state.history:
        timeline_rows = []
        for entry in st.session_state.history:
            timeline_rows.append({
                "Recorded at": entry.get("time", "Unknown"),
                "Symptoms": ", ".join(entry.get("symptoms", [])),
                "Duration at entry": entry.get("duration", "Not recorded"),
                "Self-rated severity": entry.get("severity", "Not recorded"),
                "Urgent flag": "Review urgently if sudden/severe" if entry.get("urgent") else "No automatic urgent flag",
            })
        timeline_df = pd.DataFrame(timeline_rows)
        st.dataframe(timeline_df.sort_values("Recorded at", ascending=False), use_container_width=True, hide_index=True)
        st.markdown("#### Symptom entries over time")
        timeline_counts = pd.DataFrame(timeline_rows)
        timeline_counts["Entry"] = range(1, len(timeline_counts) + 1)
        timeline_long = timeline_counts.assign(Symptom=timeline_counts["Symptoms"].str.split(", ")).explode("Symptom")
        fig_timeline = px.scatter(timeline_long, x="Entry", y="Symptom", color="Self-rated severity",
                                  hover_data=["Recorded at", "Duration at entry"],
                                  title="Recorded symptom timeline", template="plotly_dark")
        fig_timeline.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_timeline, use_container_width=True)
        st.caption("A later entry does not automatically mean symptoms improved or worsened. Record changes accurately and share concerns with a clinician.")
    else:
        st.info("No timeline entries yet. Use Symptom Checker to add your first entry.")
    st.markdown("#### Quick observation log")
    with st.form("observation_log_form"):
        obs_time = st.date_input("Date of observation", value=datetime.now().date())
        obs_symptom = st.text_input("What changed?", placeholder="e.g., cough more frequent at night")
        obs_note = st.text_area("Optional notes for your clinician", placeholder="What you noticed, readings and context. Avoid sharing unnecessary identifying details.")
        save_obs = st.form_submit_button("Add observation")
    if save_obs:
        if obs_symptom.strip():
            st.session_state.history.append({
                "time": datetime.combine(obs_time, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S"),
                "duration": "Observation log", "severity": "Not rated", "symptoms": [obs_symptom.strip()],
                "conditions": ["Not assessed"], "specialties": [], "advice": [obs_note.strip()] if obs_note.strip() else [],
                "home_checks": [], "urgent": False, "observation_only": True
            })
            st.success("Observation added to this session's timeline.")
            st.rerun()
        else:
            st.warning("Enter a short description before saving.")

# ------------------------------ CHATBOT -------------------------------
def chatbot_reply(message):
    """Transparent local FAQ helper; no external AI model or medical diagnosis."""
    text = (message or "").lower().strip()
    emergency_terms = ["chest pain", "can't breathe", "cannot breathe", "difficulty breathing", "shortness of breath", "stroke", "face droop", "heavy bleeding", "unconscious", "suicidal"]
    if any(term in text for term in emergency_terms):
        return ("⚠️ **This may need urgent help.** If symptoms are sudden or severe, call 112 in India (or your local emergency number) now. Do not wait for chat or use this app to rule out an emergency.")
    if any(x in text for x in ["diagnose", "what disease", "which disease", "do i have", "is it cancer"]):
        return ("I can’t diagnose or estimate your disease risk. I can explain general health information and help you prepare observations to discuss with a qualified clinician. If symptoms persist, worsen, or worry you, arrange medical assessment.")
    if any(x in text for x in ["temperature", "fever", "thermometer"]):
        return ("For an at-home observation, use a digital thermometer exactly as its instructions say, record the reading, measurement method and time, and note related symptoms. A reading alone does not establish the cause. Seek professional advice if symptoms persist or worsen.")
    if any(x in text for x in ["report", "pdf"]):
        return ("Open Symptom Checker after saving an entry to download the current summary PDF. You can also download the session history from that section. Review the report for accuracy before sharing it with a clinician.")
    if any(x in text for x in ["doctor", "specialist", "hospital", "clinic", "find"]):
        return ("Open **Doctor Finder** to filter any available directory dataset and search an external map/directory. The built-in sample entries are placeholders, not real recommendations. Confirm the clinician’s credentials, availability and contact details independently.")
    if any(x in text for x in ["home", "check at home", "measure", "monitor"]):
        return ("Safe observations may include when symptoms started, how they change, a temperature reading from a thermometer, fluid intake, and any relevant measurements from devices you already use. These observations are not diagnostic tests. Do not delay care for severe or worsening symptoms.")
    if any(x in text for x in ["history", "timeline", "track"]):
        return ("Use **Symptom Timeline** to review entries and add a dated observation. The log is held in the current Streamlit session and may disappear after a reset; it is not a permanent medical record.")
    return ("I’m CareLens’s local health-information helper. I can explain how to record symptoms, use the timeline, export a PDF, or find a directory. I’m not a clinician and cannot diagnose, prescribe, or confirm that a symptom is safe. What would you like help with?")

with tab_chatbot:
    st.subheader("💬 CareLens health-information chat")
    st.caption("Local FAQ-style assistant with safety routing. It does not call an LLM, access medical records, diagnose, or prescribe.")
    st.info("For sudden/severe symptoms, call 112 in India or your local emergency number. Chat is not monitored and is not an emergency service.")
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    with st.form("carelens_chat_form", clear_on_submit=True):
        user_message = st.text_input("Ask about safe observations, reports, timeline or finding a doctor", placeholder="e.g., How should I record a temperature?")
        chat_submit = st.form_submit_button("Send message", type="primary")
    if chat_submit and user_message.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_message.strip()})
        answer = chatbot_reply(user_message)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()
    if st.button("Clear chat", key="clear_chat"):
        st.session_state.chat_messages = []
        st.rerun()

# -------------------------------- ABOUT --------------------------------
with tab_about:
    st.subheader("About this project")
    st.write(
        "CareLens is a dark-themed healthcare education demo combining a rule-based symptom guide, safe at-home observation prompts, a session dashboard, advanced interactive charts, symptom timeline, local FAQ chatbot, PDF summaries, and a filterable doctor finder."
    )
    st.warning(
        "This is not a trained AI model and cannot determine the cause of symptoms. "
        "The condition list is illustrative. Do not use it to delay medical care or make treatment decisions."
    )
    st.markdown("#### Optional verified doctor CSV")
    st.write("If you have a legitimate, current dataset, save it as `data/doctors.csv` with these columns:")
    st.code("Doctor Name,State,District,Specialty,Verified", language="text")
    st.markdown("#### Install dependencies")
    st.code("python -m pip install streamlit pandas plotly matplotlib reportlab", language="powershell")
    st.markdown("#### Run")
    st.code("python -m streamlit run app.py", language="powershell")
    st.caption("History and chat are stored only in the current Streamlit session and may disappear when the session resets. No data is sent to an AI provider by this code. Do not enter sensitive personal or medical identifiers.")
