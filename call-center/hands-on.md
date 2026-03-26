### 실습 : 프롬프트들을 수정해 보세요

`prompt_examples.yaml` 파일의 내용을 수정해보세요.

### 실습 : 다양한 LLM 모델 추가하기

`app.py` 파일에서 주요 모델들을 추가해보세요. 

System-defined inference profiles에서 Global 프로파일을 사용하세요.
Haiku, Nova 2 Lite 모델을 추가해보세요.

```pyshon
model_options = {
    "Claude Sonnet 4.6": "global.anthropic.claude-sonnet-4-6"
}
```

### 실습 : 스트리밍 방식으로 수정해 보세요.    

`bedrock.py` 파일에는 스트리밍 방식의 응답 기능이 들어 있습니다. 
`app.py`을 동기식 응답 방식에서 스트리밍 방식으로 수정해보세요. 
> 타이핑 커서(▋)를 사용하도록 해보세요.
> 완성된 코드는 `complate/app.py`를 참고하세요.

---
`utils/bedrock.py`: 
```python
def generate_response_stream(
    self,
    prompt: str,
    model_id: str,
    inference_config: Optional[dict] = None,
    custom_system_message: Optional[str] = None
):
...
```

`app.py`
```python
# 동기식 응답 생성
response = bedrock_client.generate_response(
    prompt=context_prompt,
    model_id=model_id,
    inference_config=inference_config,
    custom_system_message=custom_system_message if custom_system_message else None
)
```