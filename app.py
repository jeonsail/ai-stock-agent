import streamlit as st
import requests
import google.generativeai as genai
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

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

# 주가 데이터 가져오기 함수 (yfinance)
def get_stock_data(ticker, days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = yf.download(ticker, start=start_date, end=end_date)
    return df

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
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
            qa_model = genai.GenerativeModel('gemini-1.5-flash')
            qa_prompt = f"이전 분석 결과:\n{st.session_state['analysis_result']}\n\n사용자 질문: {user_q}"
            qa_res = qa_model.generate_content(qa_prompt)
            st.info(qa_res.text)

with tab4:
    st.subheader("⚔️ 종목 1:1 라이벌 비교 분석")
    col1, col2 = st.columns(2)
    with col1:
        stock_a = st.text_input("종목 A (예: NVDA, 005930.KS)", value="005930.KS")
    with col2:
        stock_b = st.text_input("종목 B (예: INTC, 000660.KS)", value="INTC")
        
    if st.button("1:1 비교 분석 실행"):
        if gemini_key:
            with st.spinner("두 종목의 주가 데이터와 AI 비교 평가를 생성 중입니다..."):
                try:
                    # 주가 차트 그리기 (수익률 % 기준)
                    df_a = get_stock_data(stock_a)
                    df_b = get_stock_data(stock_b)
                    
                    norm_a = (df_a['Close'] / df_a['Close'].iloc[0] - 1) * 100
                    norm_b = (df_b['Close'] / df_b['Close'].iloc[0] - 1) * 100
                    
                    chart_df = pd.DataFrame({
                        stock_a: norm_a.iloc[:, 0] if isinstance(norm_a, pd.DataFrame) else norm_a,
                        stock_b: norm_b.iloc[:, 0] if isinstance(norm_b, pd.DataFrame) else norm_b
                    })
                    
                    st.line_chart(chart_df)
                    st.caption("※ 최근 30일 상대 수익률 변동폭(%) 비교 차트입니다.")
                    
                    # AI 비교 판정
                    genai.configure(api_key=gemini_key)
                    comp_model = genai.GenerativeModel('gemini-1.5-flash')
                    comp_prompt = f"""
                    두 종목 ({stock_a} vs {stock_b})을 1:1로 비교 분석하라.
                    - 최근 모멘텀 및 실적 비교
                    - 주요 리스크 요인
                    - 최종 투자 매력도 승자 판정 (종목명 명시) 및 이유 3가지
                    """
                    comp_res = comp_model.generate_content(comp_prompt)
                    st.markdown("---")
                    st.markdown(comp_res.text)
                except Exception as e:
                    st.error(f"주가 데이터 불러오기 실패: 티커 형식을 확인해 주세요. ({e})")
