import streamlit as st
import json
import os
from naver_collector import NaverFinanceCollector
from ai_formatter import AiFormatter
from datetime import datetime, timedelta, timezone

# 페이지 설정
st.set_page_config(page_title="주도주 종배 분석기", page_icon="📈", layout="centered")

st.title("📈 주도주 종가 배팅 데이터 수집기")
st.markdown("종목 코드를 입력하여 데이터 수집 및 AI 분석용 파일을 생성하세요.")

# 섹션 1: 설정 및 입력
with st.sidebar:
    st.header("설정")
    candle_count = st.slider("수집할 분봉 개수", 50, 1500, 1500)
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

                # 시장 환경 및 뉴스 텍스트 준비
                nasdaq = market_env.get("나스닥", {"price": "N/A", "change_rate": "0.0"})
                kospi200 = market_env.get("코스피200", {"price": "N/A", "change_rate": "0.0"})
                news_text = "\n".join([f"- {n['title']}" for n in news_data])

                # 사용자 정의 지침서 및 AI 출력 가이드 (전체 원문 유지)
                manual_text = r"""너는 이제부터 '냉철한 트레이더' 페르소나로 활동해. 내가 지금부터 주는 **[종가 배팅 의사결정 분석 지침서]**를 완벽히 숙지하고, 내가 종목명을 말하면 이 지침서의 5가지 항목을 아주 깐깐하게 점검해서 리포트를 작성해 줘. 특히 비중 조절에 있어서는 매우 엄격해야 해.

---
📋 **주도주 종가 배팅(종배) 의사결정 및 비중 조절 지침서 (데이터 기반)**

본 지침서는 **'그날 가장 강한 주도주'**를 대상으로 '종가 매수, 익일 시초가 매도' 전략을 수행하기 위한 AI 분석 기준이다. 모든 분석은 제공된 데이터를 기반으로 하며, AI의 주관적 추측이나 상상은 배제한다.

⚠️ **분석 대원칙: 데이터 정합 및 주포 의지 우선 (Data Anchoring & Intent)**
1. **선(先) 가격 확인**: 분석 시작 전, 반드시 해당 종목의 현재가를 먼저 보고하라.
2. **이격도 무시**: 가격이 많이 올랐거나 이격도가 크다는 이유로 비중 점수를 깎지 않는다. 이격도는 강한 수급의 결과일 뿐이다.
3. **주포 이탈 여부 감시**: 주포가 장 막판에 물량을 던지고 나갔는지, 아니면 물량을 잠그고 관리 중인지 분석하는 것이 핵심이다.
4. **수치 증명**: 모든 판단은 구체적 수치(프로그램 순매수 추이, 장 막판 체결 강도, 분봉상 지지 등)에 기반한다.

**1. 지수 선물 (시장 심리 점검)**
- 나스닥 100 선물: -0.7% 이하 급락 시에만 리스크로 비중을 소폭 조절하며, 그 외에는 주도주의 개별 힘을 우선시한다.
- 국내 코스피 200 선물: 장 막판 선물이 밀리더라도 주도주가 신고가 부근에서 가격을 지키면 주포 의지가 강한 것으로 판단한다.

**2. 주포의 최저 방어 가격 (Floor Price) 분석**
- 당일 분봉 차트에서 거래량이 실리며 반복적으로 지지받은 최저 가격대를 추출하라.
- 지지 강도(반등 횟수/거래량 유입)를 평가하고 현재가가 이 가격보다 위에서 관리되는지 확인하라.

**3. 주포의 종가 관리 및 수급 분석**
- 15:00 이후부터 동시호가 전까지 가격이 밀리더라도 방어 가격을 사수하는지 확인하라.
- 동시호가에 매수 잔량이 유입되며 종가를 회복하거나 높게 마무리하는지 확인하라.
- 프로그램 비차익 순매수가 장 막판까지 유지/증가하는지 체크하라.

**4. 수급 주체 및 이탈 여부 (질적 분석)**
- 외인/기관의 매집 지속성을 확인하라. 대량 매도(이탈)가 발생하는지, 개인 매물을 주포가 받아내는지 체크하라.

**5. 차트 및 가격 (기술적 분석 - 주포 관점)**
- 몸통이 전일 고가 위에서 형성되거나, 전고점/저항선을 돌파한 상태로 종가를 형성하는지 확인하라. 이는 내일의 상승 신호다.

**6. 시세 연속성 평가** 
- 현재가가 주포 추정 평단가 대비 과도한 수익 구간인지 확인하라. 
- 만약 고가권임에도 거래량이 터지지 않고 가격이 고정되어 있다면 '물량 잠금(Lock-up)'으로 판단하여 추가 상승에 점수를 주고, 거래량이 터지며 흔들린다면 '수익 실현 시작'으로 보고 비중을 엄격히 제한하라."
---
"""
                report_text = f"""{manual_text}
[분석 대상 데이터]
- 종목: {basic_info['stock_name']} ({stock_code})
- 현재가: {basic_info['close_price']}원 ({basic_info['fluctuation_rate']}%)
- 시장: 나스닥 {nasdaq['price']}({nasdaq['change_rate']}%), 코스피200 {kospi200['price']}({kospi200['change_rate']}%)
- 수급: 외인 {investor_data['foreign_net_buy']}, 기관 {investor_data['institution_net_buy']}, 프로그램 {investor_data['program_net_buy']}
- 뉴스:
{news_text}

[AI 분석용 상세 데이터(JSON)]
{json.dumps(ai_optimized_candles, ensure_ascii=False)}

---
**[AI 리포트 출력 형식]**
(상상을 배제하고 데이터 위주로 보고하라. 0번 항목 누락 시 분석은 무효다.)

**0. 대상 종목 현재가**: [현재가: {basic_info['close_price']}원 / 등락률: {basic_info['fluctuation_rate']}%]
**1. 시장 환경**: (나스닥 선물 및 국내 시장 분위기 요약)
**2. 최저 방어 가격(Floor Price)**: [확인된 방어 가격: OOOO원] (분봉상 반복 지지 구간 근거 제시)
**3. 주포의 종가 관리**: (장 막판 분봉 지지, 프로그램 순매수, 동시호가 수급 상태)
**4. 수급 및 이탈 여부**: (외인/기관 최종 매수 유지 및 대량 체결 특이사항)
**5. 최종 비중 제안**: [추천 비중: OO%]
**6. 대응 전략**: (방어 가격 기준 시나리오 및 손절가 제안)
"""

                # 결과 화면 표시
                st.subheader("📊 분석 요약")
                m1, m2 = st.columns(2)
                m1.metric("현재가", f"{basic_info['close_price']}원", basic_info['fluctuation_rate'] + "%")
                m2.metric("외인 수급", investor_data['foreign_net_buy'])

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
                kst = timezone(timedelta(hours=9))
                file_name = f"analysis_{stock_code}_{datetime.now(kst).strftime('%H%M%S')}.txt"
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


# 깃허브 업로드 위치
# https://github.com/Yangeunho/aver-stock-analysis
