"""
app.py
Streamlit frontend for ARIA - Autonomous Risk & Incident Assistant.
Sleek, SOC-ready interface with real-time pipeline telemetry and self-healing diagnostics.
"""

import streamlit as st
import requests
import os
import json
import time

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/query")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8000/health")

# Page Configuration
st.set_page_config(
    page_title="ARIA | Autonomous Cybersecurity Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Cybersecurity SOC Theme (Glassmorphism & Neon Accents)
st.markdown("""
<style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Dark Cyber Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(15, 23, 42, 1) 0%, rgba(9, 14, 26, 1) 90%);
        color: #F1F5F9;
    }

    /* Glassmorphism Cards */
    .cyber-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .cyber-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
    }

    .cyber-card-accent {
        border-left: 4px solid #38BDF8;
    }

    .cyber-card-success {
        border-left: 4px solid #10B981;
    }

    .cyber-card-warning {
        border-left: 4px solid #F59E0B;
    }

    /* Metric Badges */
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    .badge-pass {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-heal {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-fail {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Custom Header */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 16px;
        margin-bottom: 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .header-sub {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    /* Styled Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: #FFFFFF;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.55);
        transform: translateY(-1px);
    }

    /* Code & Output Styling */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Hide default Streamlit footer */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Function to check API backend status
@st.cache_data(ttl=10)
def check_backend_health():
    try:
        r = requests.get(HEALTH_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/shield-with-authorization-setting-and-password.png", width=64)
    st.markdown("### **ARIA Command Center**")
    st.caption("Self-Healing RAG Security Copilot")

    st.markdown("---")

    # Backend Connection Status
    backend_online = check_backend_health()
    if backend_online:
        st.markdown("🟢 **Backend Status**: `ONLINE`")
    else:
        st.markdown("🟡 **Backend Status**: `STANDBY / LOCAL`")

    st.markdown("---")

    # Mode Selection with Descriptions
    st.markdown("#### 🎯 **Analysis Mode**")
    mode_selection = st.radio(
        "Select Operation Mode:",
        options=["qa", "triage"],
        format_func=lambda m: "🔍 Knowledge Q&A" if m == "qa" else "🚨 SOC Incident Triage",
        label_visibility="collapsed"
    )

    if mode_selection == "qa":
        st.info("💡 **Q&A Mode**: Query MITRE ATT&CK techniques, security controls, CVE details, and defensive best practices.")
    else:
        st.warning("⚠️ **SOC Triage Mode**: Input raw endpoint alerts, command logs, or anomalous behavior for rapid incident analysis.")

    st.markdown("---")

    # Quick Demo Presets for Interviewers
    st.markdown("#### 🚀 **Preset Scenarios**")
    st.caption("Click to load real-world cybersecurity prompts:")

    preset_clicked = None
    if st.button("📌 MITRE T1059 (Command Line)", use_container_width=True):
        preset_clicked = "What is MITRE ATT&CK T1059 (Command and Scripting Interpreter) and how can defenders mitigate it?"
    if st.button("📌 Regsvr32 Suspicious Execution", use_container_width=True):
        preset_clicked = "I am observing regsvr32.exe connecting to an unverified external domain on an enterprise endpoint. Is this malicious?"
    if st.button("📌 OWASP API Security Top 10", use_container_width=True):
        preset_clicked = "Explain the risk of Broken Object Level Authorization (BOLA) and how to prevent it."
    if st.button("📌 Credential Dumping Detection", use_container_width=True):
        preset_clicked = "How can a SOC team detect LSASS memory dumping using Sysmon logs?"

    st.markdown("---")

    # System Info Card
    with st.expander("ℹ️ **System Architecture**", expanded=False):
        st.markdown("""
        - **LLM Engine**: `Llama 3.2 3B` (Ollama)
        - **Retrieval**: ChromaDB + BM25 Hybrid
        - **Evaluation**: Faithfulness, Relevancy & Precision
        - **Self-Healing**: Automated Query Reformulation & Dynamic Context Reranking
        """)

# Main UI Header
st.markdown("""
<div class="header-container">
    <div>
        <h1 class="header-title">🛡️ ARIA Cybersecurity Copilot</h1>
        <div class="header-sub">Autonomous Risk & Incident Assistant with Real-Time Self-Healing Retrieval</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Session State for Question Handling
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if preset_clicked:
    st.session_state.current_question = preset_clicked

# Question Input Box
input_placeholder = (
    "Ask any cybersecurity question (e.g. What is T1059 Command-Line Interface?)"
    if mode_selection == "qa"
    else "Paste alert logs or observed behavior (e.g. regsvr32.exe executing remote scrobj.dll script)"
)

user_question = st.text_area(
    "**Input Query / Incident Observation:**",
    value=st.session_state.current_question,
    placeholder=input_placeholder,
    height=110,
    key="question_input"
)

# Run Query Action Button
col_btn, col_space = st.columns([1, 4])
with col_btn:
    submit_query = st.button("⚡ Ask ARIA", type="primary", use_container_width=True)

# Main Execution Flow
if submit_query:
    query_text = user_question.strip()
    if not query_text:
        st.warning("⚠️ Please provide a valid question or incident observation.")
    else:
        st.session_state.current_question = query_text
        
        # Display Execution Spinner
        with st.status("🔍 **ARIA Pipeline Running...**", expanded=True) as status_container:
            st.write("1️⃣ Extracting hybrid vector embeddings & BM25 index...")
            time.sleep(0.3)
            st.write("2️⃣ Synthesizing response via Llama 3.2 LLM...")
            time.sleep(0.3)
            st.write("3️⃣ Evaluating response quality & applying self-healing if needed...")

            start_time = time.time()
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": query_text,
                        "mode": mode_selection
                    },
                    timeout=1200
                )
                response.raise_for_status()
                result = response.json()
                status_container.update(label="✅ **Analysis Complete!**", state="complete", expanded=False)
            except requests.exceptions.RequestException as e:
                status_container.update(label="❌ **Pipeline Error**", state="error", expanded=True)
                st.error(f"Could not connect to ARIA backend: {e}")
                st.stop()

        # Display Top Summary Telemetry Cards
        st.markdown("### 📊 **Executive Telemetry & Quality Audit**")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)

        # Confidence Metric
        conf_val = result.get("confidence", 0.0)
        conf_delta = "High Confidence" if conf_val >= 0.8 else "Moderate" if conf_val >= 0.6 else "Needs Review"
        m_col1.metric("🎯 Confidence Score", f"{conf_val:.2%}", delta=conf_delta)

        # Latency Metric
        lat_sec = result.get("latency_ms", 0) / 1000.0
        m_col2.metric("⚡ Pipeline Latency", f"{lat_sec:.2f}s", delta="CPU Local")

        # Evaluation Gate Metric
        passed = result.get("passed", False)
        healing_triggered = result.get("healing_triggered", False)
        
        if passed and not healing_triggered:
            status_text = "PASSED (Optimal)"
            badge_class = "badge-pass"
        elif healing_triggered:
            status_text = "HEALED (Auto-Corrected)"
            badge_class = "badge-heal"
        else:
            status_text = "WARN (Low Confidence)"
            badge_class = "badge-fail"

        m_col3.metric("🛡️ Verification Gate", "PASSED ✅" if passed else "REVIEW ⚠️")

        # Healing Cycles
        healing_attempts = result.get("healing_attempts", 0)
        m_col4.metric("🔄 Self-Healing Iterations", f"{healing_attempts} attempt(s)")

        st.markdown("---")

        # Layout Split: Left = Answer & Recommendations, Right = Self-Healing Diagnostics
        col_ans, col_diag = st.columns([3, 2])

        with col_ans:
            card_class = "cyber-card-success" if passed else "cyber-card-warning"
            st.markdown(f"""
            <div class="cyber-card {card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="margin: 0; color: #38BDF8;">🛡️ ARIA Security Analysis</h3>
                    <span class="metric-badge {badge_class}">{status_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(result.get("answer", "No answer generated."))

            st.markdown("#### 📄 **Export Analysis Report**")
            report_text = f"""# ARIA Security Incident & Knowledge Audit
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Mode**: {result.get('mode', mode_selection).upper()}
- **Question/Observation**: {query_text}
- **Confidence**: {conf_val:.2%}
- **Evaluation Gate**: {'PASSED' if passed else 'FAILED'}
- **Self-Healing Triggered**: {healing_triggered} ({healing_attempts} attempts)

## Analysis & Answer
{result.get('answer', '')}

## Evaluation Scores
{json.dumps(result.get('scores', {}), indent=2)}
"""
            st.download_button(
                label="📥 Download Markdown Report",
                data=report_text,
                file_name=f"aria_report_{int(time.time())}.md",
                mime="text/markdown"
            )

        with col_diag:
            st.markdown("""
            <div class="cyber-card cyber-card-accent">
                <h4 style="margin: 0 0 12px 0; color: #818CF8;">⚙️ RAG Quality Metrics</h4>
            </div>
            """, unsafe_allow_html=True)

            scores = result.get("scores", {})
            if isinstance(scores, dict):
                for metric_name, score_val in scores.items():
                    if isinstance(score_val, (int, float)):
                        formatted_name = metric_name.replace("_", " ").title()
                        st.write(f"**{formatted_name}**")
                        st.progress(min(max(float(score_val), 0.0), 1.0), text=f"{score_val:.2f}")

            st.markdown("---")
            st.markdown("#### 🔄 **Self-Healing Diagnostics**")

            if result.get("healing_triggered", False):
                st.warning(f"⚠️ **Self-Healing Activated**: The initial RAG retrieval scored below confidence thresholds. ARIA automatically executed {result.get('healing_attempts', 1)} repair cycle(s).")
                
                strategies = result.get("strategies_used", [])
                if strategies:
                    st.markdown("**Strategies Executed:**")
                    for s in strategies:
                        st.markdown(f"- 🔧 `{s}`")
            else:
                st.success("✅ **Direct Verification Passed**: High-confidence context retrieved on first attempt. No self-healing intervention required.")

# Footer Section
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B; font-size: 0.85rem;'>"
    "ARIA - Autonomous Risk & Incident Assistant | Enterprise Self-Healing RAG Pipeline"
    "</div>",
    unsafe_allow_html=True
)