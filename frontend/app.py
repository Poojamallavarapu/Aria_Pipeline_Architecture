"""
app.py
Streamlit frontend for ARIA - Autonomous Risk & Incident Assistant.
High-contrast, modern cybersecurity SOC theme with telemetry & self-healing diagnostics.
"""

import streamlit as st
import requests
import os
import json
import time

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/query")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8000/health")

# 1. Page Configuration
st.set_page_config(
    page_title="ARIA | Autonomous Cybersecurity Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. High-Contrast Cybersecurity SOC Theme CSS
st.markdown("""
<style>
    /* Global App Background */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }

    /* Force high contrast text across main container */
    .stMarkdown, p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
    }

    /* Sidebar background & text contrast */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937;
    }
    
    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    /* Dark Mode Text Input Area */
    textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
    }
    
    textarea:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 1px #38BDF8 !important;
    }

    /* Primary Action Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 20px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
        transform: translateY(-1px);
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 14px 18px !important;
        border-radius: 10px !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-weight: 700 !important;
    }

    /* Custom Header Banner */
    .header-banner {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }

    .header-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38BDF8 !important;
        margin: 0;
    }

    .header-sub {
        color: #94A3B8 !important;
        font-size: 0.9rem;
        margin-top: 4px;
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


# 3. Sidebar Setup
with st.sidebar:
    st.markdown("## 🛡️ **ARIA Controls**")
    st.caption("Self-Healing RAG Copilot")

    st.markdown("---")

    # Backend Connection Status
    backend_online = check_backend_health()
    if backend_online:
        st.success("🟢 **Backend Status**: `ONLINE`")
    else:
        st.info("🟢 **Backend Status**: `READY`")

    st.markdown("---")

    # Mode Selection
    st.markdown("### 🎯 **Analysis Mode**")
    mode_selection = st.radio(
        "Select Operation Mode:",
        options=["qa", "triage"],
        format_func=lambda m: "🔍 Knowledge Q&A" if m == "qa" else "🚨 SOC Incident Triage",
        label_visibility="collapsed"
    )

    if mode_selection == "qa":
        st.caption("💡 **Q&A Mode**: MITRE ATT&CK techniques, security controls, CVE details, and defensive concepts.")
    else:
        st.caption("🚨 **SOC Triage Mode**: Endpoint alerts, process logs, or anomalous command executions.")

    st.markdown("---")

    # Preset Sample Prompts for Interview Demos
    st.markdown("### 🚀 **Demo Preset Prompts**")
    st.caption("Click any preset to auto-load query:")

    preset_clicked = None
    if st.button("📌 MITRE T1059 (Command Line)", use_container_width=True):
        preset_clicked = "What is MITRE ATT&CK T1059 (Command and Scripting Interpreter) and how can defenders mitigate it?"
    if st.button("📌 Regsvr32 Suspicious Execution", use_container_width=True):
        preset_clicked = "I am observing regsvr32.exe connecting to an unverified external domain on an enterprise endpoint. Is this malicious?"
    if st.button("📌 OWASP API Security Top 10", use_container_width=True):
        preset_clicked = "Explain the risk of Broken Object Level Authorization (BOLA) and how to prevent it."
    if st.button("📌 Credential Dumping via LSASS", use_container_width=True):
        preset_clicked = "How can a SOC team detect LSASS memory dumping using Sysmon logs?"

    st.markdown("---")

    # Architecture Overview Expander
    with st.expander("ℹ️ **System Architecture**", expanded=False):
        st.markdown("""
        - **LLM Engine**: `Llama 3.2 3B` (Ollama)
        - **Retrieval**: ChromaDB + BM25 Hybrid
        - **Evaluation**: Faithfulness & Precision Gate
        - **Self-Healing**: Query Reformulation & Dynamic Reranking
        """)

# 4. Main Page Header
st.markdown("""
<div class="header-banner">
    <div class="header-title">🛡️ ARIA — Autonomous Cybersecurity Copilot</div>
    <div class="header-sub">Self-Healing RAG Engine • Incident Triage & Knowledge Intelligence</div>
</div>
""", unsafe_allow_html=True)

# Session State for Question Handling
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if preset_clicked:
    st.session_state.current_question = preset_clicked

# 5. Input Query Box (Containerized)
with st.container(border=True):
    st.markdown("### 📝 **Input Query / Observation**")

    input_placeholder = (
        "e.g. What is T1059 Command-Line Interface and how to mitigate it?"
        if mode_selection == "qa"
        else "e.g. Observing regsvr32.exe executing remote scrobj.dll script on domain controller"
    )

    user_question = st.text_area(
        "Enter query or incident log details below:",
        value=st.session_state.current_question,
        placeholder=input_placeholder,
        height=100,
        label_visibility="collapsed"
    )

    col_btn, col_blank = st.columns([1, 3])
    with col_btn:
        submit_query = st.button("⚡ Run ARIA Analysis", type="primary", use_container_width=True)

# 6. Pipeline Execution & Results Presentation
if submit_query:
    query_text = user_question.strip()
    if not query_text:
        st.warning("⚠️ Please enter a question or observation before submitting.")
    else:
        st.session_state.current_question = query_text

        # Execution Progress Status
        with st.status("🔍 **ARIA Pipeline Processing...**", expanded=True) as status_box:
            st.write("1️⃣ Performing Hybrid Vector (ChromaDB) + Keyword (BM25) Retrieval...")
            time.sleep(0.3)
            st.write("2️⃣ Synthesizing Contextual Answer via Local Llama 3.2 3B...")
            time.sleep(0.3)
            st.write("3️⃣ Running Quality Evaluation & Self-Healing Audit...")

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
                status_box.update(label="✅ **Analysis Completed Successfully!**", state="complete", expanded=False)
            except requests.exceptions.RequestException as e:
                status_box.update(label="❌ **Backend Connection Failed**", state="error", expanded=True)
                st.error(f"Could not connect to ARIA backend: {e}")
                st.stop()

        st.markdown("---")

        # 7. Executive Telemetry Row
        st.markdown("### 📊 **Executive Telemetry & Verification Audit**")

        m1, m2, m3, m4 = st.columns(4)

        conf_val = result.get("confidence", 0.0)
        m1.metric("🎯 Confidence Score", f"{conf_val:.1%}")

        lat_sec = result.get("latency_ms", 0) / 1000.0
        m2.metric("⚡ Response Latency", f"{lat_sec:.1f}s")

        passed = result.get("passed", False)
        healing_triggered = result.get("healing_triggered", False)

        m3.metric("🛡️ Quality Gate", "PASSED ✅" if passed else "REVIEW ⚠️")

        healing_attempts = result.get("healing_attempts", 0)
        m4.metric("🔄 Healing Cycles", f"{healing_attempts} attempt(s)")

        st.markdown("---")

        # 8. Main Analysis & Self-Healing Diagnostics Split Layout
        col_main, col_diag = st.columns([3, 2])

        with col_main:
            with st.container(border=True):
                st.markdown("### 🛡️ **ARIA Security Analysis**")
                st.markdown(result.get("answer", "No response generated."))

                st.markdown("---")
                
                # Report Download
                report_md = f"""# ARIA Security Incident Report
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Mode**: {result.get('mode', mode_selection).upper()}
- **Query**: {query_text}
- **Confidence**: {conf_val:.1%}
- **Quality Gate**: {'PASSED' if passed else 'FAILED'}
- **Self-Healing Triggered**: {healing_triggered} ({healing_attempts} attempts)

## Security Analysis & Recommendations
{result.get('answer', '')}

## Metric Scores
{json.dumps(result.get('scores', {}), indent=2)}
"""
                st.download_button(
                    label="📥 Download Audit Report (.md)",
                    data=report_md,
                    file_name=f"aria_security_report_{int(time.time())}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

        with col_diag:
            with st.container(border=True):
                st.markdown("### ⚙️ **Quality Metrics**")
                scores = result.get("scores", {})
                if isinstance(scores, dict):
                    for m_name, s_val in scores.items():
                        if isinstance(s_val, (int, float)):
                            st.write(f"**{m_name.replace('_', ' ').title()}**")
                            st.progress(min(max(float(s_val), 0.0), 1.0), text=f"{s_val:.2f}")

                st.markdown("---")
                st.markdown("### 🔄 **Self-Healing Audit**")

                if healing_triggered:
                    st.warning(f"⚠️ **Self-Healing Activated**: Initial context retrieval fell below confidence thresholds. ARIA automatically executed {healing_attempts} repair cycle(s).")
                    strategies = result.get("strategies_used", [])
                    if strategies:
                        st.markdown("**Strategies Executed:**")
                        for strat in strategies:
                            st.markdown(f"- 🔧 `{strat}`")
                else:
                    st.success("✅ **Direct Verification Passed**: High-confidence context retrieved on initial turn. No healing intervention required.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B; font-size: 0.85rem;'>"
    "ARIA — Autonomous Risk & Incident Assistant | Enterprise Self-Healing RAG Architecture"
    "</div>",
    unsafe_allow_html=True
)