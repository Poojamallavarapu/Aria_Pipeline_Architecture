"""
app.py
Streamlit frontend for ARIA. Calls the FastAPI backend.
"""

import streamlit as st
import requests
import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/query")

st.set_page_config(
    page_title="ARIA",
    page_icon="🛡️",
    layout="centered"
)

st.title("🛡️ ARIA")
st.caption("Self-healing cybersecurity RAG assistant — runs fully local")

mode = st.radio(
    "Mode",
    options=["qa", "triage"],
    horizontal=True,
    format_func=lambda m: "Q&A" if m == "qa" else "SOC Triage"
)

placeholder = (
    "e.g. What is T1059 Command-Line Interface?"
    if mode == "qa"
    else "e.g. I'm seeing regsvr32.exe connect to an unfamiliar URL on a company laptop"
)

question = st.text_area(
    "Question / Observation",
    placeholder=placeholder,
    height=100
)

if st.button("Ask ARIA", type="primary"):

    if not question.strip():
        st.warning("Please enter a question or observation.")

    else:
        with st.spinner(
            "Thinking... (this can take 1-5+ minutes on local CPU inference)"
        ):

            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": question,
                        "mode": mode
                    },
                    timeout=1200     # UPDATED FROM 900 → 1200
                )

                response.raise_for_status()

                result = response.json()

                st.markdown("### Answer")
                st.write(result["answer"])

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Confidence",
                    f"{result['confidence']:.2f}"
                )

                col2.metric(
                    "Latency",
                    f"{result['latency_ms']/1000:.1f}s"
                )

                col3.metric(
                    "Passed",
                    "✅" if result["passed"] else "⚠️"
                )

                with st.expander("Detailed scores"):
                    st.json(result["scores"])

                if result["healing_triggered"]:
                    st.info(
                        f"Self-healing triggered: "
                        f"{result['healing_attempts']} attempt(s), "
                        f"strategies used: "
                        f"{', '.join(result['strategies_used'])}"
                    )
                else:
                    st.success(
                        "Passed on first attempt — no healing needed."
                    )

            except requests.exceptions.RequestException as e:
                st.error(
                    f"Could not reach ARIA backend: {e}"
                )