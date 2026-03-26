# 주식 분석 AI - Tool Use 데모

YFinance와 Amazon Bedrock Converse API의 **Tool Use** 기능을 활용한 주식 분석 Streamlit 애플리케이션입니다.

## 프로젝트 개요

AI가 사용자의 질문을 분석하여 필요한 도구를 **자동으로 선택·호출**하고, 실시간 주식 데이터를 기반으로 답변을 생성합니다.

## 기술 스택

| 구분 | 기술 |
|------|------|
| UI | Streamlit |
| AI | Amazon Bedrock Converse API |
| AI 모델 | `global.anthropic.claude-sonnet-4-6` |
| 주식 데이터 | yfinance |
| 언어 | Python 3.14 |
| 패키지 관리 | uv |

## 파일 구조

```
fsi-demo-genai-tool-use/
├── app.py                  # Streamlit 메인 앱 (UI + 흐름 제어)
├── utils/
│   ├── tools.py            # YFinance Tool 정의 (schema + 실행 함수)
│   └── bedrock.py          # Bedrock Converse API 호출 (Tool Use 루프)
├── pyproject.toml
├── REQUIREMENTS.md
└── README.md
```

## 사용 가능한 도구 (Tools)

| 도구 이름 | 설명 |
|-----------|------|
| `get_stock_price` | 현재 주가, 시가총액, PER, 52주 고/저가 조회 |
| `get_stock_history` | 최근 N일간 주가 히스토리 조회 + 라인 차트 |
| `get_financials` | 재무제표 조회 (매출, 영업이익, 순이익) |
| `get_stock_news` | 종목 관련 최신 뉴스 5건 조회 |

## Tool Use 동작 흐름

```
사용자 입력 (티커 + 질문)
    │
    ▼
utils/bedrock.py - Converse API 호출 (tools 포함)
    │
    ▼
stopReason == "tool_use"?
    │
   YES ──▶ utils/tools.py - YFinance 데이터 조회
    │           │
    │           ▼
    │      toolResult 포함하여 Converse API 재호출
    │           │
    │           ▼
   NO  ◀── 최종 텍스트 응답 반환
    │
    ▼
app.py - 채팅 버블 + (필요시) 라인 차트 표시
```

## 실행 방법

```bash
uv run streamlit run app.py
```

## 질문 예시

- 현재 주가 알려줘
- 최근 한달 주가 흐름 분석해줘
- 재무 상태 요약해줘
- 최근 뉴스 알려줘

## 의존성

```toml
dependencies = [
    "streamlit>=1.55.0",
    "boto3>=1.35.0",
    "yfinance>=0.2.0",
    "pandas>=2.0.0",
]
```

## AWS 인증

AWS 자격증명은 **EC2 IAM Role**을 사용합니다. 코드에 키를 하드코딩하지 않으며, boto3가 인스턴스 메타데이터에서 자동으로 획득합니다.

## 참고

상세 요구사항은 [REQUIREMENTS.md](REQUIREMENTS.md)를 참조하세요.
