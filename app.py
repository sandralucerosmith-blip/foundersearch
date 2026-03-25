from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
import json

import pandas as pd
import streamlit as st

from founder_prospecting.agent import FounderProspectingAgent
from founder_prospecting.models import SearchCriteria
from founder_prospecting.sources import PublicSourceLoader

DATA_PATH = Path("data/sample_public_records.json")
STATE_PATH = Path("data/last_run_snapshot.json")
CRITERIA_PATH = Path("data/last_criteria.json")

st.set_page_config(page_title="Founder Prospecting Agent", layout="wide")
st.title("Founder Prospecting & Lead Generation Agent")

st.caption(
    "Default profile: Chicago first, then US; 10–100 employees; Series A/B or raising; "
    "tech-enabled/SaaS/professional services; no CFO-equivalent on team; revenue <= $50M"
)

with st.sidebar:
    st.header("Search Filters")
    geography_input = st.text_input("Geography (comma-separated)", "Chicago, United States")
    employee_range = st.slider("Employee range", min_value=1, max_value=500, value=(10, 100))
    funding_stage = st.multiselect(
        "Funding stage",
        options=["Series A", "Series B", "Raising"],
        default=["Series A", "Series B", "Raising"],
    )
    funding_recency = st.slider("Funding recency (days)", min_value=30, max_value=3650, value=730)
    business_models = st.multiselect(
        "Business models",
        options=["tech-enabled", "SaaS", "professional services"],
        default=["tech-enabled", "SaaS", "professional services"],
    )
    revenue_cap = st.number_input("Revenue cap ($M)", min_value=1.0, max_value=500.0, value=50.0)
    exclude_keywords_input = st.text_input(
        "Exclusion keywords (comma-separated)",
        "manufacturing, retail, ecommerce, hospitality, restaurants",
    )
    include_keywords_input = st.text_input("Inclusion keywords (comma-separated)", "")
    include_low_fit = st.checkbox("Include low-fit matches", value=False)

criteria = SearchCriteria(
    geography=[g.strip() for g in geography_input.split(",") if g.strip()],
    employee_min=employee_range[0],
    employee_max=employee_range[1],
    funding_stages=funding_stage,
    funding_recency_days=funding_recency,
    include_business_models=business_models,
    revenue_cap_millions=float(revenue_cap),
    exclude_keywords=[k.strip().lower() for k in exclude_keywords_input.split(",") if k.strip()],
    include_keywords=[k.strip().lower() for k in include_keywords_input.split(",") if k.strip()],
    include_low_fit=include_low_fit,
)

agent = FounderProspectingAgent(criteria)
loader = PublicSourceLoader(DATA_PATH)

if st.button("Run Initial Scan", type="primary"):
    raw = loader.load_candidates()
    records = agent.run(raw)
    st.session_state["records"] = records

if "records" in st.session_state:
    records = st.session_state["records"]
    frame = pd.DataFrame([r.to_csv_dict() | {"fit_tier": r.fit_tier} for r in records])

    st.subheader("Review Results")
    st.dataframe(frame, use_container_width=True)

    approved_company_names = st.multiselect(
        "Approve companies for export",
        options=frame["company_name"].tolist(),
        default=frame["company_name"].tolist(),
    )

    approved_records = [r for r in records if r.company_name in approved_company_names]

    if st.button("Export Approved to CSV"):
        output_path = Path("data/approved_export.csv")
        agent.export_csv(approved_records, output_path)
        csv_bytes = output_path.read_bytes()
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name=f"founder_prospects_{date.today().isoformat()}.csv",
            mime="text/csv",
        )

    st.subheader("Scheduled Scans")
    schedule_mode = st.selectbox("Schedule cadence", options=["Daily", "Weekly"])
    if st.button("Run Scheduled Scan"):
        latest = agent.run(loader.load_candidates())
        previous = agent.load_run_snapshot(STATE_PATH)
        new_matches, updated_matches = agent.detect_updates(previous, latest)

        st.write(f"Cadence: **{schedule_mode}**")
        st.write(f"New matches: **{len(new_matches)}**")
        st.write(f"Updated matches: **{len(updated_matches)}**")

        export_choice = st.radio(
            "Export set",
            options=["New results", "Updated results", "Full results set"],
            horizontal=True,
        )
        if export_choice == "New results":
            export_records = new_matches
        elif export_choice == "Updated results":
            export_records = updated_matches
        else:
            export_records = latest

        out_path = Path("data/scheduled_export.csv")
        agent.export_csv(export_records, out_path)
        st.success(f"Export ready ({len(export_records)} records)")

        agent.save_run_snapshot(latest, STATE_PATH)
        with CRITERIA_PATH.open("w", encoding="utf-8") as f:
            json.dump(asdict(criteria), f, indent=2)

st.markdown("---")
st.caption(
    "Notes: uses public-source candidate inputs, explicitly excludes CFO-equivalent leadership titles, "
    "and leaves founder_email blank when unavailable instead of guessing."
)
