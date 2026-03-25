from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import json

from founder_prospecting.models import ProspectRecord, SearchCriteria

EXCLUDED_FINANCE_TITLES = {
    "cfo",
    "chief financial officer",
    "fractional cfo",
    "vp finance",
    "vp of finance",
    "head of finance",
    "finance director",
}

BUSINESS_PRIORITY = {
    "tech-enabled": 0,
    "SaaS": 1,
    "professional services": 2,
    "unknown": 3,
}


class FounderProspectingAgent:
    """Validation, ranking, and change-detection engine for founder prospecting."""

    def __init__(self, criteria: SearchCriteria):
        self.criteria = criteria

    def run(self, raw_records: list[dict]) -> list[ProspectRecord]:
        normalized = [self._normalize_record(raw) for raw in raw_records]
        accepted: list[ProspectRecord] = []
        for record in normalized:
            if self._passes_required_filters(record):
                record.fit_tier = self._assign_fit_tier(record)
                if record.fit_tier != "Low-fit" or self.criteria.include_low_fit:
                    accepted.append(record)
        return sorted(accepted, key=self._sort_key)

    def detect_updates(
        self, previous_records: list[ProspectRecord], latest_records: list[ProspectRecord]
    ) -> tuple[list[ProspectRecord], list[ProspectRecord]]:
        previous_map = {r.company_name: r for r in previous_records}
        new_matches: list[ProspectRecord] = []
        updated_matches: list[ProspectRecord] = []
        for latest in latest_records:
            old = previous_map.get(latest.company_name)
            if old is None:
                new_matches.append(latest)
                continue
            if self._changed(old, latest):
                updated_matches.append(latest)
        return new_matches, updated_matches

    def export_csv(self, records: list[ProspectRecord], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(records[0].to_csv_dict().keys()) if records else [
            "founder_name",
            "founder_title",
            "company_name",
            "company_website",
            "city",
            "state",
            "us_based_location",
            "employee_count",
            "industry",
            "business_model_classification",
            "revenue",
            "latest_funding_round",
            "latest_funding_date",
            "total_funding",
            "currently_raising",
            "founder_email",
            "founder_linkedin",
            "company_linkedin",
            "cfo_listed",
            "source_urls",
            "confidence_score",
            "notes",
        ]
        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record.to_csv_dict())

    def save_run_snapshot(self, records: list[ProspectRecord], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in records], f, default=str, indent=2)

    def load_run_snapshot(self, path: Path) -> list[ProspectRecord]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        records = []
        for row in data:
            if row.get("latest_funding_date"):
                row["latest_funding_date"] = datetime.fromisoformat(row["latest_funding_date"]).date()
            records.append(ProspectRecord(**row))
        return records

    def _normalize_record(self, raw: dict) -> ProspectRecord:
        funding_date = raw.get("latest_funding_date")
        if isinstance(funding_date, str) and funding_date:
            funding_date = datetime.fromisoformat(funding_date).date()
        return ProspectRecord(
            founder_name=raw.get("founder_name", ""),
            founder_title=raw.get("founder_title", ""),
            company_name=raw.get("company_name", ""),
            company_website=raw.get("company_website", ""),
            city=raw.get("city", ""),
            state=raw.get("state", ""),
            us_based_location=bool(raw.get("us_based_location", False)),
            employee_count=raw.get("employee_count"),
            industry=raw.get("industry", ""),
            business_model_classification=raw.get("business_model_classification", "unknown"),
            revenue=raw.get("revenue"),
            latest_funding_round=raw.get("latest_funding_round"),
            latest_funding_date=funding_date,
            total_funding=raw.get("total_funding"),
            currently_raising=raw.get("currently_raising"),
            founder_email=raw.get("founder_email"),
            founder_linkedin=raw.get("founder_linkedin"),
            company_linkedin=raw.get("company_linkedin"),
            cfo_listed=bool(raw.get("cfo_listed", False)),
            source_urls=raw.get("source_urls", []),
            confidence_score=float(raw.get("confidence_score", 0.0)),
            notes=raw.get("notes", ""),
            fit_tier=raw.get("fit_tier", "Medium-fit"),
        )

    def _passes_required_filters(self, r: ProspectRecord) -> bool:
        if not r.us_based_location:
            return False
        if r.employee_count is None:
            return False
        if not (self.criteria.employee_min <= r.employee_count <= self.criteria.employee_max):
            return False
        if r.business_model_classification not in self.criteria.include_business_models:
            return False
        if r.revenue is not None and r.revenue > self.criteria.revenue_cap_millions:
            return False
        if r.cfo_listed:
            return False
        low_industry = r.industry.lower()
        if any(keyword in low_industry for keyword in self.criteria.exclude_keywords):
            return False
        if self.criteria.include_keywords and not any(
            keyword.lower() in (r.industry + " " + r.notes).lower()
            for keyword in self.criteria.include_keywords
        ):
            return False

        is_allowed_funding = (
            (r.latest_funding_round in self.criteria.funding_stages)
            or (r.currently_raising is True and "Raising" in self.criteria.funding_stages)
        )
        if not is_allowed_funding:
            return False

        if r.latest_funding_date:
            recent_cutoff = date.today() - timedelta(days=self.criteria.funding_recency_days)
            if r.latest_funding_date < recent_cutoff and not r.currently_raising:
                return False
        return True

    def _assign_fit_tier(self, r: ProspectRecord) -> str:
        complete_core = all(
            [
                r.founder_name,
                r.company_name,
                r.employee_count is not None,
                r.business_model_classification in {"tech-enabled", "SaaS", "professional services"},
                r.us_based_location,
                not r.cfo_listed,
            ]
        )
        strong_funding = r.currently_raising or r.latest_funding_round in {"Series A", "Series B"}
        if complete_core and strong_funding and r.confidence_score >= 0.75:
            return "High-fit"
        if complete_core and r.confidence_score >= 0.5:
            return "Medium-fit"
        return "Low-fit"

    def _sort_key(self, r: ProspectRecord) -> tuple:
        recently_funded = r.latest_funding_date is not None
        chicago_first = 0 if "chicago" in r.city.lower() or r.state.upper() == "IL" else 1
        funding_date_sort = r.latest_funding_date.toordinal() if r.latest_funding_date else 0
        return (
            0 if recently_funded else 1,
            0 if r.currently_raising else 1,
            -funding_date_sort,
            BUSINESS_PRIORITY.get(r.business_model_classification, 3),
            chicago_first,
            -r.confidence_score,
            -len([v for v in r.to_csv_dict().values() if v not in (None, "")]),
        )

    @staticmethod
    def _changed(old: ProspectRecord, new: ProspectRecord) -> bool:
        return any(
            [
                old.latest_funding_round != new.latest_funding_round,
                old.latest_funding_date != new.latest_funding_date,
                old.total_funding != new.total_funding,
                old.currently_raising != new.currently_raising,
                old.cfo_listed != new.cfo_listed,
            ]
        )
