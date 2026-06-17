# ScienceON API 개발 가이드

> KISTI ScienceON API Gateway 호출 규격 레퍼런스. 구현·디버깅 시 이 문서를 참조한다.
> 표기: ✅ 확인됨 / ⚠️ 발급 후 공식 명세로 확정 필요.
>
> **권위 있는 출처(로그인 상태에서 열람)** — 정확한 파라미터·필드·샘플코드는 항상 아래에서 대조:
> - 토큰 발급(Java 샘플 포함): `…/apigateway/api/way/guide/tokenGuide.do`
> - 논문 검색: `…/apigateway/api/way/service/arti/serviceArtiSearchApi.do`
> - 논문 상세: `…/apigateway/api/way/service/arti/serviceArtiBrowseApi.do`
> - 보고서 검색/상세: `…/apigateway/api/way/service/report/serviceReportSearchApi.do`, `serviceReportBrowseApi.do`
> - 오류코드: `…/apigateway/api/way/guide/errorCodeGuide.do`
> (도메인: `https://scienceon.kisti.re.kr`)

---

## 1. 자격증명 (발급 완료)

| 항목 | 용도 | 저장 위치 |
|------|------|-----------|
| 인증키 (32자) | AES-256 **암호화 키** | `.env` `SCIENCEON_AUTH_KEY` |
| Client ID (64자) | 토큰/호출 식별자 | `.env` `SCIENCEON_CLIENT_ID` |
| MAC 주소 | 토큰 발급 페이로드 | `.env` `SCIENCEON_MAC_ADDRESS` |
| 신청자 아이디 | 계정 식별(참고) | `.env` `SCIENCEON_ACCOUNT_ID` |

- **IP관리 탭 주의**: 게이트웨이는 등록 IP/MAC 기반 접근제어를 함께 둘 수 있다.
  호출 서버의 공인 IP가 포털 `IP관리`에 등록돼 있어야 하며, MAC은 발급 시
  신청 시 등록한 대표 MAC 과 일치해야 한다(클라우드/노트북 이동 시 깨질 수 있음).
- 인증키는 코드/로그/예외 메시지에 절대 노출하지 않는다.

---

## 2. 인증 흐름 (3단계)

```
[1] 인증키로 AES256 암호화 → 토큰 요청  →  access_token / refresh_token 수령
[2] access_token 으로 데이터 호출(검색/상세)
[3] 만료 시 refresh_token 으로 재발급
```

### 2.1 토큰 발급  ✅구조 / ⚠️AES세부

**엔드포인트**
```
GET https://apigateway.kisti.re.kr/tokenrequest.do
    ?accounts=<URLEncode( AES256( JSON ) )>
    &client_id=<CLIENT_ID>
```

**평문 JSON 페이로드**
```json
{ "datetime": "20260617120000", "mac_address": "AA-BB-CC-DD-EE-FF" }
```
- `datetime` 형식: `yyyyMMddHHmmss` (요청 시각, 서버와 시차 과도 시 거부될 수 있음)
- 위 JSON을 **인증키(32바이트)로 AES-256 암호화 → Base64 → URL 인코딩** 하여 `accounts` 에 전달.

> ⚠️ **AES 모드/IV/패딩은 반드시 공식 `tokenGuide.do` 의 Java 샘플과 일치시킬 것.**
> KISTI 계열에서 통용되는 기본형은 `AES/CBC/PKCS5Padding`, key=인증키(UTF-8 32byte),
> IV=인증키 앞 16byte 이지만, 모드(ECB/CBC)·IV 규칙이 서비스마다 다를 수 있어
> **최초 1회 샘플코드로 검증**이 필요하다. (아래 §6 참조구현은 이 기본형 가정)

**응답(JSON)** ✅
```json
{
  "access_token": "...",      "access_token_expire": "YYYY-MM-DD HH:mm:ss",
  "refresh_token": "...",     "refresh_token_expire": "YYYY-MM-DD HH:mm:ss",
  "client_id": "...",         "issued_at": "..."
}
```
- 운영 전략: 토큰을 디스크에 캐시(`.token_cache.json`, gitignore)하고 만료 1~2분 전이면 재발급.

### 2.2 토큰 갱신  ⚠️
- `refresh_token` 으로 동일/유사 엔드포인트에서 재발급(정확한 파라미터명은 가이드 확인).
- `refresh_token` 도 만료되면 §2.1 부터 다시 수행.

---

## 3. 데이터 호출 (검색)

**엔드포인트** ⚠️(명세로 확정)
```
GET https://apigateway.kisti.re.kr/openapicall.do
```

**공통 파라미터** (정확한 키/대소문자는 명세 대조)

| 파라미터 | 값/예 | 설명 |
|----------|-------|------|
| `client_id` | 발급값 | 식별자 |
| `token` | access_token | 인증 토큰 |
| `version` | `1.0` | API 버전 ⚠️ |
| `action` | `search` \| `browse` | 검색 / 상세보기 |
| `target` | `ARTI` \| `REPORT` | 콘텐츠 티켓(§5) |
| `searchQuery` | JSON 문자열(URL인코딩) | 질의(§4) |
| `curPage` | `1` | 페이지 번호 |
| `rowCount` | `10` (최대값 ⚠️명세) | 페이지당 건수 |
| `sortField` / `sortOrder` | 예: `PY` / `DESC` | 정렬 ⚠️ |

- 응답 형식: **XML** ✅ (인코딩 UTF-8).

---

## 4. searchQuery 문법

`searchQuery` 는 **필드코드:값 의 JSON 문자열**을 URL 인코딩하여 전달한다.

```
# 예: 제목에 "인공지능" 포함
searchQuery = URLEncode( {"TI":"인공지능"} )

# 예: 전체 필드 + 발행연도 범위 (다중 조건)  ⚠️연산자 표기는 명세 확인
searchQuery = URLEncode( {"BI":"학습부진", "PY":"2015-2024"} )
```

**ARTI 주요 검색 필드코드** ⚠️(명세의 “검색필드” 표로 확정)

| 코드 | 의미 | 코드 | 의미 |
|------|------|------|------|
| `BI` | 전체(통합) | `AB` | 초록 |
| `TI` | 논문명 | `KW` | 키워드 |
| `AU` | 저자 | `PB` | 발행기관/출판사 |
| `PY` | 발행연도 | `JN` | 저널명 |

> 보고서(REPORT)는 검색 필드코드가 일부 다르다(과제번호·수행기관 등).
> `serviceReportSearchApi.do` 의 필드표를 그대로 옮겨 본 문서를 갱신할 것.

---

## 5. 콘텐츠 티켓 (구독 현황)

| 서비스 | 티켓 | 구독 | 설명 |
|--------|------|:---:|------|
| 논문 | `ARTI` | ✅ | 국내외 학술지·학술회의·국내학위·저널/프로시딩 서지 |
| 보고서 | `REPORT` | ✅ | 국가연구개발보고서, 각종 분석리포트 |
| 동향 | `ATT` | ✅ | 해외 과기동향, 정책동향, 글로벌동향 |
| 연구자 | `RESEARCHER` | ✅ | 식별 연구자의 논문/보고서/특허 목록 |
| 연구기관 | `ORGAN` | ✅ | 식별 기관의 논문/보고서/특허 목록 |
| 특허 | `PATENT` | ❌ | 미구독 |
| 과학향기 | `SCENT` | ❌ | 미구독 |
| ScienceON Trend | `TREND` | ❌ | 미구독 |
| 과기뉴스 | `SNEWS` | ❌ | 미구독 |

- **본 프로젝트 1차 수집 대상**: `ARTI`, `REPORT`.
- 확장 여지: `ATT`(동향 분석), `RESEARCHER`/`ORGAN`(저자·기관 단위 수집).

---

## 6. 상세보기 (Browse)

검색 결과의 **제어번호(CN)** 로 단건 상세를 조회한다. ⚠️파라미터명 명세 확인.
```
GET https://apigateway.kisti.re.kr/openapicall.do
    ?...&action=browse&target=ARTI&cn=<CONTROL_NO>
```
- 검색 응답에는 요약 메타가, 상세 응답에는 초록·서지 전체가 담기는 경우가 많다.
- 초록까지 필요하면 검색→CN 수집→상세 호출 2단계 파이프라인을 구성.

---

## 7. 응답(XML) 파싱

```xml
<root>
  <recordCount>...</recordCount>
  <recordList>
    <record>
      <item metaCode="...">값</item>   <!-- 필드는 metaCode/태그명으로 식별 ⚠️ -->
      ...
    </record>
  </recordList>
</root>
```
- 실제 태그/metaCode 명은 서비스별로 다르므로 **첫 응답을 저장해 스키마를 고정**한 뒤
  정규화 매핑표(아래)를 본 문서에 채운다.

**정규화 목표 ↔ 원본 필드 매핑** (수집 후 확정)

| 정규화 필드 | ARTI 원본 | REPORT 원본 |
|-------------|-----------|-------------|
| control_no | (CN) ⚠️ | (CN) ⚠️ |
| title | | |
| authors | | |
| pub_year | | |
| publisher / journal | | |
| abstract | | |
| keywords | | |
| doi / url | | |

---

## 8. 오류 처리

- 인증 실패(토큰 만료/IP·MAC 불일치), 파라미터 오류, 한도 초과 등 코드별 분기.
- 정확한 코드표는 `errorCodeGuide.do` 참조 → 본 문서에 표로 옮겨 관리.
- 재시도 정책: 5xx·네트워크 오류는 지수 백오프(예: 1→2→4초, 최대 3회).
  4xx 인증/파라미터 오류는 재시도 대신 즉시 중단·로그.

---

## 9. 운영 주의 (대량 수집)

- 트래픽 한도는 **제공기관 정책**에 따른다 → 대량 수집 전 helpdesk(080-969-4114,
  helpdesk@kisti.re.kr) 확인.
- 호출 간 **throttle(예: 0.3~1초)**, 동시성 제한(1~2)으로 정중하게 호출.
- 페이지네이션은 `recordCount` 로 총건수 파악 후 `curPage` 순회, 중복 키(CN) 제거.
- 응답 원본 XML을 `raw` 로 함께 저장해 재처리/감사 가능하게 한다.

---

## 10. Python 참조 구현 — 토큰 발급 (스켈레톤)

> ⚠️ AES 모드/IV는 §2.1 경고대로 공식 샘플과 대조 후 확정. `pycryptodome` 사용.

```python
import os, json, base64, datetime, urllib.parse, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

TOKEN_URL = "https://apigateway.kisti.re.kr/tokenrequest.do"

def _encrypt_accounts(auth_key: str, mac: str) -> str:
    key = auth_key.encode("utf-8")          # 32 bytes → AES-256
    iv  = key[:16]                          # ⚠️ 공식 샘플로 확정
    payload = json.dumps({
        "mac_address": mac,
        "datetime": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    }).encode("utf-8")
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, AES.block_size))
    return urllib.parse.quote(base64.b64encode(ct).decode("ascii"))

def request_token() -> dict:
    accounts = _encrypt_accounts(os.environ["SCIENCEON_AUTH_KEY"],
                                 os.environ["SCIENCEON_MAC_ADDRESS"])
    r = requests.get(TOKEN_URL, params={
        "accounts": accounts,
        "client_id": os.environ["SCIENCEON_CLIENT_ID"],
    }, timeout=15)
    r.raise_for_status()
    return r.json()   # access_token / refresh_token / *_expire ...
```

---

## 변경 이력
- 발급 직후 작성. §2.1 AES 세부, §3 엔드포인트/파라미터, §7 필드 매핑은
  **첫 실호출 검증 후 ⚠️ 표시를 제거**하며 확정한다.
