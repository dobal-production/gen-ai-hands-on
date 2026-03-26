import streamlit as st
import os
import yaml
from utils.bedrock import BedrockClient

def load_transcript_file(file_path: str) -> str:
    """
    파일에서 녹취 텍스트를 로드합니다.

    Args:
        file_path: 녹취 파일 경로

    Returns:
        녹취 텍스트 내용
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return "녹취 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"파일 읽기 오류: {str(e)}"

def load_prompt_examples(file_path: str = "prompt_examples.yaml") -> dict:
    """
    YAML 파일에서 프롬프트 예제를 로드합니다.

    Args:
        file_path: 프롬프트 예제가 담긴 YAML 파일 경로

    Returns:
        프롬프트 예제가 담긴 딕셔너리
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        else:
            return {"prompt_examples": {}}
    except Exception as e:
        st.error(f"프롬프트 예제 파일 읽기 오류: {str(e)}")
        return {"prompt_examples": {}}

def main():
    st.set_page_config(
        page_title="고객센터 데모",
        page_icon="📞",
        layout="wide"
    )
    
    st.title("📞 자동차 보험 상담")
    st.markdown("Amazon Bedrock을 활용한 AI 기반 고객센터 지원 시스템")

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 모델 설정")
        
        # 아래의 모델을 model_options에 추가하세요.
        # "Claude Sonnet 4.6": "global.anthropic.claude-sonnet-4-6",
        # "Claude Haiku 4.5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
        # "Claude Opus 4.6": "global.anthropic.claude-opus-4-6-v1",
        # "Nova Pro": "apac.amazon.nova-pro-v1:0",
        # "Nova 2 Lite": "global.amazon.nova-2-lite-v1:0"
        model_options = {
            "Claude Sonnet 4.6": "global.anthropic.claude-sonnet-4-6"
        }
        
        selected_model_name = st.selectbox(
            "모델 선택",
            options=list(model_options.keys()),
            help="응답 생성을 위한 AI 모델을 선택하세요"
        )
        
        # 실제 모델 ID 가져오기
        model_id = model_options[selected_model_name]
        
        st.divider()
        
        # 추론 파라미터
        st.subheader("🎛️ 추론 파라미터")
        
        max_tokens = st.slider(
            "최대 토큰",
            min_value=100,
            max_value=4000,
            value=2000,
            step=100,
            help="응답의 최대 토큰 수"
        )
        
        temperature = st.slider(
            "온도 (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="무작위성 제어: 낮을수록 집중적, 높을수록 창의적"
        )
        
        st.divider()
        
        # 시스템 메시지 커스터마이징
        st.subheader("📝 시스템 프롬프트")
        custom_system_message = st.text_area(
            "커스텀 시스템 프롬프트 (선택사항)",
            placeholder="AI 어시스턴트에 대한 커스텀 지시를 입력하세요...",
            height=100,
            help="기본 시스템 프롬프트를 커스텀 지시로 덮어씁니다"
        )
    
    with st.expander("아키텍처 보기"):
        st.image("images/call-center-01.png")

    st.audio("media/3_Inquiries_related_to_premium_surcharge_calculation.mp3", format='audio/mp3')

    # 녹취 파일 경로 설정 (필요에 따라 수정)
    transcript_file_path = "media/3_Inquiries_related_to_premium_surcharge_calculation.txt"
    
    # 녹취 텍스트 로드 (전역적으로 사용)
    transcript_text = load_transcript_file(transcript_file_path)
    
    with st.expander("녹취록 보기"):
        # 녹취 내용 표시
        st.write(transcript_text)

    # 메인 콘텐츠 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("프롬프트")
        # "적용" 버튼으로 전달된 내용이 있으면 session_state에 반영 후 삭제
        if "transcript_copied" in st.session_state:
            st.session_state.user_input_area = st.session_state.pop("transcript_copied")

        # key를 사용하면 재렌더링 시에도 session_state가 값을 유지함
        user_input = st.text_area(
            "AI에게 지시를 내려주세요.:",
            key="user_input_area",
            height=250,
            placeholder="고객의 문의 내용을 입력하세요..."
        )
        
        if st.button("실행", type="primary"):
            if user_input:
                try:
                    bedrock_client = BedrockClient()
                    
                    # 추론 설정 준비
                    inference_config = {
                        "maxTokens": max_tokens,
                        "temperature": temperature
                    }
                    
                    # 녹취록을 포함한 컨텍스트 기반 프롬프트 준비
                    context_prompt = f"""다음은 고객과 상담원 간의 통화 녹취록입니다:

<context>
{transcript_text}
</context>

위 <context>내용을 참고하여 다음 요청에 답변해주세요:

{user_input}"""
                    
                    # 항상 스트리밍 응답 사용
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # Bedrock 스트리밍 API를 호출하여 응답을 청크(chunk) 단위로 수신
                    # - prompt: 통화 내용(transcript)이 포함된 컨텍스트 프롬프트
                    # - model_id: 사용할 Claude 모델 ID
                    # - inference_config: temperature 등 추론 파라미터
                    # - custom_system_message: 사용자 정의 시스템 프롬프트 (없으면 None)
                    for chunk in bedrock_client.generate_response_stream(
                        prompt=context_prompt,
                        model_id=model_id,
                        inference_config=inference_config,
                        custom_system_message=custom_system_message if custom_system_message else None
                    ):
                        full_response += chunk  # 수신된 청크를 누적하여 전체 응답 조합
                        response_placeholder.markdown(full_response + " ▋")  # 타이핑 커서(▋)와 함께 실시간으로 UI 업데이트
                    
                    response_placeholder.markdown(full_response)
                    st.success("응답 생성이 완료되었습니다!")
                            
                except Exception as e:
                    st.error(f"오류: {str(e)}")
            else:
                st.warning("프롬프트를 입력해주세요.")
    
    # 프롬프트 예제를 위한 영역
    with col2:
        st.subheader("프롬프트 예제들")
        
        # YAML 파일에서 프롬프트 예제들 로드
        prompt_data = load_prompt_examples()
        prompt_examples = prompt_data.get("prompt_examples", {})
        
        # 각 프롬프트 예제를 expander와 st.code로 표시
        # "적용" 버튼 클릭 시 session_state에 내용을 저장하고 rerun하여 text_area에 반영
        for key, example in prompt_examples.items():
            title = example.get("title", key)
            content = example.get("content", "")

            with st.expander(title):
                st.code(content, language="text")
                if st.button("적용", key=f"apply_{key}"):
                    st.session_state.transcript_copied = content
                    st.rerun()
        

if __name__ == "__main__":
    main()