import streamlit as st
from utils.bedrock import chat

st.title("주식 분석 AI")

# 사이드바
with st.sidebar:
    ticker = st.text_input("주식 티커", value="AAPL", placeholder="예: AAPL, 005930.KS")
    st.markdown("**질문 예시**")
    st.caption("- 현재 주가 알려줘\n- 최근 한달 주가 흐름 분석해줘\n- 재무 상태 요약해줘\n- 최근 뉴스 알려줘")

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []   # Bedrock API용 (tool use 중간 메시지 포함)
if "display" not in st.session_state:
    st.session_state.display = []    # 화면 표시용: [{"role", "content", "chart"}]

# 대화 이력 표시
for item in st.session_state.display:
    with st.chat_message(item["role"]):
        st.write(item["content"])
        if item.get("chart") is not None:
            st.line_chart(item["chart"])

# 사용자 입력
if prompt := st.chat_input("주식에 대해 질문하세요..."):
    user_text = f"[{ticker}] {prompt}"

    with st.chat_message("user"):
        st.write(user_text)

    st.session_state.messages.append({"role": "user", "content": [{"text": user_text}]})
    st.session_state.display.append({"role": "user", "content": user_text})

    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            response_text, chart_data = chat(st.session_state.messages)

        st.write(response_text)
        if chart_data is not None:
            st.line_chart(chart_data)

    st.session_state.display.append({
        "role": "assistant",
        "content": response_text,
        "chart": chart_data,
    })
