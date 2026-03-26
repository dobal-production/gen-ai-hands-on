import json
import yfinance as yf

# Bedrock Converse API Tool 스키마 정의
TOOLS = [
    {
        "toolSpec": {
            "name": "get_stock_price",
            "description": "현재 주가 및 기본 정보를 조회합니다.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커 심볼 (예: AAPL, 005930.KS)"}
                    },
                    "required": ["ticker"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "find_ticker",
            "description": "회사 이름으로 주식 티커 심볼을 검색합니다.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "검색할 회사 이름 (예: Apple, 삼성전자)"}
                    },
                    "required": ["company_name"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_stock_history",
            "description": "최근 N일간 주가 히스토리를 조회합니다.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커 심볼"},
                        "days": {"type": "integer", "description": "조회할 일수 (기본 30)"},
                    },
                    "required": ["ticker"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_financials",
            "description": "재무제표 데이터를 조회합니다 (매출, 영업이익, 순이익).",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커 심볼"}
                    },
                    "required": ["ticker"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_stock_news",
            "description": "종목 관련 최신 뉴스를 조회합니다.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커 심볼"}
                    },
                    "required": ["ticker"],
                }
            },
        }
    },
]


def execute_tool(name, tool_input):
    """도구 실행. (Claude에 전달할 결과 문자열, 차트용 DataFrame or None) 반환"""
    ticker = tool_input["ticker"]
    stock = yf.Ticker(ticker)
    chart_data = None

    if name == "get_stock_price":
        info = stock.info
        result = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName"),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        }

    elif name == "get_stock_history":
        days = tool_input.get("days", 30)
        df = stock.history(period=f"{days}d")
        chart_data = df[["Close"]].rename(columns={"Close": "종가"})
        result = {
            "ticker": ticker,
            "days": days,
            "start": str(df.index[0].date()),
            "end": str(df.index[-1].date()),
            "start_price": round(float(df["Close"].iloc[0]), 2),
            "end_price": round(float(df["Close"].iloc[-1]), 2),
            "high": round(float(df["High"].max()), 2),
            "low": round(float(df["Low"].min()), 2),
        }

    elif name == "get_financials":
        income = stock.financials
        if not income.empty:
            latest = income.iloc[:, 0]
            result = {
                "ticker": ticker,
                "period": str(income.columns[0].date()),
                "revenue": int(latest.get("Total Revenue", 0)),
                "operating_income": int(latest.get("Operating Income", 0)),
                "net_income": int(latest.get("Net Income", 0)),
            }
        else:
            result = {"ticker": ticker, "error": "재무 데이터 없음"}

    elif name == "get_stock_news":
        news_list = []
        for n in (stock.news or [])[:5]:
            if "content" in n:  # 최신 yfinance 형식
                c = n["content"]
                news_list.append({
                    "title": c.get("title", ""),
                    "publisher": c.get("provider", {}).get("displayName", ""),
                    "published": c.get("pubDate", ""),
                })
            else:  # 구버전 yfinance 형식
                news_list.append({
                    "title": n.get("title", ""),
                    "publisher": n.get("publisher", ""),
                    "published": str(n.get("providerPublishTime", "")),
                })
        result = {"ticker": ticker, "news": news_list}

    return json.dumps(result, ensure_ascii=False, default=str), chart_data
