"""ScienceON MCP 서버 (FastMCP).

Claude 등 MCP 클라이언트에 검색/상세/수집 도구를 노출한다.
자격증명은 MCP 설정의 env 블록 또는 .env 에서 로드한다.
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ScienceONClient, ScienceONError

mcp = FastMCP("scienceon")

# 검색 필드코드: BI(전체) TI(제목) AB(초록) AU(저자) KW(키워드) PB(발행기관) PY(발행연도)


def _client() -> ScienceONClient:
    return ScienceONClient()


def _build_query(query: str, field: str, year_from: int | None, year_to: int | None) -> dict:
    q = {field: query}
    if year_from and year_to:
        q["PY"] = f"{year_from}-{year_to}"
    elif year_from:
        q["PY"] = str(year_from)
    return q


@mcp.tool()
def scienceon_status() -> dict:
    """ScienceON 연결/토큰 상태 점검. 실패 시 원인 힌트와 현재 공인 IP 를 반환."""
    info: dict[str, Any] = {}
    try:
        import requests
        info["public_ip"] = requests.get("https://api.ipify.org", timeout=8).text
    except Exception:
        info["public_ip"] = "unknown"
    try:
        from .auth import TokenManager
        tok = TokenManager().get_access_token(force=True)
        info.update(ok=True, message="토큰 발급 성공", access_token_preview=tok[:8] + "…")
    except Exception as e:
        info.update(ok=False, error=str(e),
                    hint="E4006/IP 오류면 API Gateway IP관리에 위 public_ip 등록·활성화 필요.")
    return info


@mcp.tool()
def scienceon_search(query: str, target: str = "ARTI", field: str = "BI",
                     year_from: int | None = None, year_to: int | None = None,
                     rows: int = 20) -> dict:
    """ScienceON 문헌 검색.

    query: 검색어 / target: ARTI(논문)·REPORT(보고서)·ATT(동향)·RESEARCHER·ORGAN
    field: 검색필드 BI(전체)·TI(제목)·AB(초록)·AU(저자)·KW(키워드)
    year_from~year_to: 발행연도 범위. rows: 반환 건수(최대 100).
    """
    try:
        recs = _client().search(target, _build_query(query, field, year_from, year_to),
                                 max_records=min(rows, 100), rows=min(rows, 100))
    except ScienceONError as e:
        return {"error": str(e)}
    return {"count": len(recs), "records": [r.to_row() for r in recs]}


@mcp.tool()
def scienceon_detail(control_no: str, target: str = "ARTI") -> dict:
    """제어번호(CN)로 상세 서지·초록 조회."""
    try:
        r = _client().detail(target, control_no)
    except ScienceONError as e:
        return {"error": str(e)}
    return r.to_row() if r else {"error": "결과 없음"}


@mcp.tool()
def scienceon_export(query: str, target: str = "ARTI", field: str = "BI",
                     year_from: int | None = None, year_to: int | None = None,
                     formats: list[str] | None = None, max_records: int = 200,
                     out_dir: str = "output", name: str | None = None) -> dict:
    """검색 결과를 대량 수집해 파일로 저장(xlsx/csv/json/sqlite). 저장 경로 반환."""
    from .exporters import export
    try:
        recs = _client().search(target, _build_query(query, field, year_from, year_to),
                                 max_records=max_records, rows=100)
    except ScienceONError as e:
        return {"error": str(e)}
    fmts = formats or ["xlsx", "csv", "json"]
    nm = (name or f"{target}_{query}").replace(" ", "_")[:60]
    paths = export(recs, fmts, out_dir, nm)
    return {"count": len(recs), "files": paths}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
