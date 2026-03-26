import boto3
import json
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from botocore.config import Config as BotocoreConfig
from strands_tools.retrieve import filter_results_by_score

load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# 상수 정의
SYSTEM_PROMPT = "당신은 한국어로 답변하는 도움이 되는 AI 어시스턴트입니다."

class BedrockRAG:
    """Amazon Bedrock을 활용한 RAG(Retrieval-Augmented Generation) 클래스
    
    한국 금융 규제 관련 질문에 대해 Knowledge Base 검색과 AI 모델을 결합하여
    정확하고 신뢰할 수 있는 답변을 제공합니다.
    """
    
    def __init__(self, model_id: str = None, region_name: str = None, knowledge_base_id: str = None):
        """BedrockRAG 인스턴스 초기화
        
        Args:
            model_id (str, optional): 사용할 Bedrock 모델 ID
            region_name (str, optional): AWS 리전명. 기본값은 환경변수 AWS_REGION
            knowledge_base_id (str, optional): Knowledge Base ID. 기본값은 환경변수 KNOWLEDGE_BASE_ID
        """
        self.region_name = region_name or os.getenv("AWS_REGION")
        self.knowledge_base_id = knowledge_base_id or os.getenv("KNOWLEDGE_BASE_ID")
        self.model_id = model_id
        
        logger.info(f"BedrockRAG 초기화: region={self.region_name}, model={self.model_id}, kb_id={self.knowledge_base_id}")
        
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region_name
        )
    
    def generate_response_stream(self, prompt: str, context: str = "", max_tokens: int = 1000, temperature: float = 0.0, top_p: float = 0.9):
        """Bedrock Converse Stream API를 사용하여 스트리밍 응답 생성
        
        Args:
            prompt (str): 사용자 질문
            context (str, optional): 검색된 컨텍스트 정보. 기본값은 빈 문자열
            max_tokens (int, optional): 최대 토큰 수. 기본값은 1000
            temperature (float, optional): 창의성 수준 (0.0-1.0). 기본값은 0.0
            top_p (float, optional): 응답 다양성 (0.0-1.0). 기본값은 0.9
            
        Yields:
            str: 스트리밍되는 응답 텍스트 조각
        """
        system_prompt = SYSTEM_PROMPT
        
        if context:
            system_prompt += f"\n\n다음 컨텍스트를 참고하여 답변하세요:\n{context}"
        
        logger.info(f"응답 생성 시작: model={self.model_id}, max_tokens={max_tokens}")
        
        try:
            response = self.bedrock_runtime.converse_stream(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            )
            
            for event in response["stream"]:
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"]["delta"]
                    if "text" in delta:
                        yield delta["text"]
            
                        
        except Exception as e:
            logger.error(f"응답 생성 오류: {str(e)}")
            yield f"오류가 발생했습니다: {str(e)}"
    
    def retrieve_only(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Knowledge Base에서 관련 문서만 검색
        
        Args:
            query (str): 검색 쿼리
            max_results (int, optional): 최대 검색 결과 수. 기본값은 5
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 리스트. 각 항목은 다음 키를 포함:
                - content (str): 문서 내용
                - score (float): 관련성 점수
                - location (dict): 문서 위치 정보
        """
        if not self.knowledge_base_id:
            logger.warning("Knowledge Base ID가 설정되지 않음")
            return []
        
        logger.info(f"문서 검색 시작: query='{query}', max_results={max_results}")

        try:
            # strands-agents 표준 user-agent를 포함한 Bedrock 클라이언트 생성
            config = BotocoreConfig(user_agent_extra="strands-agents-retrieve")
            client = boto3.client(
                "bedrock-agent-runtime",
                region_name=self.region_name,
                config=config
            )

            # Knowledge Base에 벡터 유사도 검색 요청
            response = client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": max_results
                    }
                }
            )

            # strands_tools의 filter_results_by_score로 유사도 0.4 미만 결과 제거
            all_results = response.get("retrievalResults", [])
            filtered = filter_results_by_score(all_results, min_score=0.4)

            # app.py에서 사용하는 구조(content, score, location)로 변환
            results = [
                {
                    "content": r["content"]["text"],
                    "score": r["score"],
                    "location": r.get("location", {})
                }
                for r in filtered
            ]

            logger.info(f"문서 검색 완료: {len(results)}개 결과")
            return results

        except Exception as e:
            logger.error(f"검색 오류: {str(e)}")
            return []

