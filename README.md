# scienceon-mcp

KISTI **ScienceON OpenAPI** 문헌 검색·메타데이터 수집기 — **MCP 서버 + CLI**.
자기 ScienceON API 키만 발급받으면 누구나 Claude(또는 CLI)에서 국내외 논문·보고서
서지 메타데이터를 검색·수집할 수 있습니다.

> An MCP server + CLI for KISTI ScienceON OpenAPI. Bring your own API key and let
> Claude search & collect academic literature metadata in any project.

## 무엇을 할 수 있나

- 🔎 **검색**: 논문(ARTI)·보고서(REPORT) 등 서지 메타데이터 검색
- 📄 **상세**: 제어번호(CN)로 초록·서지 전체 조회
- 💾 **수집**: 결과를 **xlsx / csv / json / sqlite** 로 저장
- 🤖 **두 가지 사용법**: Claude에서 도구 호출(MCP) · 터미널 배치(CLI) — 같은 코어 공유

지원 티켓: `ARTI` 논문 · `REPORT` 보고서 · `ATT` 동향 · `RESEARCHER` 연구자 · `ORGAN` 연구기관
(계정 구독 범위에 따름)

## 요구사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (패키지 관리)
- ScienceON API 자격증명 (아래 발급 방법)

## 1) API 키 발급

1. [ScienceON](https://scienceon.kisti.re.kr) 회원가입·로그인
2. **API Gateway → 인증키 발급 신청** → 승인 후 `인증키`·`Client ID` 발급
3. **인증키관리**에서 신청 **MAC 주소** 등록, **IP관리**에서 호출 PC의 공인 IP 등록
4. 사용할 **서비스 콘텐츠(티켓)** 체크 (논문/보고서 등)

## 2) 설치 (uv, 클라우드 폴더 주의)

> 이 저장소가 OneDrive 등 **클라우드 동기화 폴더**에 있다면 venv를 폴더 **밖**에 두세요
> (동기화 충돌·파일락 방지). uv는 `UV_PROJECT_ENVIRONMENT` 로 환경 위치를 지정합니다.

```bash
# 예: venv 를 클라우드 밖 로컬 경로에 생성
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/scienceon-mcp"   # Windows(PowerShell): $env:UV_PROJECT_ENVIRONMENT="C:\Users\<you>\.venvs\scienceon-mcp"
uv sync
```

## 3) 자격증명 설정

`.env.example` 을 복사해 `.env` 작성 (커밋 금지):

```ini
SCIENCEON_AUTH_KEY=발급_32자리_인증키
SCIENCEON_CLIENT_ID=발급_client_id
SCIENCEON_MAC_ADDRESS=AA-BB-CC-DD-EE-FF
SCIENCEON_ACCOUNT_ID=신청자_아이디
```

## 4) Claude에 MCP 연결

**Claude Desktop** (`claude_desktop_config.json`) — 자격증명은 `env` 블록으로 전달:

```json
{
  "mcpServers": {
    "scienceon": {
      "command": "C:\\Users\\<you>\\.venvs\\scienceon-mcp\\Scripts\\python.exe",
      "args": ["-m", "scienceon_mcp.server"],
      "env": {
        "SCIENCEON_AUTH_KEY": "...",
        "SCIENCEON_CLIENT_ID": "...",
        "SCIENCEON_MAC_ADDRESS": "AA-BB-CC-DD-EE-FF"
      }
    }
  }
}
```

**Claude Code**:

```bash
claude mcp add scienceon -- "C:\Users\<you>\.venvs\scienceon-mcp\Scripts\python.exe" -m scienceon_mcp.server
```

연결되면 Claude에서 `scienceon_search`, `scienceon_detail`, `scienceon_export`,
`scienceon_status` 도구를 사용할 수 있습니다.

## 5) CLI 사용 (배치·재현)

```bash
uv run scienceon status                                   # 토큰/연결 확인
uv run scienceon search --target ARTI --query "인공지능" --year 2015-2024 --rows 100
uv run scienceon collect --config config/search.example.yaml   # 설정 기반 대량 수집
```

## 문서

- [docs/SCIENCEON_API_GUIDE.md](docs/SCIENCEON_API_GUIDE.md) — API 호출 규격 레퍼런스
- [docs/COLLECTION_WORKFLOW.md](docs/COLLECTION_WORKFLOW.md) — 반복 수집 SOP
- [docs/PROMPTS.md](docs/PROMPTS.md) — Claude 구동용 프롬프트 템플릿

## 보안

- 자격증명은 **`.env` 또는 MCP `env` 블록**으로만 전달 — 코드/커밋/로그에 넣지 마세요.
- `.env`, 토큰 캐시는 `.gitignore` 로 제외됩니다.

## 라이선스

MIT © Yeondong Yang. 본 프로젝트는 KISTI의 비공식 클라이언트이며 KISTI와 제휴 관계가 없습니다.
ScienceON 데이터 이용은 KISTI 약관·트래픽 정책을 따릅니다.
