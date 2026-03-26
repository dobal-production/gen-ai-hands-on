# 한국금융규제 관련 Q&A 채팅봇

Amazon Bedrock Knowledge Base를 활용한 RAG(Retrieval-Augmented Generation) 기반 한국어 채팅봇입니다. 한국 금융 규제 관련 질문에 대해 정확하고 신뢰할 수 있는 답변을 제공합니다.

## 주요 기능

- **AI 모델**: Amazon Nova 2 Lite (Global 크로스리전 추론)
- **실시간 스트리밍 응답**: Bedrock Converse Stream API 기반 빠른 대화형 경험
- **RAG 기반 검색**: Amazon Bedrock Knowledge Base 연동 (관련성 점수 0.4 이상 필터링)
- **참고 문서 제공**: 답변 근거가 되는 S3 문서 및 관련성 점수 표시
- **설정 가능한 파라미터**: Temperature, Top-P, Max Tokens, 검색 문서 수 조정
- **관리자 페이지**: 문서 업로드 및 Knowledge Base 동기화

## 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Amazon Bedrock  │    │  Knowledge Base │
│   Frontend      │◄──►│    Runtime       │◄──►│   (Vector DB)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        ▲
                                               ┌────────┴────────┐
                                               │    S3 Bucket    │
                                               │  (규제 문서)     │
                                               └─────────────────┘
```

## 빠른 시작

### 사전 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- AWS 계정 및 자격 증명 설정
- Amazon Bedrock 모델 액세스 권한 (Global 크로스리전 추론)
- Amazon Bedrock Knowledge Base 및 S3 버킷

### 로컬 설치

1. **의존성 설치**
   ```bash
   uv sync
   ```

2. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일을 편집하여 설정값 입력
   ```

   `.env.example` 템플릿:
   ```env
   AWS_REGION=us-east-1
   RAG_BUCKET_NAME=your-s3-bucket-here
   KNOWLEDGE_BASE_ID=your-knowledge-base-id-here
   DATA_SOURCE_ID=your-data-source-id-here
   LOG_LEVEL=INFO
   ```

3. **애플리케이션 실행**
   ```bash
   uv run streamlit run app.py
   ```

### Docker 실행

1. **Docker 이미지 빌드**
   ```bash
   docker build -t korean-regulation-rag .
   ```

2. **컨테이너 실행**
   ```bash
   docker run -p 80:80 --env-file .env korean-regulation-rag
   ```

3. **브라우저에서 접속**
   ```
   http://localhost:80/regulation
   ```

## 환경 설정

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `AWS_REGION` | AWS 리전 | `us-east-1` |
| `KNOWLEDGE_BASE_ID` | Bedrock Knowledge Base ID | (필수) |
| `RAG_BUCKET_NAME` | 문서 저장 S3 버킷 이름 | (관리자 기능 필수) |
| `DATA_SOURCE_ID` | Knowledge Base 데이터 소스 ID | (관리자 기능 필수) |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

### AWS 자격 증명

다음 중 하나의 방법으로 AWS 자격 증명을 설정하세요:

- AWS CLI: `aws configure`
- 환경 변수: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- IAM 역할 (EC2/ECS 환경)
- AWS 프로파일

### 필요한 AWS 권한

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "arn:aws:bedrock:*::foundation-model/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve"
            ],
            "Resource": "arn:aws:bedrock:*:*:knowledge-base/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:StartIngestionJob"
            ],
            "Resource": "arn:aws:bedrock:*:*:knowledge-base/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::<your-bucket>",
                "arn:aws:s3:::<your-bucket>/*"
            ]
        }
    ]
}
```

## 사용법

### 기본 채팅

1. 웹 인터페이스(`/regulation`)에서 질문을 입력하세요
2. AI가 Knowledge Base에서 관련 문서를 검색합니다 (관련성 점수 0.4 이상)
3. 검색된 컨텍스트를 기반으로 실시간 스트리밍 응답을 제공합니다
4. 답변 아래 참고 문서 목록과 관련성 점수를 확인할 수 있습니다

### 사이드바 설정

| 설정 | 범위 | 기본값 |
|------|------|--------|
| 모델 선택 | Amazon Nova 2 Lite | Amazon Nova 2 Lite |
| Max Tokens | 100 ~ 8,000 | 4,000 |
| Temperature | 0.0 ~ 1.0 | 0.0 |
| Top P | 0.0 ~ 1.0 | 0.9 |
| 검색할 문서 수 | 1 ~ 20 | 5 |

### 관리자 페이지

`?admin=true` 쿼리 파라미터를 추가하여 관리자 페이지에 접속할 수 있습니다:

```
http://localhost:80/regulation?admin=true
```

관리자 페이지에서 제공하는 기능:
- PDF, TXT, DOCX, MD 파일을 S3에 업로드
- Knowledge Base 데이터 소스 동기화 (Ingestion Job 시작)
- S3 버킷 내 파일 목록 조회

> **주의**: 관리자 기능을 사용하려면 `RAG_BUCKET_NAME`, `KNOWLEDGE_BASE_ID`, `DATA_SOURCE_ID` 환경 변수가 모두 설정되어야 합니다.

## 프로젝트 구조

```
fsi-regulation/
├── app.py                 # Streamlit 메인 애플리케이션 (채팅 UI)
├── admin.py               # 관리자 페이지 (문서 업로드 및 KB 동기화)
├── utils/
│   ├── __init__.py
│   └── bedrock_lib.py     # BedrockRAG 클래스 (RAG 핵심 로직)
├── pyproject.toml         # 프로젝트 설정 및 Python 의존성
├── uv.lock                # 의존성 잠금 파일 (uv)
├── Dockerfile             # Docker 컨테이너 설정
├── docker-build.sh        # Docker 빌드 스크립트
├── .env.example           # 환경 변수 템플릿
├── .env                   # 환경 변수 (git에서 제외)
└── README.md              # 프로젝트 문서
```

## 개발

### 로컬 개발 환경

```bash
# 자동 리로드 모드로 실행
uv run streamlit run app.py --server.runOnSave true

# 포트 지정 (기본값: 8501)
uv run streamlit run app.py --server.port 8080

# 디버그 모드
uv run streamlit run app.py --logger.level debug

# 패키지 추가
uv add <package>
```

### 코드 구조

- `app.py`: Streamlit UI, 사용자 입력 처리, 응답 스트리밍 표시
- `admin.py`: 관리자 UI, S3 업로드, Knowledge Base Ingestion Job 관리
- `utils/bedrock_lib.py`: `BedrockRAG` 클래스 - `retrieve_only()`로 KB 검색, `generate_response_stream()`으로 스트리밍 응답 생성

## Docker 배포

### 헬스체크

컨테이너 헬스체크 엔드포인트:
```
http://localhost:80/_stcore/health
```

### 프로덕션 배포

```bash
# 프로덕션 이미지 빌드
docker build -t korean-regulation-rag:prod .

# AWS ECR 배포 예시
docker tag korean-regulation-rag:prod <account>.dkr.ecr.<region>.amazonaws.com/korean-regulation-rag:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/korean-regulation-rag:latest
```

## 문제 해결

### 일반적인 문제

1. **모델 액세스 오류**
   - Amazon Bedrock 콘솔에서 Global 크로스리전 추론 모델 액세스 권한 확인
   - `AWS_REGION` 환경 변수가 올바른 리전으로 설정되었는지 확인

2. **관련 문서를 찾을 수 없음**
   - `KNOWLEDGE_BASE_ID` 환경 변수 확인
   - Knowledge Base 상태 및 문서 동기화 여부 확인
   - 검색할 문서 수 및 관련성 점수 임계값(0.4) 조건 확인

3. **관리자 페이지 오류**
   - `RAG_BUCKET_NAME`, `DATA_SOURCE_ID` 환경 변수 설정 여부 확인
   - S3 버킷 접근 권한(`s3:ListBucket`, `s3:PutObject`) 확인

4. **AWS 자격 증명 오류**
   - AWS CLI 설정 확인: `aws sts get-caller-identity`
   - IAM 권한 정책 검토

### 로그 확인

```bash
# Streamlit 로그
uv run streamlit run app.py --logger.level debug

# Docker 컨테이너 로그
docker logs <container-id>
```

`LOG_LEVEL` 환경 변수로 로그 레벨을 조정할 수 있습니다 (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

---

**Made with Amazon Bedrock and Streamlit**
