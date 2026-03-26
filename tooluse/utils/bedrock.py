import boto3
from utils.tools import TOOLS, execute_tool

MODEL_ID = "global.anthropic.claude-sonnet-4-6"
SYSTEM_PROMPT = "당신은 주식 분석 전문가입니다. 제공된 도구를 활용하여 사용자의 질문에 답하세요."

client = boto3.client("bedrock-runtime", region_name="us-east-1")


def chat(messages):
    """
    Bedrock Converse API 호출 (Tool Use 1회 포함).
    messages 리스트를 직접 수정하며, (응답 텍스트, 차트 데이터) 반환.
    """
    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=messages,
        toolConfig={"tools": TOOLS},
    )

    chart_data = None

    # Tool Use 요청이 온 경우
    if response["stopReason"] == "tool_use":
        assistant_msg = response["output"]["message"]
        messages.append(assistant_msg)

        # 도구 실행 후 결과 수집
        tool_results = []
        for block in assistant_msg["content"]:
            if "toolUse" in block:
                tool_use = block["toolUse"]
                result_str, chart_data = execute_tool(tool_use["name"], tool_use["input"])
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"text": result_str}],
                    }
                })

        messages.append({"role": "user", "content": tool_results})

        # 도구 결과 포함하여 재호출
        response = client.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOLS},
        )

    # 최종 응답 저장 및 반환
    final_msg = response["output"]["message"]
    messages.append(final_msg)

    text = "".join(b["text"] for b in final_msg["content"] if "text" in b)
    return text, chart_data
