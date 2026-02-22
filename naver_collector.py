import requests
import json
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup

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
            item = data.get("result", {}).get("areas", [])[0].get("datas", [])[0]
            return {
                "stock_name": item.get("nm"),
                "close_price": str(item.get("nv")),
                "fluctuation_rate": str(item.get("cr")),
            }
        except Exception as e:
            print(f"Error fetching basic info: {e}")
            return None

    def get_market_environment(self):
        """지수 정보(나스닥 선물, VIX, 국채금리 등) 조회"""
        indices = {}
        
        # 수집 대상 목록 (이름: (심볼, 서비스타입))
        targets = {
            "코스피200": ("KPI200", "SERVICE_INDEX"),
            "나스닥100선물": ("NAS@NQcv1", "SERVICE_WORLD"),
            "S&P500선물": ("SPI@SPcv1", "SERVICE_WORLD"),
            "VIX공포지수": (".VIX", "SERVICE_WORLD"),
            "미국채10년금리": ("US10Y", "SERVICE_WORLD"),
            "나스닥지수": (".IXIC", "SERVICE_WORLD")
        }

        for name, (symbol, service) in targets.items():
            try:
                # 1. 실시간 API 시도
                url = f"https://polling.finance.naver.com/api/realtime?query={service}:{symbol}"
                res = requests.get(url, headers=self.headers, timeout=5)
                res_json = res.json()
                
                # 데이터 존재 여부 체크
                areas = res_json.get("result", {}).get("areas", [])
                if areas and len(areas) > 0:
                    data = areas[0].get("datas", [])[0]
                    if data.get("nv") and data.get("nv") != 0:
                        indices[name] = {"price": str(data["nv"]), "change_rate": str(data["cr"])}
                        continue

                # 2. API 데이터가 없거나 실패 시 웹 크롤링 시도 (해외 지표)
                if service == "SERVICE_WORLD":
                    url = f"https://finance.naver.com/world/sise.naver?symbol={symbol}"
                    res = requests.get(url, headers=self.headers, timeout=5)
                    price_match = re.search(r'item_chart_price">([\d,.]+)', res.text)
                    rate_match = re.search(r'rate">([\d.+-]+)%', res.text)
                    if price_match:
                        indices[name] = {
                            "price": price_match.group(1).replace(",", ""),
                            "change_rate": rate_match.group(1) if rate_match else "0.0"
                        }
            except: pass
            
            if name not in indices:
                # 현재 시간이 일요일인 경우 휴장 메시지 우선
                if datetime.now().weekday() == 6: # Sunday
                    indices[name] = {"price": "시장휴장", "change_rate": "0.0"}
                else:
                    indices[name] = {"price": "N/A", "change_rate": "0.0"}
            
        return indices

    def get_investor_data(self, stock_code):
        """외인/기관/프로그램 순매수 데이터 스캔"""
        data = {"foreign_net_buy": "N/A", "institution_net_buy": "N/A", "program_net_buy": "N/A"}
        
        # 1. 외인/기관
        try:
            url = f"https://finance.naver.com/item/frgn.naver?code={stock_code}"
            res = requests.get(url, headers=self.headers)
            if res.encoding == 'ISO-8859-1': res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select("table.type2 tr")
            for row in rows:
                cols = row.select("td")
                if len(cols) >= 9:
                    data["foreign_net_buy"] = cols[6].text.strip()
                    data["institution_net_buy"] = cols[5].text.strip()
                    break
        except: pass

        # 2. 프로그램
        try:
            url = f"https://finance.naver.com/item/sise.naver?code={stock_code}"
            res = requests.get(url, headers=self.headers)
            if res.encoding == 'ISO-8859-1': res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            prog_label = soup.find(string=re.compile("프로그램"))
            if prog_label:
                prog_val = prog_label.find_parent("tr").select("td")[-1]
                data["program_net_buy"] = prog_val.text.strip()
        except: pass

        return data

    def get_related_news(self, stock_code):
        """종목 관련 뉴스 스크래핑 (최신 5건)"""
        news_list = []
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
        try:
            res = requests.get(url, headers=self.headers)
            if res.encoding == 'ISO-8859-1': res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            # '뉴스' 섹션 내의 링크들 탐색
            news_area = soup.find('div', class_='section news_area')
            if news_area:
                for a in news_area.select('li span a'):
                    title = a.text.strip()
                    if title:
                        news_list.append({
                            "title": title,
                            "link": "https://finance.naver.com" + a['href']
                        })
            if not news_list:
                for a in soup.select('div.news_section ul li a'):
                    title = a.text.strip()
                    if title:
                        news_list.append({
                            "title": title,
                            "link": "https://finance.naver.com" + a['href']
                        })
        except: pass
        return news_list[:5]

    def get_minute_candles(self, stock_code, count=1500):
        """분봉 데이터 조회 (XML API 활용)"""
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={stock_code}&timeframe=minute&count={count}&requestType=0"
        try:
            res = requests.get(url, headers=self.headers)
            root = ET.fromstring(res.text)
            candles = []
            
            # 이전 누적 거래량 및 날짜 초기화 (명시적 사용)
            prev_v = 0
            prev_date = None
            
            def clean_int(val):
                if not val or val.lower() == 'null': return 0
                return int(val)
            
            for item in root.findall(".//item"):
                data = item.get("data").split("|")
                c = clean_int(data[4])
                o = clean_int(data[1])
                h = clean_int(data[2])
                l = clean_int(data[3])
                v_raw = clean_int(data[5])
                
                # 순 거래량 계산 (누적 -> 분당 순증가분)
                # 이전 데이터와 같은 날짜인 경우에만 차이를 구함 (날짜 바뀌면 누적치가 리셋됨)
                curr_date = data[0][:8]
                if prev_date is not None and curr_date == prev_date:
                    v_pure = max(0, v_raw - prev_v)
                else:
                    v_pure = v_raw
                
                prev_v = v_raw
                prev_date = curr_date

                if o == 0: o = c
                if h == 0: h = c
                if l == 0: l = c
                candles.append({
                    "time": data[0],
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": v_pure,
                    "amount": c * v_pure  # 실제 분당 순 거래대금
                })
            return candles[-count:]
        except:
            return []
