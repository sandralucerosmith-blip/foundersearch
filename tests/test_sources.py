from pathlib import Path
import json

from founder_prospecting.sources import HackerNewsHiringSource, PublicSourceLoader


class StubLiveSource:
    name = "Stub Feed"

    def fetch_candidates(self):
        return [{"company_name": "LiveWebCo"}]


class FailingLiveSource:
    name = "Failing Feed"

    def fetch_candidates(self):
        raise RuntimeError("upstream unavailable")


def test_loader_merges_seed_and_extra_files(tmp_path: Path):
    seed = tmp_path / "seed.json"
    extra = tmp_path / "extra.json"
    seed.write_text(json.dumps([{"company_name": "SeedCo"}]), encoding="utf-8")
    extra.write_text(json.dumps([{"company_name": "LiveCo"}]), encoding="utf-8")

    loader = PublicSourceLoader(seed, extra_files=[extra])

    rows = loader.load_candidates()

    assert [r["company_name"] for r in rows] == ["SeedCo", "LiveCo"]
    assert loader.active_sources() == ["seed.json", "extra.json"]


def test_loader_merges_live_sources(tmp_path: Path):
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps([{"company_name": "SeedCo"}]), encoding="utf-8")

    loader = PublicSourceLoader(seed, live_sources=[StubLiveSource()])

    rows = loader.load_candidates()

    assert [r["company_name"] for r in rows] == ["SeedCo", "LiveWebCo"]
    assert loader.active_sources() == ["seed.json", "Stub Feed"]


def test_loader_skips_missing_extra_files_and_failed_live_source(tmp_path: Path):
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps([{"company_name": "SeedCo"}]), encoding="utf-8")

    loader = PublicSourceLoader(
        seed,
        extra_files=[tmp_path / "missing.json"],
        live_sources=[FailingLiveSource()],
    )

    rows = loader.load_candidates()

    assert [r["company_name"] for r in rows] == ["SeedCo"]
    assert loader.active_sources() == ["seed.json", "Failing Feed"]


def test_hackernews_source_maps_api_hits(monkeypatch):
    payload = {
        "hits": [
            {
                "title": "AcmeAI - Raising seed extension",
                "url": "https://acme.example",
                "objectID": "123",
                "created_at": "2026-03-01T10:00:00Z",
            }
        ]
    }

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr("founder_prospecting.sources.urlopen", lambda *args, **kwargs: DummyResponse())

    source = HackerNewsHiringSource(query="acme", hits_per_page=1)
    rows = source.fetch_candidates()

    assert rows[0]["company_name"] == "AcmeAI"
    assert rows[0]["latest_funding_round"] == "Raising"
    assert rows[0]["currently_raising"] is True
    assert rows[0]["source_urls"] == ["https://acme.example"]
    assert rows[0]["latest_funding_date"] == "2026-03-01"
