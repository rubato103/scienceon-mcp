# scienceon-mcp — 프로젝트 지침

> KISTI ScienceON OpenAPI 문헌 검색·메타데이터 수집기. 누구나 자기 API 키로 쓰는
> **공개 MCP 서버 + CLI**. API 호출 규격은 [docs/SCIENCEON_API_GUIDE.md](docs/SCIENCEON_API_GUIDE.md) 참조.

## 1. 목표
연구 초반 **자료수집 단계**에서 반복 재사용하는 도구. 논문·보고서 등 서지 메타데이터를
검색·수집해 후속 텍스트마이닝 입력 데이터를 안정적으로 생산한다.

## 2. 확정 결정사항
| 항목 | 결정 |
|------|------|
| 언어/런타임 | Python 3.10+ (개발 venv는 3.12) |
| 패키지 관리 | **uv** (pyproject + uv.lock). venv는 **클라우드 폴더 밖** `C:\Users\rubat\.venvs\scienceon-mcp` (`UV_PROJECT_ENVIRONMENT`) |
| 의존성 | mcp(FastMCP), requests, pycryptodome, openpyxl, python-dotenv, pyyaml |
| 인터페이스 | 공용 코어 + **MCP 서버(server.py)** + **CLI(cli.py)** |
| 수집 대상 | ARTI(논문)·REPORT(보고서) 우선, ATT/RESEARCHER/ORGAN 확장 가능 |
| 출력 | xlsx · csv · json · sqlite |
| 공개 | MIT. `.env`·`reference/`·`output/`·토큰캐시는 gitignore |

## 3. 구조
```
src/scienceon_mcp/
  config.py     # .env 로딩, 엔드포인트
  auth.py       # AES256 토큰 발급/캐시/갱신 (라이브 검증 완료)
  client.py     # 검색/상세/페이징/재시도/에러
  parser.py     # XML(.//record/item[@metaCode]) → 정규화
  models.py     # Record 스키마
  exporters.py  # xlsx/csv/json/sqlite
  server.py     # MCP 도구: scienceon_search/detail/export/status
  cli.py        # status/search/detail/collect
docs/           # API 가이드, 워크플로, 프롬프트
config/         # 검색 설정 템플릿
reference/      # KISTI 매뉴얼·공식 샘플(gitignore, 비공개)
```

## 4. 자격증명 (.env 또는 사용자 환경변수)
- 변수: `SCIENCEON_AUTH_KEY`(32자), `SCIENCEON_CLIENT_ID`, `SCIENCEON_MAC_ADDRESS`, `SCIENCEON_ACCOUNT_ID`
- 구독 티켓(계정별 상이): 예) ARTI·REPORT·ATT·RESEARCHER·ORGAN
- API Gateway **IP관리**에 호출 PC 공인 IP 등록·활성화 필수(미등록 시 E4006). MAC = 신청 시 등록한 대표 MAC.
- ⚠️ 인증키는 코드/로그/커밋 금지 — `.env`(gitignore) 또는 OS 사용자 환경변수로만.

## 5. 핵심 기술사실 (라이브 검증)
- **토큰 발급**: `tokenrequest.do?client_id=&accounts=` — accounts = urlsafe_b64( AES-256-CBC(
  key=인증키 UTF-8 32B, **IV=`jvHJ1EFA0IXBrxxz`(고정)**, PKCS7, 평문 `{"datetime":"YYYYMMDDHHMMSS","mac_address":"..."}`)) → URL 인코딩. (그 고정 IV는 공식 샘플로만 확인 가능했음)
- **데이터 호출**: `openapicall.do?...&action=search|browse&target=ARTI&searchQuery={"BI":"검색어"}&curPage=&rowCount=`
- **응답 XML**: 레코드 `.//record`, 필드 `<item metaCode="...">`. 총건수 `TotalCount`.
  ARTI metaCode: CN/Title/Author/Pubyear/Publisher/JournalName/Abstract/Keyword/DOI/ContentURL.
- Access Token 2시간, Refresh Token 2주. 429(Too Many Requests) 주의 → throttle·백오프 필수.

## 6. 개발 원칙
- 자격증명은 `.env`/MCP env 블록으로만. 로그·예외에 노출 금지.
- 정중한 호출: throttle(기본 0.5s), 지수 백오프, 페이지네이션 안전장치(새 레코드 0이면 종료).
- 원본 XML 필드는 `raw`로 보존. 커밋 메시지 한국어, Claude 서명 금지.
- 라이브 검증 우선(추정 금지) — 대량 호출 전 소량 시범.

## 7. 상태
- ✅ 토큰 발급·검색 라이브 검증 / 코어·MCP·CLI 구현 / 4종 익스포터
- ⏳ 라이브 수집 최종 검증 → git init·커밋 → (확인 후) GitHub 공개 푸시
