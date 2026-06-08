# -*- coding: utf-8 -*-
"""
데이터 전처리, 텍스트 분석 및 Plotly 시각화를 담당하는 유틸리티 모듈입니다.
"""

import re
import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

def clean_html_tags(text: str) -> str:
    """
    텍스트 내의 HTML 태그(예: <b>) 및 HTML 엔티티(예: &quot;)를 제거하고 정제합니다.
    """
    if not isinstance(text, str):
        return ""
    # HTML 태그 제거
    clean_text = re.sub(r"<[^>]+>", "", text)
    # HTML 엔티티 복원
    clean_text = html.unescape(clean_text)
    return clean_text

def get_word_frequencies(series: pd.Series, stop_words: list = None) -> pd.DataFrame:
    """
    텍스트 시리즈(예: 제목 리스트)를 입력받아 불용어를 제외한 주요 단어 빈도수를 계산하여 DataFrame으로 반환합니다.
    """
    if stop_words is None:
        stop_words = ["네이버", "검색", "블로그", "카페", "뉴스", "쇼핑", "으로", "에서", "하고", "그리고", "하는", "이다", "있다", "것", "그", "이", "저", "수"]
        
    words = []
    for text in series.dropna():
        cleaned = clean_html_tags(text)
        # 한글, 영문, 숫자 외 문자 제거
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        # 단어 분리 (길이 2 이상인 단어만 수집)
        for word in cleaned.split():
            word_lower = word.lower()
            if len(word_lower) >= 2 and word_lower not in stop_words:
                words.append(word_lower)
                
    counter = Counter(words)
    top_words = counter.most_common(20)
    
    df = pd.DataFrame(top_words, columns=["단어", "빈도수"])
    return df

# --- Plotly 시각화 헬퍼 함수 ---

# 공통 디자인 템플릿 설정 (Dark/Light 모드 모두 어울리는 모던한 스타일)
CHART_LAYOUT_THEME = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Pretendard, Inter, Malgun Gothic, sans-serif"},
    "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
}

COLOR_PALETTE = px.colors.qualitative.Prism  # 세련되고 가독성 높은 현대적인 컬러 파레트

def create_line_chart(df: pd.DataFrame, x_col: str, title: str) -> go.Figure:
    """
    시계열 트렌드 데이터를 위한 모던한 라인 차트를 생성합니다.
    """
    y_cols = [col for col in df.columns if col != x_col]
    
    fig = px.line(
        df, 
        x=x_col, 
        y=y_cols, 
        title=title,
        color_discrete_sequence=COLOR_PALETTE,
        template="plotly_white"
    )
    
    fig.update_layout(**CHART_LAYOUT_THEME)
    fig.update_layout(
        hovermode="x unified",
        legend_title_text="검색어 그룹",
        yaxis_title="상대적 비율 (최대 100)"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(240, 240, 240, 0.8)", gridwidth=1)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(240, 240, 240, 0.8)", gridwidth=1)
    return fig

def create_pie_chart(df: pd.DataFrame, names_col: str, values_col: str, title: str) -> go.Figure:
    """
    비율이나 점유율 분석을 위한 도넛 형태의 파이 차트를 생성합니다.
    """
    fig = px.pie(
        df, 
        names=names_col, 
        values=values_col, 
        title=title,
        hole=0.4,
        color_discrete_sequence=COLOR_PALETTE,
        template="plotly_white"
    )
    fig.update_layout(**CHART_LAYOUT_THEME)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, horizontal: bool = False) -> go.Figure:
    """
    양적 비교를 위한 가로/세로 바 차트를 생성합니다.
    """
    if horizontal:
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col, 
            orientation="h",
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template="plotly_white"
        )
    else:
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col, 
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template="plotly_white"
        )
        
    fig.update_layout(**CHART_LAYOUT_THEME)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(240, 240, 240, 0.8)", gridwidth=1)
    return fig

def create_histogram(df: pd.DataFrame, x_col: str, title: str, nbins: int = 20) -> go.Figure:
    """
    수치형 데이터(예: 가격) 분포 분석을 위한 히스토그램을 생성합니다.
    """
    fig = px.histogram(
        df, 
        x=x_col, 
        nbins=nbins,
        title=title,
        color_discrete_sequence=[COLOR_PALETTE[0]],
        template="plotly_white",
        marginal="box"  # 상단에 상자그림(Box plot) 배치하여 이상치 시각화
    )
    fig.update_layout(**CHART_LAYOUT_THEME)
    fig.update_layout(yaxis_title="빈도수")
    fig.update_xaxes(showgrid=True, gridcolor="rgba(240, 240, 240, 0.8)", gridwidth=1)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(240, 240, 240, 0.8)", gridwidth=1)
    return fig
