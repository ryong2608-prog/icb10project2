# -*- coding: utf-8 -*-
"""
네이버 API 통합 분석 Streamlit 대시보드 메인 애플리케이션
"""

import os
from pathlib import Path

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

# 모듈 임포트
from api import NaverAPIClient
import utils

# Streamlit 설정(secrets)에서 먼저 읽고, 없으면 로컬 .env를 보조로 사용합니다.
def _load_naver_credentials() -> tuple[str, str]:
    try:
        if "NAVER_CLIENT_ID" in st.secrets and "NAVER_CLIENT_SECRET" in st.secrets:
            return (
                str(st.secrets["NAVER_CLIENT_ID"]).strip(),
                str(st.secrets["NAVER_CLIENT_SECRET"]).strip(),
            )

        naver_secret = st.secrets.get("naver", {})
        client_id = str(naver_secret.get("client_id", "")).strip()
        client_secret = str(naver_secret.get("client_secret", "")).strip()
        if client_id and client_secret:
            return client_id, client_secret
    except Exception:
        pass

    return os.getenv("NAVER_CLIENT_ID", "").strip(), os.getenv("NAVER_CLIENT_SECRET", "").strip()

# .env를 여러 후보 경로에서 로드합니다.
APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parent
ENV_CANDIDATES = [
    Path.cwd() / ".env",
    APP_ROOT / ".env",
    REPO_ROOT / ".env",
]
for env_path in ENV_CANDIDATES:
    if env_path.exists():
        load_dotenv(env_path, override=False)

CLIENT_ID, CLIENT_SECRET = _load_naver_credentials()

# --- 페이지 기본 설정 및 디자인 테마 주입 ---
st.set_page_config(
    page_title="네이버 API 통합 데이터 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모던한 Pretendard 폰트 및 카드 UI 스타일 커스텀 CSS 주입
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* 카드 스타일 컨테이너 */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
    }
    .metric-title {
        font-size: 14px;
        color: #888888;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 28px;
        color: #111111;
        font-weight: 700;
    }
    .metric-desc {
        font-size: 12px;
        color: #00c73c;
        margin-top: 4px;
    }
    
    /* 헤더 그라데이션 및 하이라이트 */
    .main-title {
        background: linear-gradient(135deg, #03c75a 0%, #009848 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 40px;
        margin-bottom: 5px;
    }
    .sub-title {
        color: #666666;
        font-size: 16px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- 캐싱을 활용한 API 데이터 로더 구현 ---
@st.cache_data(show_spinner="통합 검색어 트렌드 데이터를 수집하고 있습니다...")
def load_search_trend_data(client_id: str, client_secret: str, start_date: str, end_date: str, 
                           time_unit: str, keywords_str: str, device: str, gender: str, ages_tuple: tuple) -> pd.DataFrame:
    client = NaverAPIClient(client_id, client_secret)
    # 콤마로 구분된 검색어를 그룹으로 매핑
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    keyword_groups = [{"groupName": k, "keywords": [k]} for k in keywords]
    
    ages = list(ages_tuple) if ages_tuple else None
    return client.get_search_trend(start_date, end_date, time_unit, keyword_groups, device, gender, ages)

@st.cache_data(show_spinner="쇼핑 키워드 트렌드 데이터를 수집하고 있습니다...")
def load_shopping_trend_data(client_id: str, client_secret: str, start_date: str, end_date: str, 
                             time_unit: str, category_id: str, keywords_str: str, device: str, gender: str, ages_tuple: tuple) -> pd.DataFrame:
    client = NaverAPIClient(client_id, client_secret)
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    keyword_groups = [{"name": k, "param": [k]} for k in keywords]
    
    ages = list(ages_tuple) if ages_tuple else None
    return client.get_shopping_trend(start_date, end_date, time_unit, category_id, keyword_groups, device, gender, ages)

@st.cache_data(show_spinner="블로그 검색 결과를 분석하고 있습니다...")
def load_blog_data(client_id: str, client_secret: str, query: str, sort: str) -> pd.DataFrame:
    client = NaverAPIClient(client_id, client_secret)
    return client.get_blog_search(query, display=100, sort=sort)

@st.cache_data(show_spinner="뉴스 검색 결과를 분석하고 있습니다...")
def load_news_data(client_id: str, client_secret: str, query: str, sort: str) -> pd.DataFrame:
    client = NaverAPIClient(client_id, client_secret)
    return client.get_news_search(query, display=100, sort=sort)

@st.cache_data(show_spinner="카페글 검색 결과를 분석하고 있습니다...")
def load_cafe_data(client_id: str, client_secret: str, query: str, sort: str) -> pd.DataFrame:
    client = NaverAPIClient(client_id, client_secret)
    return client.get_cafe_search(query, display=100, sort=sort)

@st.cache_data(show_spinner="쇼핑 상품 정보를 분석하고 있습니다...")
def load_shop_data(client_id: str, client_secret: str, query: str, sort: str) -> pd.DataFrame:
    client = NaverAPIClient(client_id, client_secret)
    return client.get_shop_search(query, display=100, sort=sort)

# --- 사이드바 설정 및 입력 조건 ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 대시보드 메뉴")
menu = st.sidebar.selectbox(
    "페이지 선택",
    [
        "통합 검색어 트렌드 (Datalab)",
        "쇼핑 트렌드 (쇼핑인사이트)",
        "블로그 검색 분석",
        "카페글 검색 분석",
        "뉴스 검색 분석",
        "쇼핑 검색 분석"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ 검색 조건 설정")

# 검색어 다중 입력 (콤마로 구분)
default_keywords = "삼성전자, 애플"
keywords_input = st.sidebar.text_input(
    "분석 대상 검색어 (반쉼표 ',' 로 구분)", 
    value=default_keywords, 
    help="여러 검색어 입력 시 콤마로 구분해 주세요. (Datalab 기준 최대 5개)"
)

# 날짜 검색 기간 설정
today = datetime.today()
default_start = today - timedelta(days=90)
start_date = st.sidebar.date_input("조회 시작일", value=default_start, min_value=datetime(2016, 1, 1), max_value=today)
end_date = st.sidebar.date_input("조회 종료일", value=today, min_value=datetime(2016, 1, 1), max_value=today)

# 세부 분석 필터
with st.sidebar.expander("세부 필터 설정"):
    time_unit = st.selectbox("구간 단위", ["date", "week", "month"], index=0)
    device = st.selectbox("기기 구분", ["전체", "pc", "mo"], index=0)
    gender = st.selectbox("성별", ["전체", "m", "f"], index=0)
    
    age_list = st.multiselect(
        "연령대 선택 (다중 선택 가능)",
        options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
        format_func=lambda x: {
            "1": "0~12세", "2": "13~18세", "3": "19~24세", "4": "25~29세",
            "5": "30~34세", "6": "35~39세", "7": "40~44세", "8": "45~49세",
            "9": "50~54세", "10": "55~59세", "11": "60세 이상"
        }[x]
    )

# 사이드바 입력값 정제
device_val = "" if device == "전체" else device
gender_val = "" if gender == "전체" else gender
ages_tuple = tuple(age_list) if age_list else None

# --- 메인 대시보드 영역 ---

if not CLIENT_ID or not CLIENT_SECRET:
    st.markdown('<div class="main-title">Naver API 통합 데이터 대시보드</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">네이버 오픈 API 실시간 트렌드 및 채널별 분석 도구</div>', unsafe_allow_html=True)
    st.error(
        "`st.secrets` 또는 `.env`에서 `NAVER_CLIENT_ID`와 `NAVER_CLIENT_SECRET`을 읽지 못했습니다. "
        "Streamlit Cloud에서는 App > Settings > Secrets에 값을 넣고, 로컬에서는 "
        f"확인한 경로({', '.join(str(path) for path in ENV_CANDIDATES)}) 중 하나에 `.env`를 두세요."
    )
    st.stop()

# API 클라이언트 초기화 및 데이터 로드 영역
keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]

# 화면 헤더 렌더링
st.markdown(f'<div class="main-title">{menu}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">기간: {start_date} ~ {end_date} | 대상 키워드: {", ".join(keywords_list)}</div>', unsafe_allow_html=True)

# ----------------- 1. 통합 검색어 트렌드 (Datalab) -----------------
if menu == "통합 검색어 트렌드 (Datalab)":
    if len(keywords_list) > 5:
        st.error("🚨 통합 검색어 트렌드 API는 최대 5개의 검색어 그룹만 비교 가능합니다. 검색어를 5개 이하로 조정해 주세요.")
        st.stop()
        
    try:
        df_trend = load_search_trend_data(
            CLIENT_ID, CLIENT_SECRET,
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"),
            time_unit, keywords_input, device_val, gender_val, ages_tuple
        )
        
        if df_trend.empty:
            st.info("ℹ️ 조회 기간 및 세부 필터 조건에 해당하는 데이터가 없습니다.")
        else:
            # 1. KPI 카드 (각 키워드별 평균 및 최대 비율)
            st.markdown("### 📊 키워드별 트렌드 핵심 요약 (KPI)")
            kpi_cols = st.columns(len(keywords_list))
            
            for idx, keyword in enumerate(keywords_list):
                if keyword in df_trend.columns:
                    mean_ratio = df_trend[keyword].mean()
                    max_ratio = df_trend[keyword].max()
                    max_date = df_trend.loc[df_trend[keyword].idxmax(), "period"].strftime("%Y-%m-%d")
                    
                    with kpi_cols[idx]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">🔥 {keyword}</div>
                            <div class="metric-value">{mean_ratio:.1f}%</div>
                            <div class="metric-desc">최고 검색일: {max_date} ({max_ratio:.0f}%)</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # 2. 트렌드 차트
            st.markdown("### 📈 시계열 트렌드 시각화")
            fig = utils.create_line_chart(df_trend, "period", "네이버 통합검색 트렌드 추이")
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. 데이터 테이블 및 다운로드
            st.markdown("### 📋 수집된 데이터 테이블")
            st.dataframe(df_trend, use_container_width=True)
            
            # CSV 다운로드
            csv = df_trend.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f"naver_search_trend_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"❌ 데이터 로딩 중 에러가 발생했습니다: {str(e)}")

# ----------------- 2. 쇼핑 트렌드 (쇼핑인사이트) -----------------
elif menu == "쇼핑 트렌드 (쇼핑인사이트)":
    # 네이버 쇼핑 카테고리 매핑 리스트
    categories = {
        "50000000": "패션의류",
        "50000001": "패션잡화",
        "50000002": "화장품/미용",
        "50000003": "디지털/가전",
        "50000004": "가구/인테리어",
        "50000005": "출산/육아",
        "50000006": "식품",
        "50000007": "스포츠/레저",
        "50000008": "생활/건강",
        "50000009": "여가/생활편의",
        "50000010": "면세점"
    }
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 🛒 쇼핑 카테고리")
        selected_cat_id = st.selectbox(
            "카테고리 선택",
            options=list(categories.keys()),
            format_func=lambda x: categories[x]
        )
    
    try:
        df_shop_trend = load_shopping_trend_data(
            CLIENT_ID, CLIENT_SECRET,
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"),
            time_unit, selected_cat_id, keywords_input, device_val, gender_val, ages_tuple
        )
        
        if df_shop_trend.empty:
            st.info("ℹ️ 조회 기간 및 세부 필터 조건에 해당하는 쇼핑 트렌드 데이터가 없습니다.")
        else:
            with col2:
                # 쇼핑 트렌드 차트
                st.markdown("### 📈 쇼핑 키워드 클릭 트렌드 추이")
                fig = utils.create_line_chart(df_shop_trend, "period", f"[{categories[selected_cat_id]}] 카테고리 내 쇼핑 클릭 추이")
                st.plotly_chart(fig, use_container_width=True)
            
            # 요약 분석 통계
            st.markdown("### 📊 키워드별 클릭 비중 통계")
            kpi_cols = st.columns(len(keywords_list))
            for idx, keyword in enumerate(keywords_list):
                if keyword in df_shop_trend.columns:
                    mean_val = df_shop_trend[keyword].mean()
                    max_val = df_shop_trend[keyword].max()
                    max_date = df_shop_trend.loc[df_shop_trend[keyword].idxmax(), "period"].strftime("%Y-%m-%d")
                    
                    with kpi_cols[idx]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">🛍️ {keyword}</div>
                            <div class="metric-value">{mean_val:.1f}%</div>
                            <div class="metric-desc">최고 클릭일: {max_date} ({max_val:.0f}%)</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("### 📋 수집된 데이터 테이블")
            st.dataframe(df_shop_trend, use_container_width=True)
            
            # CSV 다운로드
            csv = df_shop_trend.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 쇼핑 트렌드 데이터 다운로드 (CSV)",
                data=csv,
                file_name=f"naver_shopping_trend_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"❌ 쇼핑 트렌드 데이터 로딩 중 에러가 발생했습니다: {str(e)}")

# ----------------- 3. 블로그 검색 분석 -----------------
elif menu == "블로그 검색 분석":
    sort_option = st.selectbox("정렬 기준", ["sim (정확도순)", "date (최신순)"], format_func=lambda x: x.split()[0])
    
    # 여러 검색어인 경우 각 검색어별로 분석할 수 있도록 탭으로 제공
    tabs = st.tabs([f"📝 {k}" for k in keywords_list])
    
    for idx, tab in enumerate(tabs):
        keyword = keywords_list[idx]
        with tab:
            try:
                df_blog = load_blog_data(CLIENT_ID, CLIENT_SECRET, keyword, sort_option.split()[0])
                
                if df_blog.empty:
                    st.info(f"ℹ️ '{keyword}'에 대한 블로그 검색 결과가 없습니다.")
                    continue
                
                # 블로그 이름 전처리
                df_blog["cafename_cleaned"] = df_blog["bloggername"].apply(utils.clean_html_tags)
                
                # 시각화 데이터 생성
                blog_counts = df_blog["cafename_cleaned"].value_counts().reset_index()
                blog_counts.columns = ["블로그명", "발행 글 수"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📊 글을 많이 발행한 블로그 (Top 10)")
                    fig = utils.create_bar_chart(blog_counts.head(10), "발행 글 수", "블로그명", "블로그 점유율", horizontal=True)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("### 🔤 빈번하게 나타난 키워드 (Top 15)")
                    df_words = utils.get_word_frequencies(df_blog["title"] + " " + df_blog["description"])
                    fig = utils.create_bar_chart(df_words.head(15), "단어", "빈도수", "주요 키워드 빈도")
                    st.plotly_chart(fig, use_container_width=True)
                
                # 원본 글 보기 리스트
                st.markdown("### 📋 수집된 최근 블로그 글 (최대 100개)")
                for _, row in df_blog.iterrows():
                    title_cleaned = utils.clean_html_tags(row["title"])
                    desc_cleaned = utils.clean_html_tags(row["description"])
                    post_date = row.get("postdate", "")
                    
                    if post_date:
                        post_date = f" | {post_date[:4]}-{post_date[4:6]}-{post_date[6:]}"
                    
                    with st.expander(f"{title_cleaned} (블로그: {row['cafename_cleaned']}{post_date})"):
                        st.write(desc_cleaned)
                        st.markdown(f"[🔗 블로그 원본 글 보기]({row['link']})")
                        
            except Exception as e:
                st.error(f"❌ '{keyword}' 블로그 데이터 로딩 중 에러: {str(e)}")

# ----------------- 4. 카페글 검색 분석 -----------------
elif menu == "카페글 검색 분석":
    sort_option = st.selectbox("정렬 기준", ["sim (정확도순)", "date (최신순)"], format_func=lambda x: x.split()[0])
    
    tabs = st.tabs([f"☕ {k}" for k in keywords_list])
    
    for idx, tab in enumerate(tabs):
        keyword = keywords_list[idx]
        with tab:
            try:
                df_cafe = load_cafe_data(CLIENT_ID, CLIENT_SECRET, keyword, sort_option.split()[0])
                
                if df_cafe.empty:
                    st.info(f"ℹ️ '{keyword}'에 대한 카페글 검색 결과가 없습니다.")
                    continue
                
                # 카페 이름 전처리
                df_cafe["cafename_cleaned"] = df_cafe["cafename"].apply(utils.clean_html_tags)
                
                # 카페별 점유율
                cafe_counts = df_cafe["cafename_cleaned"].value_counts().reset_index()
                cafe_counts.columns = ["카페명", "게시글 수"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📊 주요 커뮤니티(카페) 점유율")
                    fig = utils.create_pie_chart(cafe_counts.head(10), "카페명", "게시글 수", "상위 10개 카페 분포")
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col2:
                    st.markdown("### 🔤 주요 키워드 빈도 분석")
                    df_words = utils.get_word_frequencies(df_cafe["title"] + " " + df_cafe["description"])
                    fig = utils.create_bar_chart(df_words.head(15), "단어", "빈도수", "가장 많이 사용된 단어")
                    st.plotly_chart(fig, use_container_width=True)
                
                # 리스트 테이블 렌더링
                st.markdown("### 📋 최근 카페 게시글")
                for _, row in df_cafe.iterrows():
                    title_cleaned = utils.clean_html_tags(row["title"])
                    desc_cleaned = utils.clean_html_tags(row["description"])
                    
                    with st.expander(f"{title_cleaned} (카페: {row['cafename_cleaned']})"):
                        st.write(desc_cleaned)
                        st.markdown(f"[🔗 카페글 원본 보기]({row['link']})")
                        
            except Exception as e:
                st.error(f"❌ '{keyword}' 카페 데이터 로딩 중 에러: {str(e)}")

# ----------------- 5. 뉴스 검색 분석 -----------------
elif menu == "뉴스 검색 분석":
    sort_option = st.selectbox("정렬 기준", ["sim (정확도순)", "date (최신순)"], format_func=lambda x: x.split()[0])
    
    tabs = st.tabs([f"📰 {k}" for k in keywords_list])
    
    for idx, tab in enumerate(tabs):
        keyword = keywords_list[idx]
        with tab:
            try:
                df_news = load_news_data(CLIENT_ID, CLIENT_SECRET, keyword, sort_option.split()[0])
                
                if df_news.empty:
                    st.info(f"ℹ️ '{keyword}'에 대한 뉴스 검색 결과가 없습니다.")
                    continue
                
                # 링크 도메인을 기반으로 임의로 언론사명 파싱
                def parse_domain(url):
                    try:
                        domain = urlparse(url).netloc
                        # 일부 도메인 매핑 처리
                        mapping = {
                            "n.news.naver.com": "네이버뉴스",
                            "www.yna.co.kr": "연합뉴스",
                            "news.naver.com": "네이버뉴스",
                            "sports.news.naver.com": "네이버스포츠",
                            "www.hankyung.com": "한국경제",
                            "www.mk.co.kr": "매일경제",
                            "biz.chosun.com": "조선비즈",
                            "www.chosun.com": "조선일보",
                            "www.donga.com": "동아일보",
                            "www.joongang.co.kr": "중앙일보",
                            "www.seoul.co.kr": "서울신문",
                            "www.khan.co.kr": "경향신문",
                            "www.hani.co.kr": "한겨레",
                            "www.sedaily.com": "서울경제",
                            "www.moneytoday.co.kr": "머니투데이"
                        }
                        return mapping.get(domain, domain.replace("www.", ""))
                    except:
                        return "기타 언론사"
                
                df_news["언론사"] = df_news["originallink"].apply(parse_domain)
                
                # 1. 언론사 점유율
                news_counts = df_news["언론사"].value_counts().reset_index()
                news_counts.columns = ["언론사", "기사 수"]
                
                # 2. 일자별 발행 추이 (pubDate 파싱)
                def parse_pubdate(pub_date_str):
                    try:
                        # RFC 822 날짜 포맷 예시: Tue, 04 Oct 2016 13:23:58 +0900
                        return pd.to_datetime(pub_date_str).strftime("%Y-%m-%d")
                    except:
                        return "날짜 분석 불가"
                
                df_news["발행일자"] = df_news["pubDate"].apply(parse_pubdate)
                date_counts = df_news[df_news["발행일자"] != "날짜 분석 불가"]["발행일자"].value_counts().reset_index()
                date_counts.columns = ["발행일자", "기사 수"]
                date_counts = date_counts.sort_values("발행일자")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📊 주요 보도 언론사 점유율")
                    fig = utils.create_pie_chart(news_counts.head(10), "언론사", "기사 수", "상위 10개 언론사 분포")
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col2:
                    st.markdown("### 📈 최근 일별 뉴스 발행 추이")
                    if not date_counts.empty:
                        fig = utils.create_line_chart(date_counts, "발행일자", "일별 기사 발행 건수")
                        fig.update_layout(yaxis_title="보도 건수")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ 뉴스 날짜 정보가 부족하여 발행 추이를 그릴 수 없습니다.")
                
                # 기사 리스트
                st.markdown("### 📋 최근 보도 기사 리스트")
                for _, row in df_news.iterrows():
                    title_cleaned = utils.clean_html_tags(row["title"])
                    desc_cleaned = utils.clean_html_tags(row["description"])
                    
                    with st.expander(f"{title_cleaned} ({row['언론사']} | {row['pubDate']})"):
                        st.write(desc_cleaned)
                        st.markdown(f"[🔗 뉴스 원본 기사]({row['originallink']})")
                        if row['link']:
                            st.markdown(f"[🔗 네이버 뉴스 링크]({row['link']})")
                            
            except Exception as e:
                st.error(f"❌ '{keyword}' 뉴스 데이터 로딩 중 에러: {str(e)}")

# ----------------- 6. 쇼핑 검색 분석 -----------------
elif menu == "쇼핑 검색 분석":
    sort_option = st.selectbox(
        "정렬 기준", 
        ["sim (정확도순)", "date (신상품순)", "asc (낮은가격순)", "dsc (높은가격순)"], 
        format_func=lambda x: x.split()[0]
    )
    
    tabs = st.tabs([f"🛍️ {k}" for k in keywords_list])
    
    for idx, tab in enumerate(tabs):
        keyword = keywords_list[idx]
        with tab:
            try:
                df_shop = load_shop_data(CLIENT_ID, CLIENT_SECRET, keyword, sort_option.split()[0])
                
                if df_shop.empty:
                    st.info(f"ℹ️ '{keyword}'에 대한 쇼핑 검색 결과가 없습니다.")
                    continue
                
                # 수치형 변환
                df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors="coerce").fillna(0)
                df_shop["hprice"] = pd.to_numeric(df_shop["hprice"], errors="coerce").fillna(0)
                
                # 가격 통계 정보 계산
                valid_prices = df_shop[df_shop["lprice"] > 0]["lprice"]
                if not valid_prices.empty:
                    min_price = valid_prices.min()
                    max_price = valid_prices.max()
                    avg_price = valid_prices.mean()
                else:
                    min_price = max_price = avg_price = 0
                
                # KPI 카드 노출
                kpi1, kpi2, kpi3 = st.columns(3)
                with kpi1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">🏷️ 평균 최저가 가격</div>
                        <div class="metric-value">₩{avg_price:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with kpi2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📉 최저 가격</div>
                        <div class="metric-value">₩{min_price:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with kpi3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📈 최고 가격</div>
                        <div class="metric-value">₩{max_price:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 차트 분석
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📊 상품 가격 분포")
                    if not valid_prices.empty:
                        fig = utils.create_histogram(df_shop[df_shop["lprice"] > 0], "lprice", "상품 최저가 가격대 분포")
                        fig.update_layout(xaxis_title="가격(원)")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ 유효한 가격 정보가 없습니다.")
                        
                with col2:
                    st.markdown("### 🏬 입점 쇼핑몰 점유율 (Top 10)")
                    mall_counts = df_shop["mallName"].value_counts().reset_index()
                    mall_counts.columns = ["쇼핑몰", "상품 수"]
                    fig = utils.create_pie_chart(mall_counts.head(10), "쇼핑몰", "상품 수", "상위 10개 쇼핑몰 분포")
                    st.plotly_chart(fig, use_container_width=True)
                
                # 브랜드 및 제조사 분석
                col3, col4 = st.columns(2)
                with col3:
                    st.markdown("### 🏷️ 브랜드 점유율 (Top 7)")
                    brand_counts = df_shop[df_shop["brand"] != ""]["brand"].value_counts().reset_index()
                    if not brand_counts.empty:
                        brand_counts.columns = ["브랜드", "상품 수"]
                        fig = utils.create_bar_chart(brand_counts.head(7), "상품 수", "브랜드", "브랜드별 비중", horizontal=True)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ 브랜드 정보가 기재된 상품이 없습니다.")
                        
                with col4:
                    st.markdown("### 🏭 제조사 점유율 (Top 7)")
                    maker_counts = df_shop[df_shop["maker"] != ""]["maker"].value_counts().reset_index()
                    if not maker_counts.empty:
                        maker_counts.columns = ["제조사", "상품 수"]
                        fig = utils.create_bar_chart(maker_counts.head(7), "상품 수", "제조사", "제조사별 비중", horizontal=True)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ 제조사 정보가 기재된 상품이 없습니다.")
                
                # 상품 카드형 렌더링
                st.markdown("### 📋 쇼핑 상품 목록 (최대 100개)")
                
                # Grid 형태로 배치 (한 줄에 4개씩)
                items = df_shop.to_dict('records')
                num_cols = 4
                for i in range(0, len(items), num_cols):
                    cols = st.columns(num_cols)
                    for j in range(num_cols):
                        if i + j < len(items):
                            item = items[i + j]
                            title_cleaned = utils.clean_html_tags(item["title"])
                            price_formatted = f"₩{int(item['lprice']):,}" if item['lprice'] > 0 else "가격 정보 없음"
                            
                            with cols[j]:
                                # 이미지 출력 (이미지가 없거나 깨진 주소일 때 예외 방지)
                                if item.get("image"):
                                    st.image(item["image"], use_container_width=True)
                                else:
                                    st.write("📷 이미지 준비중")
                                    
                                st.markdown(f"**[{item['mallName']}]** {title_cleaned}")
                                st.markdown(f"<span style='color:#f39c12; font-weight:bold;'>{price_formatted}</span>", unsafe_allow_html=True)
                                if item.get("brand"):
                                    st.markdown(f"*{item['brand']}*")
                                st.markdown(f"[🔗 상품 구매하러 가기]({item['link']})")
                                st.markdown("---")
                                
            except Exception as e:
                st.error(f"❌ '{keyword}' 쇼핑 데이터 로딩 중 에러: {str(e)}")
