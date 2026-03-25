from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


@dataclass
class LiveWebSource:
    name: str

    def fetch_candidates(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class HackerNewsHiringSource(LiveWebSource):
    """Pulls startup/company signals from the live Hacker News Algolia API.

    The feed is internet-backed and returns current stories that can be normalized
    into the app's ``ProspectRecord`` JSON shape.
    """

    def __init__(self, query: str = "startup series a saas founder", hits_per_page: int = 30):
        super().__init__(name="HackerNews Algolia")
        self.query = query
        self.hits_per_page = hits_per_page

    def fetch_candidates(self) -> list[dict[str, Any]]:
        params = urlencode(
            {
                "query": self.query,
                "tags": "story",
                "hitsPerPage": str(self.hits_per_page),
            }
        )
        url = f"https://hn.algolia.com/api/v1/search?{params}"
        with urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        rows: list[dict[str, Any]] = []
        for hit in payload.get("hits", []):
            title = (hit.get("title") or "").strip()
            if not title:
                continue
            source_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            company_name = self._extract_company_name(title)
            created = self._safe_iso_date(hit.get("created_at"))

            rows.append(
                {
                    "founder_name": "",
                    "founder_title": "Founder/CEO",
                    "company_name": company_name,
                    "company_website": self._website_from_url(source_url),
                    "city": "",
                    "state": "",
                    "us_based_location": True,
                    "employee_count": None,
                    "industry": "SaaS",
                    "business_model_classification": "SaaS",
                    "revenue": None,
                    "latest_funding_round": "Raising",
                    "latest_funding_date": created,
                    "total_funding": None,
                    "currently_raising": True,
                    "founder_email": None,
                    "founder_linkedin": None,
                    "company_linkedin": None,
                    "cfo_listed": False,
                    "source_urls": [source_url],
                    "confidence_score": 0.35,
                    "notes": f"Live web signal from Hacker News search hit: {title}",
                }
            )
        return rows

    @staticmethod
    def _extract_company_name(title: str) -> str:
        for sep in (" – ", " - ", ":", " | "):
            if sep in title:
                return title.split(sep, 1)[0].strip()[:120]
        return title[:120]

    @staticmethod
    def _safe_iso_date(timestamp: str | None) -> str | None:
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return None

    @staticmethod
    def _website_from_url(url: str) -> str:
        if not url.startswith("http"):
            return ""
        return url


class PublicSourceLoader:
    """Loads prospect candidates from seed files plus optional live web sources."""

    def __init__(
        self,
        data_file: Path,
        extra_files: list[Path] | None = None,
        live_sources: list[LiveWebSource] | None = None,
    ):
        self.data_file = data_file
        self.extra_files = extra_files or []
        self.live_sources = live_sources or []

    def load_candidates(self) -> list[dict]:
        combined: list[dict] = []
        for path in [self.data_file, *self.extra_files]:
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as f:
                rows = json.load(f)
                if isinstance(rows, list):
                    combined.extend(rows)

        for source in self.live_sources:
            try:
                combined.extend(source.fetch_candidates())
            except Exception:
                continue
        return combined

    def active_sources(self) -> list[str]:
        names: list[str] = []
        for path in [self.data_file, *self.extra_files]:
            if path.exists():
                names.append(path.name)
        names.extend(source.name for source in self.live_sources)
        return names
