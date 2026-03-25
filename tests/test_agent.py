from datetime import date

from founder_prospecting.agent import FounderProspectingAgent
from founder_prospecting.models import SearchCriteria


def test_filters_excluded_industry_and_cfo():
    agent = FounderProspectingAgent(SearchCriteria())
    records = agent.run(
        [
            {
                "founder_name": "A",
                "founder_title": "CEO",
                "company_name": "KeepMe",
                "company_website": "https://example.com",
                "city": "Chicago",
                "state": "IL",
                "us_based_location": True,
                "employee_count": 50,
                "industry": "SaaS for operations",
                "business_model_classification": "SaaS",
                "revenue": 5,
                "latest_funding_round": "Series A",
                "latest_funding_date": "2025-05-01",
                "currently_raising": False,
                "cfo_listed": False,
                "source_urls": ["https://example.com"],
                "confidence_score": 0.8,
            },
            {
                "founder_name": "B",
                "founder_title": "CEO",
                "company_name": "DropMeRetail",
                "company_website": "https://example.org",
                "city": "Chicago",
                "state": "IL",
                "us_based_location": True,
                "employee_count": 30,
                "industry": "Retail analytics",
                "business_model_classification": "tech-enabled",
                "revenue": 4,
                "latest_funding_round": "Series A",
                "latest_funding_date": "2025-07-01",
                "currently_raising": False,
                "cfo_listed": False,
                "source_urls": ["https://example.org"],
                "confidence_score": 0.8,
            },
            {
                "founder_name": "C",
                "founder_title": "CEO",
                "company_name": "DropMeCFO",
                "company_website": "https://example.net",
                "city": "Chicago",
                "state": "IL",
                "us_based_location": True,
                "employee_count": 40,
                "industry": "SaaS",
                "business_model_classification": "SaaS",
                "revenue": 3,
                "latest_funding_round": "Series A",
                "latest_funding_date": "2025-07-01",
                "currently_raising": False,
                "cfo_listed": True,
                "source_urls": ["https://example.net"],
                "confidence_score": 0.8,
            },
        ]
    )
    assert [r.company_name for r in records] == ["KeepMe"]


def test_sorting_prefers_recent_funding_then_chicago():
    agent = FounderProspectingAgent(SearchCriteria())
    records = agent.run(
        [
            {
                "founder_name": "A",
                "founder_title": "CEO",
                "company_name": "USRecent",
                "company_website": "https://a.com",
                "city": "Austin",
                "state": "TX",
                "us_based_location": True,
                "employee_count": 50,
                "industry": "SaaS",
                "business_model_classification": "SaaS",
                "revenue": 5,
                "latest_funding_round": "Series A",
                "latest_funding_date": date.today().isoformat(),
                "currently_raising": False,
                "cfo_listed": False,
                "source_urls": ["https://a.com"],
                "confidence_score": 0.8,
            },
            {
                "founder_name": "B",
                "founder_title": "CEO",
                "company_name": "ChicagoOlder",
                "company_website": "https://b.com",
                "city": "Chicago",
                "state": "IL",
                "us_based_location": True,
                "employee_count": 50,
                "industry": "SaaS",
                "business_model_classification": "SaaS",
                "revenue": 5,
                "latest_funding_round": "Series A",
                "latest_funding_date": "2025-01-01",
                "currently_raising": False,
                "cfo_listed": False,
                "source_urls": ["https://b.com"],
                "confidence_score": 0.8,
            },
        ]
    )
    assert records[0].company_name == "USRecent"
