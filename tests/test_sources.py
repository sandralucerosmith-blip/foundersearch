from pathlib import Path
import json

from founder_prospecting.sources import PublicSourceLoader


def test_loader_merges_seed_and_extra_files(tmp_path: Path):
    seed = tmp_path / "seed.json"
    extra = tmp_path / "extra.json"
    seed.write_text(json.dumps([{"company_name": "SeedCo"}]), encoding="utf-8")
    extra.write_text(json.dumps([{"company_name": "LiveCo"}]), encoding="utf-8")

    loader = PublicSourceLoader(seed, extra_files=[extra])

    rows = loader.load_candidates()

    assert [r["company_name"] for r in rows] == ["SeedCo", "LiveCo"]
    assert loader.active_sources() == ["seed.json", "extra.json"]


def test_loader_skips_missing_extra_files(tmp_path: Path):
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps([{"company_name": "SeedCo"}]), encoding="utf-8")

    loader = PublicSourceLoader(seed, extra_files=[tmp_path / "missing.json"])

    rows = loader.load_candidates()

    assert [r["company_name"] for r in rows] == ["SeedCo"]
    assert loader.active_sources() == ["seed.json"]
