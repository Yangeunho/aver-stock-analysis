import json
from datetime import datetime

class AiFormatter:
    """
    네이버 증권 API 응답 데이터를 Gemini(LLM) 분석에 최적화된 구조로 변환하는 클래스
    """
    
    @staticmethod
    def format_minute_data(raw_response, stock_name, stock_code, tic_scope='1'):
        """
        네이버 분봉 차트 데이터를 분석용 구조로 변환
        """
        raw_list = raw_response.get('list', [])
        
        if not raw_list:
            return {"error": "No data available in the raw response."}
        
        # 1. 컬럼 정의 (LLM이 이해하기 쉬운 명칭)
        # 네이버 필드명: time(시간), close(종가), open(시가), high(고가), low(저가), volume(거래량), amount(거래대금)
        columns = ["time", "close", "open", "high", "low", "volume", "amount"]
        
        # 2. 데이터 변환 및 기초 계산
        formatted_data = []
        prices = []
        
        for item in raw_list:
            # naver_collector.py에서 생성된 필드명으로 매핑
            row = [
                item.get('time', ''),
                int(item.get('close', 0)),
                int(item.get('open', 0)),
                int(item.get('high', 0)),
                int(item.get('low', 0)),
                int(item.get('volume', 0)),
                int(item.get('amount', 0))
            ]
            formatted_data.append(row)
            prices.append(row[1]) # 종가 기준
            
        # 3. 요약 정보 계산 (데이터는 과거 -> 현재 순으로 가정)
        # Naver fchart API는 과거 데이터를 먼저 줌 (0: oldest, -1: latest)
        summary = {
            "period_high": max(prices) if prices else 0,
            "period_low": min(prices) if prices else 0,
            "start_price": prices[0] if prices else 0,
            "end_price": prices[-1] if prices else 0,
            "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0
        }
        
        if summary["start_price"] != 0:
            summary["price_change_percent"] = round((summary["price_change"] / summary["start_price"]) * 100, 2)
        else:
            summary["price_change_percent"] = 0.0

        # 4. 최종 구조 생성
        result = {
            "metadata": {
                "stock_name": stock_name,
                "stock_code": stock_code,
                "data_type": "minute_chart",
                "interval": f"{tic_scope}m",
                "total_records": len(formatted_data),
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": summary
            },
            "columns": columns,
            "data": formatted_data
        }
        
        return result

    @staticmethod
    def to_json_string(formatted_data):
        """변환된 데이터를 JSON 문자열로 반환 (토큰 절약을 위해 compact하게 반환 가능)"""
        return json.dumps(formatted_data, ensure_ascii=False)

# 사용 예시
if __name__ == "__main__":
    # Naver Finance 형식의 테스트 데이터 (과거 -> 현재 순서)
    mock_raw_data = {
        "list": [
            {"time": "202602201434", "close": "84200", "open": "84000", "high": "84300", "low": "83900", "volume": "800", "amount": "67360000"},
            {"time": "202602201435", "close": "84500", "open": "84200", "high": "84600", "low": "84100", "volume": "1000", "amount": "84500000"}
        ]
    }
    
    formatter = AiFormatter()
    optimized = formatter.format_minute_data(mock_raw_data, "삼성전자", "005930")
    
    print("--- Optimized Data for Gemini ---")
    print(json.dumps(optimized, indent=2, ensure_ascii=False))
