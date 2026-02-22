import json
from datetime import datetime

class AiFormatter:
    """
    키움증권 REST API 응답 데이터를 Gemini(LLM) 분석에 최적화된 구조로 변환하는 클래스
    """
    
    @staticmethod
    def format_minute_data(raw_response, stock_name, stock_code, tic_scope='1'):
        """
        분봉 차트(ka10080) 원시 데이터를 분석용 구조로 변환
        """
        raw_list = raw_response.get('list', [])
        
        if not raw_list:
            return {"error": "No data available in the raw response."}
        
        # 1. 컬럼 정의 (LLM이 이해하기 쉬운 명칭)
        # 키움 필드명: stck_cntg_hour(체결시간), stck_prpr(현재가), stck_oprc(시가), stck_hgpr(고가), stck_lwpr(저가), cntg_vol(체결량)
        columns = ["time", "close", "open", "high", "low", "volume", "amount"]
        
        # 2. 데이터 변환 및 기초 계산
        formatted_data = []
        prices = []
        
        for item in raw_list:
            # 문자열 숫자를 int/float로 변환
            row = [
                item.get('stck_cntg_hour', ''),
                int(item.get('stck_prpr', 0)),
                int(item.get('stck_oprc', 0)),
                int(item.get('stck_hgpr', 0)),
                int(item.get('stck_lwpr', 0)),
                int(item.get('cntg_vol', 0)),
                int(item.get('cntg_amt', 0))
            ]
            formatted_data.append(row)
            prices.append(row[1]) # 종가 기준
            
        # 3. 요약 정보 계산
        summary = {
            "period_high": max(prices) if prices else 0,
            "period_low": min(prices) if prices else 0,
            "start_price": prices[-1] if prices else 0,
            "end_price": prices[0] if prices else 0,
            "price_change": prices[0] - prices[-1] if len(prices) > 1 else 0
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
    # 가상의 키움 API 응답 데이터 (ka10080 방식)
    mock_raw_data = {
        "list": [
            {"stck_cntg_hour": "143500", "stck_prpr": "84500", "stck_oprc": "84200", "stck_hgpr": "84600", "stck_lwpr": "84100", "cntg_vol": "1000"},
            {"stck_cntg_hour": "143400", "stck_prpr": "84200", "stck_oprc": "84000", "stck_hgpr": "84300", "stck_lwpr": "83900", "cntg_vol": "800"}
        ]
    }
    
    formatter = AiFormatter()
    optimized = formatter.format_minute_data(mock_raw_data, "삼성전자", "005930")
    
    print("--- Optimized Data for Gemini ---")
    print(json.dumps(optimized, indent=2, ensure_ascii=False))
