# Bithumb Agent

Bithumb Agent는 [Hermes Agent](https://github.com/NousResearch/hermes-agent)의 MIT 오픈소스 코어와 Google Antigravity에서 영감을 받은 CLI 경험을 빗썸 업무 환경에 맞게 커스터마이징한 로컬 코딩 에이전트입니다.

> 오픈소스를 빗썸에 맞게 바꾼 것입니다. 문의: `ilhong.kim@bithumbcorp.com`

이 프로젝트는 빗썸의 공식 제품 또는 공식 배포판이 아닌 독립적인 오픈소스 커스터마이징입니다. 빗썸 및 관련 상표는 각 권리자에게 귀속됩니다.

## 요구 사항

- macOS 또는 Linux
- Python 3.11 이상 (Python 3.14 포함)
- Git
- ChatGPT/Codex OAuth 또는 Google Antigravity CLI OAuth

## GitHub에서 pip로 설치

가상환경 사용을 권장합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "git+https://github.com/realmi-lab/bithumb-agent.git@v0.19.0.post10"
```

설치 후 실행합니다.

```bash
bithumb-agent
```

## 인증과 모델 선택

최초 실행 화면에서 아래 둘 중 하나를 입력하면 로그인 창이 열립니다.

```text
/bit gpt
/bit gemini
```

- `/bit gpt`: 기존 Bithumb Agent 또는 공식 Codex 로그인을 먼저 재사용하고,
  없으면 ChatGPT/Codex OAuth 페이지를 기본 브라우저에서 엽니다. 공식 Codex
  CLI를 별도로 설치하지 않아도 되며, 로그인한 ChatGPT 계정에 Codex 사용
  권한이 있어야 합니다. SSH·헤드리스 환경에서는 Device Code 방식으로
  자동 전환합니다.
- `/bit gemini`: 공식 Google Antigravity CLI를 열어 Google OAuth 로그인을 진행합니다.
- `/bit status`: 두 로그인 상태를 확인합니다.

기존 셸 명령도 그대로 사용할 수 있습니다.

```bash
bithumb-agent auth status openai-codex
bithumb-agent auth status antigravity-cli
bithumb-agent model --provider openai-codex
bithumb-agent model --provider antigravity-cli
```

- `openai-codex`: ChatGPT/Codex OAuth
- `antigravity-cli`: Google OAuth를 사용하는 Gemini/Antigravity CLI
- `auto`: 인증된 두 공급자 중 하나를 자동 선택

API 키 또는 임의의 외부 추론 엔드포인트는 받지 않도록 제한되어 있습니다.

## 내장 코딩 스킬

LLM이 디버깅, 테스트, 계획, 단순화, 코드 리뷰, 기술 검증 작업을 더
일관되게 수행하도록 다음 여섯 개 방법론 문서를 읽기 전용으로 포함합니다.

- `systematic-debugging`
- `test-driven-development`
- `plan`
- `simplify-code`
- `requesting-code-review`
- `spike`

대화 중 모델은 관련 작업에 맞는 문서를 `skills_list`와 `skill_view`로 읽을
수 있습니다. 사용자가 직접 확인할 때는 다음 명령을 사용합니다.

```text
/skills
/skills view systematic-debugging
```

이 카탈로그는 wheel 내부에 고정되어 있습니다. 외부 디렉터리를 스캔하거나
스킬을 검색·설치·추가·수정하지 않으며, 비밀키 수집이나 셸 전처리 기능도
포함하지 않습니다.

## 업데이트와 삭제

```bash
python -m pip install --upgrade "git+https://github.com/realmi-lab/bithumb-agent.git"
python -m pip uninstall bithumb-agent
```

## 소스에서 개발 설치

```bash
git clone https://github.com/realmi-lab/bithumb-agent.git
cd bithumb-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
bithumb-agent
```

`requirements.txt`는 일반 실행에 필요한 직접 의존성을 담고 있으며
`pyproject.toml`의 핵심 의존성 목록과 테스트로 동기화됩니다. 일반적인
Git/PyPI 설치에서는 pip가 `pyproject.toml`을 읽으므로 별도로 실행할 필요가
없습니다.

## 보안 범위

외부 에이전트 도구는 터미널/프로세스 관리, 파일 읽기·쓰기·패치·검색,
로컬 코드 실행, 작업 계획·확인, 그리고 위 여섯 개 읽기 전용 코딩 스킬
조회로 제한됩니다. 플러그인, MCP 서버, 브라우저/웹 도구, 미디어 생성,
TTS, 장기 메모리, 위임, cron, 컴퓨터 제어, 메시징 도구, 동적 스킬,
셸 훅 및 승인 우회 모드는 비활성화됩니다. 관련 CLI 명령은 상위 런타임을
불러오기 전에 거부됩니다.

기업 또는 금융권 검토 전에는 [SECURITY_REVIEW.md](SECURITY_REVIEW.md)를 확인하세요. 저장소에는 비활성화된 Hermes 상류 구현 일부가 남아 있으며, 외부 `agy` 바이너리의 기능은 물리적으로 제거하는 대신 런타임에서 제한합니다.

## 오픈소스 출처와 변경 내역

Bithumb Agent는 Nous Research의 Hermes Agent를 기반으로 만든 수정 배포판입니다.
원 프로젝트의 MIT 라이선스 전문과 `Copyright (c) 2025 Nous Research`
고지를 삭제하거나 Bithumb 명의로 대체하지 않고 그대로 유지합니다. 빗썸용
수정 부분도 동일한 MIT 라이선스로 배포합니다.

Hermes Agent에서 Bithumb Agent로 변경한 내용은 다음과 같습니다.

- 배포 패키지와 실행 명령을 `bithumb-agent`로 변경
- 오렌지 CLI·초기 화면·`/bit` 로그인 명령 추가
- ChatGPT/Codex 및 Google Antigravity OAuth만 노출
- 로컬 코딩 도구만 허용하고 플러그인·MCP·웹·메시징·cron·위임 기능 차단
- 관리형 gateway와 기존 동적 skill-tool 배포 경로 제거
- MIT 출처를 남긴 여섯 개 코딩 방법론을 패키지 내부 읽기 전용 스킬로 재구성
- Python 3.14 설치 지원과 의존성·보안·패키징 회귀 테스트 추가

상세한 파일·기능별 변경 및 파생 관계는 [CUSTOMIZATION.md](CUSTOMIZATION.md),
배포 고지는 [NOTICE.md](NOTICE.md), MIT 전문은 [LICENSE](LICENSE)를 확인하세요.
