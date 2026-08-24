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
python -m pip install "git+https://github.com/realmi-lab/bithumb-agent.git@v0.19.0.post2"
```

설치 후 실행합니다.

```bash
bithumb-agent
```

## 인증과 모델 선택

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
python -m pip install -e .
bithumb-agent
```

## 보안 범위

외부 에이전트 도구는 터미널/프로세스 관리, 파일 읽기·쓰기·패치·검색, 로컬 코드 실행, 작업 계획 및 확인 기능으로 제한됩니다. 플러그인, MCP 서버, 브라우저/웹 도구, 미디어 생성, TTS, 장기 메모리, 위임, cron, 컴퓨터 제어, 메시징 도구 등은 비활성화됩니다.

기업 또는 금융권 검토 전에는 [SECURITY_REVIEW.md](SECURITY_REVIEW.md)를 확인하세요. 저장소에는 비활성화된 Hermes 상류 구현 일부가 남아 있으며, 외부 `agy` 바이너리의 기능은 물리적으로 제거하는 대신 런타임에서 제한합니다.

## 오픈소스와 라이선스

Bithumb Agent는 Nous Research의 Hermes Agent를 기반으로 하며 원 프로젝트의 MIT 라이선스와 저작권 고지를 유지합니다. 자세한 출처와 변경 고지는 [NOTICE.md](NOTICE.md), 라이선스 전문은 [LICENSE](LICENSE)를 확인하세요.
