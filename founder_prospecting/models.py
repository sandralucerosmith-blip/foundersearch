from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

BusinessModel = Literal["tech-enabled", "SaaS", "professional services", "unknown"]
FitTier = Literal["High-fit", "Medium-fit", "Low-fit"]


@dataclass
class SearchCriteria:
    geography: list[str] = field(default_factory=lambda: ["Chicago", "United States"])
    employee_min: int = 10
    employee_max: int = 100
    funding_stages: list[str] = field(default_factory=lambda: ["Series A", "Series B", "Raising"])
    funding_recency_days: int = 365 * 2
    include_business_models: list[BusinessModel] = field(
        default_factory=lambda: ["tech-enabled", "SaaS", "professional services"]
    )
    revenue_cap_millions: float = 50.0
    exclude_keywords: list[str] = field(
        default_factory=lambda: ["manufacturing", "retail", "ecommerce", "hospitality", "restaurants"]
    )
    include_keywords: list[str] = field(default_factory=list)
    include_low_fit: bool = False


@dataclass
class ProspectRecord:
    founder_name: str
    founder_title: str
    company_name: str
    company_website: str
    city: str
    state: str
    us_based_location: bool
    employee_count: int | None
    industry: str
    business_model_classification: BusinessModel
    revenue: float | None
    latest_funding_round: str | None
    latest_funding_date: date | None
    total_funding: float | None
    currently_raising: bool | None
    founder_email: str | None
    founder_linkedin: str | None
    company_linkedin: str | None
    cfo_listed: bool
    source_urls: list[str]
    confidence_score: float
    notes: str = ""
    fit_tier: FitTier = "Medium-fit"

    def to_csv_dict(self) -> dict[str, str | int | float | bool | None]:
        return {
            "founder_name": self.founder_name,
            "founder_title": self.founder_title,
            "company_name": self.company_name,
            "company_website": self.company_website,
            "city": self.city,
            "state": self.state,
            "us_based_location": self.us_based_location,
            "employee_count": self.employee_count,
            "industry": self.industry,
            "business_model_classification": self.business_model_classification,
            "revenue": self.revenue,
            "latest_funding_round": self.latest_funding_round,
            "latest_funding_date": self.latest_funding_date.isoformat() if self.latest_funding_date else "",
            "total_funding": self.total_funding,
            "currently_raising": self.currently_raising,
            "founder_email": self.founder_email or "",
            "founder_linkedin": self.founder_linkedin or "",
            "company_linkedin": self.company_linkedin or "",
            "cfo_listed": self.cfo_listed,
            "source_urls": "; ".join(self.source_urls),
            "confidence_score": self.confidence_score,
            "notes": self.notes,
        }
