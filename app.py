import streamlit as st
import requests
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
from datetime import datetime, timedelta

@st.cache_data
def get_krx_stock_list():
    df = fdr.StockListing('KRX')
    # {종목명: 티커} 형태의 사전 생성 (예: '삼성전자' -> '005930.KS')
    krx_map = {}
    for _, row in df.iterrows():
        market_suffix = ".KQ" if row['Market'] == 'KOSDAQ' else ".KS"
        krx_map[row['Name']] = f"{row['Code']}{market_suffix}"
    return krx_map

# 해외 주요 종목 및 기본 맵핑
OVERSEAS_MAP = {
    "엔비디아": "NVDA", "인텔": "INTC", "애플": "AAPL", "테슬라": "TSLA",
    "마이크로소프트": "MSFT", "구글": "GOOGL", "아마존": "AMZN", "메타": "META",
    "AMD": "AMD", "TSMC": "TSM", "브로드컴": "AVGO", "ASML": "ASML"
}

def get_stock_data(ticker_input, days=30):
    ticker_clean = ticker_input.strip()
    krx_map = get_krx_stock_list()
    
    # 1. 한국 전체 상장 종목 이름 검색
    if ticker_clean in krx_map:
        ticker = krx_map[ticker_clean]
    # 2. 해외 주요 종목 이름 검색
    elif ticker_clean in OVERSEAS_MAP:
        ticker = OVERSEAS_MAP[ticker_clean]
    # 3. 6자리 숫자 코드 입력 시
    elif len(ticker_clean) == 6 and ticker_clean.isdigit():
        ticker = f"{ticker_clean}.KS"
    # 4. 티커 그대로 입력 시 (NVDA, INTC 등)
    else:
        ticker = ticker_clean.upper()
        
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = yf.download(ticker, start=start_date, end=end_date)
    return df, ticker
    
# Page Configuration
st.set_page_config(page_title="AI Hot 뉴스 & 주식 분석 에이전트", page_icon="📈", layout="wide")

# 사이드바: API 키 및 설정
with st.sidebar:
    st.header("⚙️ API 키 설정")
    gemini_key = st.text_input("Gemini API Key", type="password")
    naver_client_id = st.text_input("Naver Client ID", type="password")
    naver_client_secret = st.text_input("Naver Client Secret", type="password")
    st.markdown("---")
    st.caption("Google AI Studio 및 Naver Developers에서 무료로 발급받은 키를 입력하세요.")

# 메인 타이틀
st.title("📈 AI Hot 뉴스 & 글로벌 주식 추천/비교 에이전트")
st.caption("관심 분야를 입력하면 최신 Hot 뉴스 분석, 수혜주 추천, 그리고 라이벌 종목 1:1 비교 분석을 제공합니다.")

# 네이버 뉴스 수집 함수
def get_naver_news(keyword, client_id, client_secret):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {"query": keyword, "display": 15, "sort": "sim"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    return []

# 주가 데이터 가져오기 함수 (yfinance - 한국 주식 자동 보정 포함)
def get_stock_data(ticker, days=30):
    ticker = ticker.strip().upper()
    # 6자리 숫자만 입력된 경우 자동으로 .KS 붙여주기
    if len(ticker) == 6 and ticker.isdigit():
        ticker = f"{ticker}.KS"
        
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = yf.download(ticker, start=start_date, end=end_date)
    return df, ticker
    
# 탭 구성 (4개 탭)
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Hot 이슈 TOP 3", "📊 추천 종목 & 차트", "💬 AI 심층 Q&A", "⚔️ 1:1 라이벌 비교"])

# 사용자 키워드 입력
keyword = st.text_input("관심 분야 또는 키워드를 입력하세요", placeholder="예: 반도체, 2차전지, 로봇, 경제 등")

if st.button("🚀 AI 분석 및 종목 추천 시작", type="primary"):
    if not (gemini_key and naver_client_id and naver_client_secret):
        st.error("사이드바에 모든 API 키를 먼저 입력해 주세요!")
    elif not keyword:
        st.warning("분석할 키워드를 입력해 주세요.")
    else:
        # Gemini API 설정
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        with st.spinner("최신 뉴스를 수집하고 AI가 시장을 분석 중입니다..."):
            news_items = get_naver_news(keyword, naver_client_id, naver_client_secret)
            
            if not news_items:
                st.error("뉴스를 가져오지 못했습니다. API 키나 검색어를 확인해 주세요.")
            else:
                prompt = f"""
                너는 글로벌 IT/금융 전문 AI 에이전트이다.
                제공된 뉴스 데이터를 바탕으로 '{keyword}' 분야의 Hot 이슈와 추천 주식을 분석하라.

                [뉴스 데이터]
                {news_items}

                [출력 형식 - 반드시 마크다운 준수]
                ## 🔥 Hot 이슈 TOP 3
                1. **[이슈 제목]**
                   - **핵심 요약:**
                   - **시장 영향:**
                   - **단기 리스크:**

                ## 🌐 추천 해외 주식 (미국)
                1. **[기업명] (티커: TICKER)**
                   - **수혜 강도:** 🔥🔥🔥
                   - **추천 사유:**
                2. **[기업명] (티커: TICKER)**
                   - **수혜 강도:** 🔥🔥
                   - **추천 사유:**

                ## 🇰🇷 추천 국내 주식 (한국 - 6자리 코드.KS)
                1. **[종목명] (티커: 000000.KS)**
                   - **수혜 강도:** 🔥🔥🔥
                   - **추천 사유:**
                2. **[종목명] (티커: 000000.KS)**
                   - **수혜 강도:** 🔥🔥
                   - **추천 사유:**
                """
                
                response = model.generate_content(prompt)
                st.session_state['analysis_result'] = response.text
                st.success("분석 완료!")

# 결과 출력 (탭 1 & 탭 2)
if 'analysis_result' in st.session_state:
    result_text = st.session_state['analysis_result']
    
    with tab1:
        st.markdown(result_text.split("## 🌐")[0])
        
    with tab2:
        st.markdown("## 🌐 해외 & 국내 추천 종목 및 분석")
        if "## 🌐" in result_text:
            st.markdown("## 🌐" + result_text.split("## 🌐")[1])

with tab3:
    st.subheader("💬 AI 심층 질의응답")
    user_q = st.text_input("추천 종목이나 시장 이슈에 대해 추가로 궁금한 점을 물어보세요.")
    if st.button("질문하기"):
        if gemini_key and 'analysis_result' in st.session_state:
            genai.configure(api_key=gemini_key)
            qa_model = genai.GenerativeModel('gemini-3.5-flash')
            qa_prompt = f"이전 분석 결과:\n{st.session_state['analysis_result']}\n\n사용자 질문: {user_q}"
            qa_res = qa_model.generate_content(qa_prompt)
            st.info(qa_res.text)

# 탭 4: 1:1 라이벌 비교 (기간 선택 기능 추가!)
with tab4:
    st.subheader("⚔️ 종목 1:1 라이벌 비교 분석")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        stock_a_input = st.text_input("종목 A (예: NVDA, 005930 또는 005930.KS)", value="005930.KS")
    with col2:
        stock_b_input = st.text_input("종목 B (예: INTC, 000660 또는 000660.KS)", value="INTC")
    with col3:
        period_option = st.radio("차트 조회 기간", ["30일", "6개월"], index=0)
        days = 30 if period_option == "30일" else 180

    if st.button("1:1 비교 분석 실행"):
        if gemini_key:
            with st.spinner(f"두 종목의 최근 {period_option} 주가 데이터와 AI 비교 평가를 생성 중입니다..."):
                try:
                    # 선택된 기간(days)으로 주가 데이터 조회 (보정된 티커 수신)
                    df_a, stock_a = get_stock_data(stock_a_input, days=days)
                    df_b, stock_b = get_stock_data(stock_b_input, days=days)
                    
                    if df_a.empty or df_b.empty:
                        st.error("종목 데이터를 가져올 수 없습니다. 종목 코드/티커를 다시 확인해 주세요.")
                    else:
                        # 0% 기준 상대 수익률 변동폭 계산
                        close_a = df_a['Close'].squeeze()
                        close_b = df_b['Close'].squeeze()

                        norm_a = (close_a / close_a.iloc[0] - 1) * 100
                        norm_b = (close_b / close_b.iloc[0] - 1) * 100
                        
                        chart_df = pd.DataFrame({
                            stock_a: norm_a,
                            stock_b: norm_b
                        })
                        
                        st.line_chart(chart_df)
                        st.caption(f"※ 최근 {period_option} 상대 수익률 변동폭(%) 비교 차트입니다.")
                        
                        # AI 비교 판정
                        genai.configure(api_key=gemini_key)
                        comp_model = genai.GenerativeModel('gemini-2.5-flash')
                        comp_prompt = f"""
                        두 종목 ({stock_a} vs {stock_b})을 1:1로 비교 분석하라. (최근 {period_option} 추세 반영)
                        - 최근 모멘텀 및 실적 비교
                        - 주요 리스크 요인
                        - 최종 투자 매력도 승자 판정 (종목명 명시) 및 이유 3가지
                        """
                        comp_res = comp_model.generate_content(comp_prompt)
                        st.markdown("---")
                        st.markdown(comp_res.text)
                except Exception as e:
                    st.error(f"주가 데이터 처리 중 오류 발생: {e}")
