### 실습 : Model 추가
`app.py` 파일에 최신 모델을 추가해보세요.

```python
MODEL_OPTIONS = {
    "Claude Sonnet 4.6": "채워야 할 부분",
    "Claude Haiku 4.5": "채워야 할 부분",
    "Amazon Nova 2 Lite": "global.amazon.nova-2-lite-v1:0"
}
```

### 실습 : 파일 업로드 후, 데이터 동기화
`admin.py` 파일에 S3파일 업로드 후, Amazon Bedrock Knowledge Base의 데이터 소스를 자동으로 동기화하는 코드를 추가해보세요.

```python
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
<이 곳에 추가 코드가 들어야야 합니다.>
```

### 실습 : 유사도 변경 후, 결과 확인
`utils/bedrock_lib.py` 파일에서 유사도 점수를 조정하여 결과를 관찰합니다.
 ```python
# strands_tools의 filter_results_by_score로 유사도 0.4 미만 결과 제거
all_results = response.get("retrievalResults", [])
filtered = filter_results_by_score(all_results, min_score=0.4)
 ```