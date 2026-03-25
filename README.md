# Founder Prospecting Agent

A Streamlit-based agent for founder-led company prospecting tailored to fractional CFO / strategic finance services.

## What it does

- Applies a default search profile (Chicago first, then US; 10–100 employees; Series A/B or raising; revenue <= $50M).
- Screens out excluded industries and companies with CFO-equivalent top finance leadership.
- Produces reviewable table results in UI before export.
- Supports interactive filter refinement, approval workflow, and CSV export.
- Supports scheduled scans (daily/weekly mode selection) with new-vs-updated change detection.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## CSV columns

The export includes:

`founder_name, founder_title, company_name, company_website, city, state, us_based_location, employee_count, industry, business_model_classification, revenue, latest_funding_round, latest_funding_date, total_funding, currently_raising, founder_email, founder_linkedin, company_linkedin, cfo_listed, source_urls, confidence_score, notes`

## Notes

- Uses multi-source-ready architecture with `PublicSourceLoader`; replace with live connectors as needed.
- Does not guess missing facts and leaves unknown founder emails blank.
- Keeps source URLs for auditability.
