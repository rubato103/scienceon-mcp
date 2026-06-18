"""익스포터 단위 테스트 — 4종 형식 + sqlite 스냅샷."""
import json
import sqlite3

from scienceon_mcp.exporters import export
from scienceon_mcp.models import Record


def _recs():
    return [
        Record(source="ARTI", control_no="A1", title="제목1", authors=["저자A", "저자B"],
               pub_year="2024", keywords=["k1", "k2"], abstract="초록1", raw={"DBCode": "JAKO"}),
        Record(source="REPORT", control_no="R1", title="보고서1", pub_year="2023", raw={}),
    ]


def test_export_all_formats(tmp_path):
    paths = export(_recs(), ["xlsx", "csv", "json", "sqlite"], str(tmp_path), "smoke")
    assert len(paths) == 4
    # json
    data = json.loads((tmp_path / "smoke.json").read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["authors"] == "저자A; 저자B"  # 리스트는 구분자로 join
    # sqlite
    n = sqlite3.connect(str(tmp_path / "smoke.sqlite")).execute("select count(*) from records").fetchone()[0]
    assert n == 2


def test_sqlite_snapshot_no_accumulation(tmp_path):
    # 두 번 내보내도 누적되지 않고 스냅샷(N) 유지
    export(_recs(), ["sqlite"], str(tmp_path), "snap")
    export(_recs(), ["sqlite"], str(tmp_path), "snap")
    n = sqlite3.connect(str(tmp_path / "snap.sqlite")).execute("select count(*) from records").fetchone()[0]
    assert n == 2
