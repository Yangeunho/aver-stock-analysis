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
    candle_count = st.slider("수집할 분봉 개수", 50, 2400, 1500)
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
                    {"list": candles},
                    basic_info['stock_name'],
                    stock_code
                )
                
                # 가공 데이터 추가
                ai_optimized_candles["investor_flow"] = investor_data
                ai_optimized_candles["latest_news"] = [n['title'] for n in news_data]

                # 시장 환경 및 뉴스 텍스트 준비
                nasdaq_f = market_env.get("나스닥100선물", {"price": "N/A", "change_rate": "0.0"})
                snp500_f = market_env.get("S&P500선물", {"price": "N/A", "change_rate": "0.0"})
                vix = market_env.get("VIX공포지수", {"price": "N/A", "change_rate": "0.0"})
                us10y = market_env.get("미국채10년금리", {"price": "N/A", "change_rate": "0.0"})
                kospi200 = market_env.get("코스피200", {"price": "N/A", "change_rate": "0.0"})
                
                market_summary = f"""
- 나스닥100선물: {nasdaq_f['price']} ({nasdaq_f['change_rate']}%)
- S&P500선물: {snp500_f['price']} ({snp500_f['change_rate']}%)
- VIX공포지수: {vix['price']} ({vix['change_rate']}%)
- 미국채10년금리: {us10y['price']} ({us10y['change_rate']}%)
- 코스피200: {kospi200['price']} ({kospi200['change_rate']}%)
"""
                news_text = "\n".join([f"- {n['title']}" for n in news_data])

                # 사용자 정의 지침서 및 AI 출력 가이드 (전체 원문 유지)
                manual_text = r"""너는 이제부터 '냉철한 트레이더' 페르소나로 활동해. 내가 지금부터 주는 **[종가 배팅 의사결정 분석 지침서]**를 완벽히 숙지하고, 내가 종목명을 말하면 이 지침서의 5가지 항목을 아주 깐깐하게 점검해서 리포트를 작성해 줘. 특히 비중 조절에 있어서는 매우 엄격해야 해.

---
📋 **주도주 종가 배팅(종배) 의사결정 및 비중 조절 지침서 (데이터 기반)**

본 지침서는 **'그날 가장 강한 주도주'**를 대상으로 '종가 매수, 익일 시초가 매도' 전략을 수행하기 위한 AI 분석 기준이다. 모든 분석은 제공된 데이터를 기반으로 하며, AI의 주관적 추측이나 상상은 배제한다.

⚠️ **분석 대원칙: 데이터 정합 및 주포 의지 우선 (Data Anchoring & Intent)**
1. **선(先) 가격 확인**: 분석 시작 전, 반드시 해당 종목의 현재가를 먼저 보고하라.
2. **이격도와 수급 밀도의 상관관계 분석**: 가격 과열(이격)이 발생했더라도, 그것이 주포의 강력한 물량 장악에 의한 것인지 아니면 단기 고점의 징후인지를 수급 데이터로 판별하여 비중을 결정하라.
3. **주포 이탈 여부 감시**: 주포가 장 막판에 물량을 던지고 나갔는지, 아니면 물량을 잠그고 관리 중인지 분석하는 것이 핵심이다.
4. **수치 증명**: 모든 판단은 구체적 수치(프로그램 순매수 추이, 장 막판 체결 강도, 분봉상 지지 등)에 기반한다.

**1. 지수 선물 (시장 심리 점검)**
- 나스닥 100 선물: 글로벌 시장의 심리적 위기 수위를 평가하여 비중 조절에 반영하되, 개별 종목의 수급이 시장 환경을 압대할 수 있는지 종합적으로 판단하라.
- 국내 코스피 200 선물: 지수 선물의 변동성 대비 종목의 가격 방어력을 대조하여, 시장 영향력에 굴복하는지 아니면 독자적인 시세를 형성하는 주도적 힘이 있는지 분석하라.

**2. 주포의 핵심 지지 및 방어 가격 분석**
- 당일 분봉 차트에서 대량 거래가 실리며 주포의 의지가 개입된 **핵심 가격대(Critical Level)**를 데이터로 추출하라.
- 단순히 최저가를 찾는 것이 아니라, 가격 방어의 질적 우수성(강력한 눌림목 사수, 추세 유지력 등)을 근거로 현재가가 안전 구역 내에 있는지 판단하라.

**3. 종가 배팅 결정 전 수급 모멘텀 분석 (15:00 ~ 현재 시점)**
- **현재 데이터가 수집된 시점**까지의 프로그램 비차익 순매수 유지력과 가격 방어의 적극성을 입체적으로 판별하라.
- 현재의 수급 가속도를 기반으로 향후 종가가 유리하게 형성될 확률을 예측하고, 현 시점에서의 최종 베팅 여부와 비중을 직접적으로 제안하라.

**4. 수급 주체 및 실시간 이탈 여부 판독**
- 외인/기관의 누적 수급 데이터와 더불어 **현 시점까지의 상대적 변화량**을 대조하여 매집의 가속 혹은 이탈의 징후를 선별하라.
- 단순히 수치적 합계를 확인하는 것이 아니라, 개인의 투매 물량을 주포가 **패시브하게 받아내는지** 혹은 **액티브하게 쓸어담으며** 가격을 견인하는지 수급의 성격을 육안 분석하듯 정밀하게 판독하라.

**5. 기술적 위치 및 가격 프라이싱 분석**
- 현재가가 전일 고가, 주요 저항선, 혹은 신고가 영역 등 **주요 매물대와의 상관관계**에서 어떤 위치에 있는지 분석하라.
- 고정된 해석(상승 신호 등)에 얽매이지 말고, 현재의 가격 위치가 주포의 추가 견인 의지를 보여주는지 아니면 차익 실현을 위한 유인 구간인지를 수급 데이터와 연계하여 중립적으로 판독하라.

**6. 시세 연속성 및 가격 전개 판독**
- 현재 가격이 주요 수급 주체의 평단가 대비 어느 정도의 수익/손실권에 위치하는지 산출하라.
- 고가권에서의 '가격 경직성' 혹은 '변동성 확대' 현상을 단순한 물량 잠금이나 수익 실현으로 단정하지 말고, **거래량 패턴과 체결 강도의 변화**를 통해 주포의 시세 유지 의지를 입체적으로 판별하라. 
- 상승 여력이 남아있는 '건강한 매물 소화'인지, 아니면 상단이 막힌 '분산 과정(Distribution)'인지를 데이터의 분석으로 증명하라."
---
"""
                report_text = f"""{manual_text}
[분석 대상 데이터]
- 종목: {basic_info['stock_name']} ({stock_code})
- 현재가: {basic_info['close_price']}원 ({basic_info['fluctuation_rate']}%)
- 시장 상황: {market_summary}
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
