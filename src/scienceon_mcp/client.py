"""ScienceON OpenAPI 호출 클라이언트 — 검색/상세/페이징.

데이터 호출(라이브 검증):
  openapicall.do?client_id=&token=&version=1.0&action=search|browse
                &target=ARTI|REPORT|...&searchQuery={"필드":"검색어"}&curPage=&rowCount=
응답: XML (성공 시 resultSummary/statusCode=200, 레코드는 .//record/item[@metaCode]).
"""
from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET

import requests

from .auth import TokenManager
from .config import API_URL, Credentials
from .models import Record
from .parser import normalize, parse_response


class ScienceONError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


_HINTS = {
    "E4006": "토큰 발급용 MAC 추출 실패(암호화 오류). 인증키/암호화 스킴 확인.",
    "E4107": "accounts MAC 이 신청 MAC 과 불일치.",
    "E4103": "Access Token 만료/오류 — 재발급 필요.",
    "E4104": "신청정보가 승인상태가 아님.",
    "E4007": "searchField(검색필드) 값 오류.",
    "E4008": "target 값 오류.",
}


def _check_xml_error(text: str) -> None:
    if "errorCode" not in text and "errorDetail" not in text:
        return
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return
    sc = (root.findtext(".//statusCode") or "").strip()
    if sc and sc != "200":
        code = (root.findtext(".//errorCode") or sc).strip()
        msg = (root.findtext(".//errorMessage") or root.findtext(".//statusMessage") or "").strip()
        if code in _HINTS:
            msg = f"{msg} — {_HINTS[code]}"
        raise ScienceONError(code, msg)


class ScienceONClient:
    def __init__(self, creds: Credentials | None = None, *, throttle: float = 0.5,
                 timeout: int = 20, token_manager: TokenManager | None = None):
        self.creds = creds or Credentials.from_env()
        self.tokens = token_manager or TokenManager(self.creds)
        self.throttle = throttle
        self.timeout = timeout

    def _call(self, params: dict) -> str:
        base = {"client_id": self.creds.client_id,
                "token": self.tokens.get_access_token(), "version": "1.0"}
        base.update(params)
        for attempt in range(3):
            r = requests.get(API_URL, params=base, timeout=self.timeout)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(1.5 * (2 ** attempt))  # 지수 백오프
                continue
            break
        if r.status_code == 429:
            raise ScienceONError("429", "요청 한도 초과(Too Many Requests). throttle 상향 또는 잠시 후 재시도.")
        r.raise_for_status()
        _check_xml_error(r.text)
        return r.text

    def search_page(self, target: str, query, *, page: int = 1, rows: int = 20,
                    sort_field: str = "", include: str = "") -> tuple[int, list[Record], str]:
        q = query if isinstance(query, str) else json.dumps(query, ensure_ascii=False, separators=(",", ":"))
        params = {"action": "search", "target": target, "searchQuery": q,
                  "curPage": page, "rowCount": rows}
        if sort_field:
            params["sortField"] = sort_field
        if include:
            params["include"] = include
        text = self._call(params)
        total, raws = parse_response(text)
        return total, [normalize(r, target) for r in raws], text

    def search(self, target: str, query, *, max_records: int = 100, rows: int = 100,
               sort_field: str = "", include: str = "") -> list[Record]:
        """페이지네이션·중복제거 수집. 최대 max_records 건 반환."""
        out: list[Record] = []
        seen: set = set()
        page = 1
        while len(out) < max_records and page <= 1000:
            total, recs, _ = self.search_page(target, query, page=page, rows=rows,
                                               sort_field=sort_field, include=include)
            if not recs:
                break
            before = len(out)
            for r in recs:
                key = r.control_no or (r.title, r.pub_year)
                if key in seen:
                    continue
                seen.add(key)
                out.append(r)
            if len(out) == before:  # 이번 페이지에 새 레코드 없음 → 종료(끝/중복)
                break
            if total and page * rows >= total:
                break
            page += 1
            time.sleep(self.throttle)
        return out[:max_records]

    def detail(self, target: str, cn: str) -> Record | None:
        text = self._call({"action": "browse", "target": target, "cn": cn})
        _, raws = parse_response(text)
        return normalize(raws[0], target) if raws else None
