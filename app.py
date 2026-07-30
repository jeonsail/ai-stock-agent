import streamlit as st
import requests
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="AI Hot 뉴스 & 주식 분석 에이전트", page_icon="📈", layout="wide")

# Streamlit Secrets에서 API 키 자동 로딩
gemini_key = st.secrets.get("GEMINI_KEY", "")
naver_client_id = st.secrets.get("NAVER_CLIENT_ID", "")
naver_client_secret = st.secrets.get("NAVER_CLIENT_SECRET", "")

# 주요 종목 한글-티커 맵핑 테이블 (엔디비아 오타 보정 포함)
STOCK_MAP = {
    # 국내 주요 종목
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS",
    "현대차": "005380.KS", "네이버": "035420.KS", "NAVER": "035420.KS", "카카오": "035720.KS",
    "LG에너지솔루션": "373220.KS", "삼성바이오로직스": "207940.KS", "알테오젠": "196170.KQ",
    "에코프로비엠": "247540.KQ", "에코프로": "086520.KQ", "포스코홀딩스": "005490.KS",
    
    # 해외 주요 종목 (오타 포함)
    "엔비디아": "NVDA", "엔디비아": "NVDA", "인텔": "INTC", "애플": "AAPL", "테슬라": "TSLA",
    "마이크로소프트": "MSFT", "구글": "GOOGL", "알파벳": "GOOGL", "아마존": "AMZN",
    "메타": "META", "AMD": "AMD", "TSMC": "TSM", "브로드컴": "AVGO", "ASML": "ASML",
    "마이크론": "MU", "마이크론 테크놀로지": "MU", "퀄컴": "QCOM"
}

# 주가 데이터 가져오기 및 단방향 Series 변환 함수
def get_stock_data(ticker_input, days=30):
    ticker_clean = ticker_input.strip()
    
    if ticker_clean in STOCK_MAP:
        ticker = STOCK_MAP[ticker_clean]
    elif len(ticker_clean) == 6 and ticker_clean.isdigit():
        ticker = f"{ticker_clean}.KS"
    else:
        ticker = ticker_clean.upper()
        
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # yfinance 데이터 호출
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    # MultiIndex 컬럼일 경우 단순화 처리
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    currency = "원(₩)" if ticker.endswith(".KS") or ticker.endswith(".KQ") else "달러($)"
    return df, ticker, currency

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

# 좌측 사이드바 구성
with st.sidebar:
    st.header("🔍 관심 분야 입력")
    keyword = st.text_input("분석할 키워드를 입력하세요", placeholder="예: 반도체, 2차전지, 로봇 등")
    analyze_btn = st.button("🚀 AI 분석 및 종목 추천 시작", type="primary", use_container_width=True)
    st.markdown("---")
    st.caption("AI가 최신 네이버 뉴스 이슈 분석 및 글로벌 수혜주를 추천해 드립니다.")

# 메인 타이틀
st.title("📈 AI Hot 뉴스 & 글로벌 주식 추천/비교 에이전트")
st.caption("좌측 사이드바에 관심 분야를 입력하면 최신 Hot 뉴스 분석, 수혜주 추천, 그리고 라이벌 종목 1:1 비교 분석을 제공합니다.")

tab1, tab2, tab3, tab4 = st.tabs(["🔥 Hot 이슈 TOP 3", "📊 추천 종목 & 차트", "💬 AI 심층 Q&A", "⚔️ 1:1 라이벌 비교"])

if analyze_btn:
    if not (gemini_key and naver_client_id and naver_client_secret):
        st.error("Streamlit Secrets에 API 키 설정이 필요합니다.")
    elif not keyword:
        st.warning("사이드바에 관심 분야/키워드를 입력해 주세요.")
    else:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        with st.spinner(f"'{keyword}' 관련 최신 뉴스를 수집하고 AI가 시장을 분석 중입니다..."):
            news_items = get_naver_news(keyword, naver_client_id, naver_client_secret)
            
            if not news_items:
                st.error("뉴스를 가져오지 못했습니다. 키워드를 확인해 주세요.")
            else:
                prompt = f"""
                너는 글로벌 IT/금융 전문 AI 에이전트이다.
                제공된 뉴스 데이터를 바탕으로 '{keyword}' 분야의 Hot 이슈와 추천 주식을 분석하라.

                [뉴스 데이터]
                {news_items}

                [출력 절대 규칙 - 필수 준수]
                - 본문 작성 시 굵은 글씨용 별표 기호(**)를 절대 사용하지 마라.
                - 텍스트 강조가 필요하다면 기호 없이 일반 텍스트로 깔끔하게 써라.

                [출력 형식]
                ## 🔥 Hot 이슈 TOP 3
                1. [이슈 제목]
                   - 핵심 요약:
                   - 시장 영향:
                   - 단기 리스크:

                ## 🌐 추천 해외 주식 (미국)
                1. [기업명] (티커: TICKER)
                   - 수혜 강도: 🔥🔥🔥
                   - 추천 사유:
                2. [기업명] (티커: TICKER)
                   - 수혜 강도: 🔥🔥
                   - 추천 사유:

                ## 🇰🇷 추천 국내 주식 (한국)
                1. [종목명] (티커: 000000.KS)
                   - 수혜 강도: 🔥🔥🔥
                   - 추천 사유:
                2. [종목명] (티커: 000000.KS)
                   - 수혜 강도: 🔥🔥
                   - 추천 사유:
                """
                
                response = model.generate_content(prompt)
                st.session_state['analysis_result'] = response.text
                st.success("분석 완료!")

if 'analysis_result' in st.session_state:
    result_text = st.session_state['analysis_result']
    
    with tab1:
        st.markdown(result_text.split("## 🌐")[0])
        
    with tab2:
        st.markdown("## 🌐 해외 & 국내 추천 종목 및 분석")
        if "## 🌐" in result_text:
            st.markdown("## 🌐" + result_text.split("## 🌐")[1])
            
            tickers = re.findall(r'티커:\s*([A-Za-z0-9.]+)', result_text)
            if tickers:
                st.markdown("---")
                st.subheader("📈 추천 종목 최근 30일 주가 봉차트 (Candlestick)")
                chart_cols = st.columns(min(len(tickers), 2))
                for idx, t in enumerate(tickers):
                    with chart_cols[idx % 2]:
                        try:
                            df, valid_ticker, currency = get_stock_data(t, days=30)
                            if not df.empty and all(k in df.columns for k in ['Open', 'High', 'Low', 'Close']):
                                fig = go.Figure(data=[go.Candlestick(
                                    x=df.index,
                                    open=df['Open'],
                                    high=df['High'],
                                    low=df['Low'],
                                    close=df['Close'],
                                    name=valid_ticker
                                )])
                                fig.update_layout(
                                    title=f"{t} ({valid_ticker}) 최근 30일 봉차트 [통화: {currency}]",
                                    yaxis_title=f"주가 ({currency})",
                                    xaxis_rangeslider_visible=False,
                                    margin=dict(l=10, r=10, t=40, b=10),
                                    height=350
                                )
                                # Y축 범위를 주가 변동 폭에 맞게 자동 조정 (0부터 시작 금지)
                                fig.update_yaxes(autorange=True, fixedrange=False)
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.caption(f"{t} 차트 로딩 실패: {e}")

with tab3:
    st.subheader("💬 AI 심층 질의응답")
    user_q = st.text_input("추천 종목이나 시장 이슈에 대해 추가로 궁금한 점을 물어보세요.")
    if st.button("질문하기"):
        if gemini_key and 'analysis_result' in st.session_state:
            genai.configure(api_key=gemini_key)
            qa_model = genai.GenerativeModel('gemini-3.5-flash')
            qa_prompt = f"이전 분석 결과:\n{st.session_state['analysis_result']}\n\n사용자 질문: {user_q}\n(주의: 답변 작성 시 ** 문자를 절대 사용하지 말 것)"
            qa_res = qa_model.generate_content(qa_prompt)
            st.info(qa_res.text)

# 탭 4: 1:1 라이벌 비교
with tab4:
    st.subheader("⚔️ 종목 1:1 라이벌 비교 분석")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        stock_a_input = st.text_input("종목 A (예: 삼성전자, 엔디비아, NVDA)", value="삼성전자")
    with col2:
        stock_b_input = st.text_input("종목 B (예: SK하이닉스, INTC)", value="SK하이닉스")
    with col3:
        period_option = st.radio("차트 조회 기간", ["30일", "6개월"], index=0)
        days = 30 if period_option == "30일" else 180

    if st.button("1:1 비교 분석 실행"):
        if gemini_key:
            with st.spinner(f"두 종목의 최근 {period_option} 주가 데이터와 AI 비교 평가를 생성 중입니다..."):
                try:
                    df_a, stock_a, curr_a = get_stock_data(stock_a_input, days=days)
                    df_b, stock_b, curr_b = get_stock_data(stock_b_input, days=days)
                    
                    if df_a.empty or df_b.empty:
                        st.error("종목 데이터를 가져올 수 없습니다. 입력한 종목명을 다시 확인해 주세요.")
                    else:
                        close_a = df_a['Close']
                        close_b = df_b['Close']

                        # 상대 수익률 변동폭(%) 계산
                        norm_a = (close_a / close_a.iloc[0] - 1) * 100
                        norm_b = (close_b / close_b.iloc[0] - 1) * 100
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_a.index, y=norm_a, mode='lines', name=f"{stock_a_input}({stock_a}) [{curr_a}]"))
                        fig.add_trace(go.Scatter(x=df_b.index, y=norm_b, mode='lines', name=f"{stock_b_input}({stock_b}) [{curr_b}]"))
                        
                        fig.update_layout(
                            title=f"상대 수익률 변동폭(%) 비교 ({period_option})",
                            yaxis_title="수익률 변동폭 (%)",
                            height=400,
                            margin=dict(l=10, r=10, t=40, b=10)
                        )
                        fig.update_yaxes(autorange=True, fixedrange=False)
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption(f"※ 최근 {period_option} 상대 수익률 변동폭(%) 비교 차트입니다. 각 종목의 원본 통화 단위가 표시되어 있습니다.")
                        
                        genai.configure(api_key=gemini_key)
                        comp_model = genai.GenerativeModel('gemini-3.5-flash')
                        comp_prompt = f"""
                        두 종목 ({stock_a_input}({stock_a}, 단치: {curr_a}) vs {stock_b_input}({stock_b}, 단위: {curr_b}))을 1:1로 비교 분석하라. (최근 {period_option} 추세 반영)
                        - 최근 모멘텀 및 실적 비교
                        - 주요 리스크 요인
                        - 최종 투자 매력도 승자 판정 (종목명 명시) 및 이유 3가지
                        
                        (주의: 답변 작성 시 ** 문자를 절대 사용하지 마라)
                        """
                        comp_res = comp_model.generate_content(comp_prompt)
                        st.markdown("---")
                        st.markdown(comp_res.text)
                except Exception as e:
                    st.error(f"주가 데이터 처리 중 오류 발생: {e}")
