import streamlit as st
import json
import os
from naver_collector import NaverFinanceCollector
from ai_formatter import AiFormatter
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="주도주 종배 분석기", page_icon="📈", layout="centered")

st.title("📈 주도주 종가 배팅 데이터 수집기")
st.markdown("종목 코드를 입력하여 데이터 수집 및 AI 분석용 파일을 생성하세요.")

# 섹션 1: 설정 및 입력
with st.sidebar:
    st.header("설정")
    candle_count = st.slider("수집할 분봉 개수", 50, 500, 100)
    st.info("Tip: 핸드폰에서 접속 중이라면 PC의 IP 주소로 접속하세요.")

stock_code = st.text_input("종목 코드 입력 (예: 032820, 005930)", placeholder="6자리 숫자 입력")

if st.button("🚀 데이터 수집 및 보고서 생성"):
    if not stock_code or len(stock_code) != 6:
        st.error("올바른 종목 코드 6자리를 입력해주세요.")
    else:
        with st.spinner(f"[{stock_code}] 데이터를 네이버에서 가져오는 중..."):
            collector = NaverFinanceCollector()
            basic_info = collector.get_basic_info(stock_code)
            market_env = collector.get_market_environment()
            investor_data = collector.get_investor_data(stock_code)
            news_data = collector.get_related_news(stock_code)
            candles = collector.get_minute_candles(stock_code, count=candle_count)

            if not basic_info or not candles:
                st.error("데이터 수집에 실패했습니다. 종목 코드를 확인해주세요.")
            else:
                st.success(f"{basic_info['stock_name']} 데이터 수집 완료!")
                
                # Floor Price 계산
                lows = [c['low'] for c in candles if c['low'] > 0]
                floor_price = min(lows) if lows else 0
                
                # AI 포맷팅
                formatter = AiFormatter()
                ai_optimized_candles = formatter.format_minute_data(
                    {"list": [
                        {
                            "stck_cntg_hour": c['time'][-6:],
                            "stck_prpr": str(c['close']),
                            "stck_oprc": str(c['open']),
                            "stck_hgpr": str(c['high']),
                            "stck_lwpr": str(c['low']),
                            "cntg_vol": str(c['volume']),
                            "cntg_amt": str(c.get('amount', 0)) # 거래대금 추가
                        } for c in candles
                    ]},
                    basic_info['stock_name'],
                    stock_code
                )
                
                # 가공 데이터 추가
                ai_optimized_candles["investor_flow"] = investor_data
                ai_optimized_candles["latest_news"] = [n['title'] for n in news_data]

                # 보고서 텍스트 생성
                nasdaq = market_env.get("나스닥", {"price": "N/A", "change_rate": "0.0"})
                kospi200 = market_env.get("코스피200", {"price": "N/A", "change_rate": "0.0"})
                current_p = int(basic_info['close_price'].replace(',','')) if basic_info['close_price'] else 0
                diff_from_floor = ((current_p - floor_price) / floor_price * 100) if floor_price > 0 else 0

                news_text = "\n".join([f"- {n['title']}" for n in news_data])
                report_text = f"""# **📋 주도주 종가 배팅(종배) 분석 보고서**
0. 대상 종목: {basic_info['stock_name']} ({stock_code})
1. 현재가: {basic_info['close_price']}원 ({basic_info['fluctuation_rate']}%)
2. 시장 환경:
   - 나스닥: {nasdaq['price']} ({nasdaq['change_rate']}%)
   - 코스피200: {kospi200['price']} ({kospi200['change_rate']}%)
3. 수급 상황:
   - 외인 순매수: {investor_data['foreign_net_buy']}
   - 기관 순매수: {investor_data['institution_net_buy']}
   - 프로그램: {investor_data['program_net_buy']}
4. 최신 뉴스:
{news_text}
5. 최저 방어 가격: {floor_price}원 (현재가 대비 {diff_from_floor:.2f}% 차이)
---
[AI 분석용 데이터]
{json.dumps(ai_optimized_candles, ensure_ascii=False)}
"""

                # 결과 화면 표시
                st.subheader("📊 분석 요약")
                m1, m2, m3 = st.columns(3)
                m1.metric("현재가", f"{basic_info['close_price']}원", basic_info['fluctuation_rate'] + "%")
                m2.metric("방어 가격(Floor)", f"{floor_price}원", f"{diff_from_floor:.2f}%")
                m3.metric("외인 수급", investor_data['foreign_net_buy'])

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🏦 수급 현황")
                    st.write(f"**기관:** {investor_data['institution_net_buy']}")
                    st.write(f"**프로그램:** {investor_data['program_net_buy']}")
                with col2:
                    st.subheader("📰 최신 뉴스")
                    for n in news_data[:3]:
                        st.write(f"[{n['title']}]({n['link']})")

                st.text_area("보고서 전문 (제미나이 복사용)", report_text, height=250)

                # 파일 다운로드 버튼 (핸드폰 첨부용)
                file_name = f"analysis_{stock_code}_{datetime.now().strftime('%H%M%S')}.txt"
                st.download_button(
                    label="💾 제미나이 첨부용 파일 다운로드",
                    data=report_text,
                    file_name=file_name,
                    mime="text/plain"
                )

                st.info("💡 위 파일을 다운로드하여 제미나이 대화창에 첨본 뒤 분석을 요청하세요.")

# 하단 정보
st.divider()
st.caption("본 프로그램은 네이버 증권의 공개 데이터를 활용합니다. 실제 투자 책임은 본인에게 있습니다.")
