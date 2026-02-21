import requests
import json
import re
from datetime import datetime
import xml.etree.ElementTree as ET

class NaverFinanceCollector:
    """
    네이버 증권에서 주식 데이터, 시황, 수급 정보를 수집하는 클래스
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_basic_info(self, stock_code):
        """종목 기본 정보 (현재가, 등락률 등) 조회"""
        url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{stock_code}"
        try:
            res = requests.get(url, headers=self.headers)
            data = res.json()
            # 국내 주식 필드 추출
            item = data.get("result", {}).get("areas", [])[0].get("datas", [])[0]
            return {
                "stock_name": item.get("nm"),
                "close_price": str(item.get("nv")),
                "fluctuation_rate": str(item.get("cr")),
                "market_cap": "N/A",
            }
        except Exception as e:
            print(f"Error fetching basic info: {e}")
            return None

    def get_market_environment(self):
        """지수 및 선물 정보 조회 (나스닥100 선물, 코스피200 선물 등)"""
        # 나스닥 100 선물: NAS@NQX, 코스피 200: KOSPI200
        url = "https://polling.finance.naver.com/api/realtime?query=SERVICE_INDEX:NAS@NQX,SERVICE_INDEX:KOSPI200"
        try:
            res = requests.get(url, headers=self.headers)
            data = res.json()
            results = {}
            for item in data.get("result", {}).get("areas", [])[0].get("datas", []):
                sym = item.get("nm")
                results[sym] = {
                    "price": item.get("nv"),
                    "change_rate": item.get("cr")
                }
            return results
        except Exception as e:
            print(f"Error fetching market environment: {e}")
            return None

    def get_minute_candles(self, stock_code, count=100):
        """분봉 데이터 조회 (XML API 활용)"""
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={stock_code}&timeframe=minute&count={count}&requestType=0"
        try:
            res = requests.get(url, headers=self.headers)
            root = ET.fromstring(res.text)
            candles = []
            for item in root.findall(".//item"):
                data = item.get("data").split("|")
                # data format: "시간|시가|고가|저가|종가|거래량"
                # 'null' 또는 0인 경우 처리를 강화합니다.
                def clean_int(val):
                    if not val or val.lower() == 'null':
                        return 0
                    return int(val)

                c = clean_int(data[4]) # 종가
                o = clean_int(data[1])
                h = clean_int(data[2])
                l = clean_int(data[3])
                v = clean_int(data[5])
                
                # 시/고/저가 가 0이면 종가로 대체 (일부 데이터 유실 대응)
                if o == 0: o = c
                if h == 0: h = c
                if l == 0: l = c

                candles.append({
                    "time": data[0],
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": v
                })
            return candles
        except Exception as e:
            print(f"Error fetching minute candles: {e}")
            return []

    def get_investor_and_program(self, stock_code):
        """외국인/기관/프로그램 수급 정보 스크래핑"""
        url = f"https://finance.naver.com/item/frgn.naver?code={stock_code}"
        try:
            res = requests.get(url, headers=self.headers)
            # HTML에서 프로그램 순매수 및 투자자 정보를 파싱 (간략화된 정규식 방식)
            # 수치만 추출하기 위해 특정 패턴을 찾습니다.
            html = res.text
            
            # 프로그램 순매수는 별도의 API나 더 정교한 파싱이 필요할 수 있으나, 
            # 여기서는 공개된 정보를 최대한 탐색합니다.
            # 실제 '프로그램 매매'는 다른 페이지에 있을 수 있어 보완이 필요할 수 있습니다.
            
            return {
                "source_url": url,
                "note": "프로그램 매매 및 상세 수급은 추가 스니펫 파싱이 필요할 수 있음"
            }
        except Exception as e:
            print(f"Error fetching investor info: {e}")
            return None

if __name__ == "__main__":
    collector = NaverFinanceCollector()
    print("--- Basic Info (Samsung) ---")
    print(collector.get_basic_info("005930"))
    
    print("\n--- Market Environment ---")
    print(collector.get_market_environment())
    
    print("\n--- Minute Candles (Top 5) ---")
    candles = collector.get_minute_candles("005930", count=5)
    print(json.dumps(candles, indent=2))
