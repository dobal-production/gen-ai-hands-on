import streamlit as st
import boto3
import os
from botocore.exceptions import ClientError
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS 클라이언트 초기화
@st.cache_resource
def get_aws_clients():
    region = os.getenv("AWS_REGION", "ap-northeast-2")
    return {
        "s3": boto3.client("s3", region_name=region),
        "bedrock_agent": boto3.client("bedrock-agent", region_name=region)
    }

def upload_to_s3(file, bucket_name, key):
    """S3에 파일 업로드"""
    try:
        clients = get_aws_clients()
        clients["s3"].upload_fileobj(file, bucket_name, key)
        return True
    except ClientError as e:
        logger.error(f"S3 업로드 실패: {e}")
        return False

def sync_knowledge_base(knowledge_base_id, data_source_id):
    """Knowledge Base 데이터 소스 동기화"""
    try:
        clients = get_aws_clients()
        response = clients["bedrock_agent"].start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        return response["ingestionJob"]["ingestionJobId"]
    except ClientError as e:
        logger.error(f"Knowledge Base 동기화 실패: {e}")
        return None

# 메인 UI
st.title("🔧 관리자 - 문서 업로드")
st.caption("Knowledge Base에 새로운 문서를 업로드하고 동기화합니다.")

# 홈으로 돌아가기 버튼
if st.button("🏠 홈으로 돌아가기"):
    st.switch_page("app.py")

# 환경 변수 확인
bucket_name = os.getenv("RAG_BUCKET_NAME")
knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")
data_source_id = os.getenv("DATA_SOURCE_ID")

# logger.info(f"환경 변수: RAG_BUCKET_NAME={bucket_name}, KNOWLEDGE_BASE_ID={knowledge_base_id}, DATA_SOURCE_ID={data_source_id}")

if not bucket_name or not knowledge_base_id or not data_source_id:
    st.error("환경 변수 RAG_BUCKET_NAME, KNOWLEDGE_BASE_ID, DATA_SOURCE_ID가 모두 설정되어야 합니다.")
    st.stop()

# 파일 업로드 섹션
st.subheader("📁 파일 업로드")

uploaded_files = st.file_uploader(
    "업로드할 파일을 선택하세요",
    accept_multiple_files=True,
    type=['pdf', 'txt', 'docx', 'md']
)

if uploaded_files:
    st.write(f"선택된 파일: {len(uploaded_files)}개")
    
    for file in uploaded_files:
        st.write(f"- {file.name} ({file.size:,} bytes)")
    
    if st.button("업로드 및 동기화 시작", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 파일 업로드
        uploaded_count = 0
        for i, file in enumerate(uploaded_files):
            status_text.text(f"업로드 중: {file.name}")
            
            if upload_to_s3(file, bucket_name, file.name):
                uploaded_count += 1
                st.success(f"✅ {file.name} 업로드 완료")
            else:
                st.error(f"❌ {file.name} 업로드 실패")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Knowledge Base 동기화
        if uploaded_count > 0:
            status_text.text("Knowledge Base 동기화 중...")
            job_id = sync_knowledge_base(knowledge_base_id, data_source_id)
            
            if job_id:
                st.success(f"🔄 Knowledge Base 동기화 시작됨 (Job ID: {job_id})")
                st.info("동기화가 완료될 때까지 몇 분 정도 소요될 수 있습니다.")
            else:
                st.error("Knowledge Base 동기화 실패")
        
        status_text.text("완료!")

# 현재 상태 확인
st.subheader("📊 현재 상태")

if st.button("S3 버킷 파일 목록 확인"):
    try:
        clients = get_aws_clients()
        response = clients["s3"].list_objects_v2(Bucket=bucket_name)
        
        if "Contents" in response:
            st.write(f"**총 {len(response['Contents'])}개 파일**")
            for obj in response["Contents"]:
                st.write(f"- {obj['Key']} ({obj['Size']:,} bytes, {obj['LastModified']})")
        else:
            st.write("버킷이 비어있습니다.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            st.error("❌ S3 버킷 접근 권한이 없습니다.")
            st.info("💡 필요한 권한: s3:ListBucket, s3:GetObject, s3:PutObject")
        else:
            st.error(f"S3 버킷 조회 실패: {e}")