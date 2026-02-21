import requests
import json
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd

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
        """지수 정보(나스닥, 코스피200 등) 조회"""
        indices = {}
        # 1. 코스피 200
        try:
            url = "https://polling.finance.naver.com/api/realtime?query=SERVICE_INDEX:KPI200"
            res = requests.get(url, headers=self.headers)
            item = res.json()["result"]["areas"][0]["datas"][0]
            indices["코스피200"] = {"price": str(item["nv"]), "change_rate": str(item["cr"])}
        except: pass

        # 2. 나스닥 (종합지수)
        try:
            url = "https://polling.finance.naver.com/api/realtime?query=SERVICE_WORLD:.IXIC"
            res = requests.get(url, headers=self.headers)
            item = res.json()["result"]["areas"][0]["datas"][0]
            indices["나스닥"] = {"price": str(item["nv"]), "change_rate": str(item["cr"])}
        except: pass
            
        return indices

    def get_investor_data(self, stock_code):
        """외인/기관/프로그램 순매수 데이터 스캔"""
        from bs4 import BeautifulSoup
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
        from bs4 import BeautifulSoup
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

    def get_minute_candles(self, stock_code, count=100):
        """분봉 데이터 조회 (XML API 활용)"""
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={stock_code}&timeframe=minute&count={count}&requestType=0"
        try:
            res = requests.get(url, headers=self.headers)
            root = ET.fromstring(res.text)
            candles = []
            for item in root.findall(".//item"):
                data = item.get("data").split("|")
                def clean_int(val):
                    if not val or val.lower() == 'null': return 0
                    return int(val)
                c = clean_int(data[4])
                o = clean_int(data[1])
                h = clean_int(data[2])
                l = clean_int(data[3])
                v = clean_int(data[5])
                if o == 0: o = c
                if h == 0: h = c
                if l == 0: l = c
                candles.append({
                    "time": data[0],
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": v,
                    "amount": c * v  # 거래대금 (종가 * 거래량 근사치)
                })
            return candles
        except:
            return []
