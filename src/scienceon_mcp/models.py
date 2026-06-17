"""정규화된 메타데이터 스키마."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 표 출력(csv/xlsx/sqlite) 시 컬럼 순서
COLUMNS = [
    "source", "control_no", "title", "authors", "pub_year",
    "publisher", "journal", "abstract", "keywords", "doi", "url",
]


@dataclass
class Record:
    """소스(ARTI/REPORT 등) 공통 정규화 레코드."""

    source: str
    control_no: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    pub_year: str = ""
    publisher: str = ""
    journal: str = ""
    abstract: str = ""
    keywords: list[str] = field(default_factory=list)
    doi: str = ""
    url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)  # 원본 필드 보존

    def to_row(self, *, list_sep: str = "; ") -> dict[str, Any]:
        """평탄화된 표 한 행(dict). 리스트 필드는 구분자로 join."""
        row: dict[str, Any] = {}
        for col in COLUMNS:
            val = getattr(self, col)
            row[col] = list_sep.join(val) if isinstance(val, list) else val
        return row
