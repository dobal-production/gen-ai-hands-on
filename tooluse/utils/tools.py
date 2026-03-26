import json
import re
import yfinance as yf
import FinanceDataReader as fdr

# Bedrock Converse API Tool 스키마 정의
TOOLS = [
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
            "name": "get_stock_history",
            "description": "최근 N일간 주가 히스토리(시가, 고가, 저가, 종가, 거래량)를 조회합니다.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커 심볼 (예: AAPL, 005930.KS)"},
                        "days": {"type": "integer", "description": "조회할 기간(일수), 기본값 30", "default": 30},
                    },
                    "required": ["ticker"],
                }
            },
        }
    }
]

def execute_tool(name, tool_input):
    """도구 실행. (Claude에 전달할 결과 문자열, 차트용 DataFrame or None) 반환"""
    chart_data = None

    if name == "find_ticker":
        company_name = tool_input["company_name"]

        # 한글 포함 여부 감지
        has_korean = bool(re.search(r"[가-힣]", company_name))

        if has_korean:
            # KRX 전체 종목 리스트에서 한글 이름으로 검색
            krx = fdr.StockListing("KRX")
            matched = krx[krx["Name"].str.contains(company_name, na=False)]
            results = []
            for _, row in matched.head(5).iterrows():
                market = row.get("Market", "")
                suffix = ".KQ" if market == "KOSDAQ" else ".KS"
                results.append({
                    "ticker": f"{row['Code']}{suffix}",
                    "name": row["Name"],
                    "exchange": market,
                    "type": "Equity",
                })
        else:
            # 영문 회사명은 Yahoo Finance Search 사용
            search = yf.Search(company_name, max_results=5)
            quotes = search.quotes
            results = [
                {
                    "ticker": q.get("symbol"),
                    "name": q.get("longname") or q.get("shortname"),
                    "exchange": q.get("exchDisp") or q.get("exchange"),
                    "type": q.get("typeDisp") or q.get("quoteType"),
                }
                for q in quotes
                if q.get("symbol")
            ]

        result = {"company_name": company_name, "results": results}
        return json.dumps(result, ensure_ascii=False, default=str), chart_data

    ticker = tool_input["ticker"]
    stock = yf.Ticker(ticker)

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
        days = int(tool_input.get("days", 30))
        hist = stock.history(period=f"{days}d")
        chart_data = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        chart_data.index = chart_data.index.tz_localize(None)
        records = [
            {
                "date": str(idx.date()),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]
        result = {"ticker": ticker, "days": days, "history": records}

    return json.dumps(result, ensure_ascii=False, default=str), chart_data
