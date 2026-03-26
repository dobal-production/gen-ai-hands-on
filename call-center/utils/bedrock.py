import boto3
import json
import os
from typing import Optional
import streamlit as st
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class BedrockClient:
    """Amazon Bedrock AI 모델 연동 클라이언트"""

    # 콜센터 어시스턴트의 기본 시스템 메시지
    DEFAULT_SYSTEM_MESSAGE = """당신은 친절한 콜센터 어시스턴트입니다.
            고객 문의에 전문적이고 공감하는 답변을 제공해 주세요.

            가이드라인:
            - 정중하고 전문적인 태도를 유지하세요
            - 명확하고 실행 가능한 해결책을 제시하세요
            - 고객의 불편에 공감을 표현하세요
            - 답변은 간결하되 충분한 내용을 담으세요
            """

    # 기본 추론 설정
    # - maxTokens: 모델이 생성할 최대 토큰 수 (응답 길이 제한)
    # - temperature: 응답의 무작위성 조절 (0.0 = 결정적, 1.0 = 창의적). 0.7은 균형 잡힌 응답 생성
    # - topP: 누적 확률 기반 토큰 샘플링 범위 (0.9 = 상위 90% 확률 토큰만 사용)
    DEFAULT_INFERENCE_CONFIG = {
        "maxTokens": 1000,
        "temperature": 0.7,
        "topP": 0.9
    }

    def __init__(self, region_name: Optional[str] = None):
        """
        Bedrock 클라이언트 초기화

        Args:
            region_name: AWS 리전 이름 (선택 사항, 기본값은 환경 변수)
        """
        try:
            # 환경 변수 또는 제공된 값 또는 기본값에서 리전 가져오기
            self.region_name = region_name or os.getenv('AWS_REGION', 'ap-northeast-2')
            
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
        except Exception as e:
            st.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise
    
    def generate_response(
        self,
        prompt: str,
        model_id: str,
        inference_config: Optional[dict] = None,
        custom_system_message: Optional[str] = None
    ) -> str:
        """
        Amazon Bedrock Converse API를 사용하여 응답 생성 (비스트리밍)

        Args:
            prompt: 사용자 입력 프롬프트
            model_id: Bedrock 모델 식별자
            inference_config: 추론 파라미터 딕셔너리 (maxTokens, temperature, topP)
            custom_system_message: 선택적 커스텀 시스템 메시지

        Returns:
            생성된 응답 텍스트
        """
        try:
            # 커스텀 시스템 메시지가 제공된 경우 사용, 아니면 기본값 사용
            system_message = custom_system_message if custom_system_message else self.DEFAULT_SYSTEM_MESSAGE

            # Converse API용 메시지 준비
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]

            # 제공된 추론 설정 또는 기본값 사용
            final_inference_config = inference_config if inference_config else self.DEFAULT_INFERENCE_CONFIG

            # Converse API 호출
            response = self.bedrock_runtime.converse(
                modelId=model_id,
                messages=messages,
                system=[{"text": system_message}],
                inferenceConfig=final_inference_config
            )

            # 응답 텍스트 추출
            return response['output']['message']['content'][0]['text']
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            st.error(error_msg)
            return error_msg
    
    def generate_response_stream(
        self,
        prompt: str,
        model_id: str,
        inference_config: Optional[dict] = None,
        custom_system_message: Optional[str] = None
    ):
        """
        Amazon Bedrock Converse Stream API를 사용하여 스트리밍 응답 생성

        Args:
            prompt: 사용자 입력 프롬프트
            model_id: Bedrock 모델 식별자
            inference_config: 추론 파라미터 딕셔너리 (maxTokens, temperature, topP)
            custom_system_message: 선택적 커스텀 시스템 메시지

        Yields:
            스트리밍 응답 청크
        """
        try:
            # 커스텀 시스템 메시지가 제공된 경우 사용, 아니면 기본값 사용
            system_message = custom_system_message if custom_system_message else self.DEFAULT_SYSTEM_MESSAGE

            # Converse API용 메시지 준비
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]

            # 제공된 추론 설정 또는 기본값 사용
            final_inference_config = inference_config if inference_config else self.DEFAULT_INFERENCE_CONFIG

            # Converse Stream API 호출
            response = self.bedrock_runtime.converse_stream(
                modelId=model_id,
                messages=messages,
                system=[{"text": system_message}],
                inferenceConfig=final_inference_config
            )

            # 스트리밍 응답 처리
            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    delta = event['contentBlockDelta']['delta']
                    if 'text' in delta:
                        yield delta['text']
                elif 'messageStop' in event:
                    break
                    
        except Exception as e:
            error_msg = f"Error generating streaming response: {str(e)}"
            st.error(error_msg)
            yield error_msg
    
    def list_available_models(self) -> list:
        """
        사용 가능한 Bedrock 모델 목록 조회

        Returns:
            사용 가능한 모델 ID 목록
        """
        try:
            # 런타임 클라이언트와 동일한 리전 사용
            bedrock = boto3.client('bedrock', region_name=self.region_name)
            response = bedrock.list_foundation_models()
            return [model['modelId'] for model in response['modelSummaries']]
        except Exception as e:
            st.error(f"Error listing models: {str(e)}")
            return []