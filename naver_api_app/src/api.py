# -*- coding: utf-8 -*-
"""
네이버 오픈 API 통신 및 데이터 정규화를 담당하는 모듈입니다.
"""

import urllib.request
import json
import pandas as pd
import requests

class NaverAPIClient:
    """
    네이버 API와 통신하기 위한 클라이언트 클래스
    """
    def __init__(self, client_id: str, client_secret: str):
        """
        API 키 및 헤더 정보 설정
        """
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json"
        }

    def _call_api_post(self, url: str, json_data: dict) -> dict:
        """
        POST API 공통 호출 헬퍼 (Datalab 계열)
        """
        try:
            response = requests.post(url, headers=self.headers, json=json_data, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API 호출 실패 (상태 코드: {response.status_code}): {response.text}")
        except Exception as e:
            raise Exception(f"네트워크 오류 또는 API 에러: {str(e)}")

    def _call_api_get(self, url: str, params: dict) -> dict:
        """
        GET API 공통 호출 헬퍼 (검색 계열)
        """
        try:
            # GET 요청의 경우 Content-Type 헤더가 JSON이면 오류를 낼 수 있으므로 복사해서 Content-Type을 지움
            headers = self.headers.copy()
            if "Content-Type" in headers:
                del headers["Content-Type"]
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API 호출 실패 (상태 코드: {response.status_code}): {response.text}")
        except Exception as e:
            raise Exception(f"네트워크 오류 또는 API 에러: {str(e)}")

    def get_search_trend(self, start_date: str, end_date: str, time_unit: str, 
                         keyword_groups: list, device: str = "", gender: str = "", ages: list = None) -> pd.DataFrame:
        """
        네이버 통합 검색어 트렌드 데이터를 가져와서 DataFrame으로 변환합니다.
        
        :param keyword_groups: [{'groupName': '그룹명', 'keywords': ['키워드1', '키워드2']}] 형식의 리스트
        """
        url = "https://openapi.naver.com/v1/datalab/search"
        
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups
        }
        
        if device:
            body["device"] = device
        if gender:
            body["gender"] = gender
        if ages:
            body["ages"] = ages

        data = self._call_api_post(url, body)
        
        # 데이터프레임으로 파싱
        # 여러 그룹의 데이터를 하나의 테이블로 합칩니다.
        results = data.get("results", [])
        if not results:
            return pd.DataFrame()
            
        dfs = []
        for group in results:
            group_name = group["title"]
            group_data = group.get("data", [])
            
            if not group_data:
                continue
                
            df = pd.DataFrame(group_data)
            # ratio 컬럼명을 group_name으로 변경
            df = df.rename(columns={"ratio": group_name})
            df["period"] = pd.to_datetime(df["period"])
            df = df.set_index("period")
            dfs.append(df)
            
        if not dfs:
            return pd.DataFrame()
            
        # 모든 데이터프레임을 period(index) 기준으로 아우터 조인
        final_df = dfs[0]
        for df in dfs[1:]:
            final_df = final_df.join(df, how="outer")
            
        # 인덱스를 다시 컬럼으로 빼고 정렬
        final_df = final_df.reset_index().sort_values("period")
        return final_df

    def get_shopping_trend(self, start_date: str, end_date: str, time_unit: str, 
                           category_id: str, keyword_groups: list, device: str = "", gender: str = "", ages: list = None) -> pd.DataFrame:
        """
        네이버 데이터랩 쇼핑인사이트 키워드 트렌드 데이터를 가져와서 DataFrame으로 변환합니다.
        
        :param category_id: 네이버 쇼핑 카테고리 코드 (예: '50000000')
        :param keyword_groups: [{'name': '그룹명', 'param': ['키워드1']}] 형식의 리스트
        """
        url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
        
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "category": category_id,
            "keyword": keyword_groups
        }
        
        if device:
            body["device"] = device
        if gender:
            body["gender"] = gender
        if ages:
            body["ages"] = ages

        data = self._call_api_post(url, body)
        
        results = data.get("results", [])
        if not results:
            return pd.DataFrame()
            
        dfs = []
        for group in results:
            group_name = group["title"]
            group_data = group.get("data", [])
            
            if not group_data:
                continue
                
            df = pd.DataFrame(group_data)
            df = df.rename(columns={"ratio": group_name})
            df["period"] = pd.to_datetime(df["period"])
            df = df.set_index("period")
            dfs.append(df)
            
        if not dfs:
            return pd.DataFrame()
            
        final_df = dfs[0]
        for df in dfs[1:]:
            final_df = final_df.join(df, how="outer")
            
        final_df = final_df.reset_index().sort_values("period")
        return final_df

    def get_blog_search(self, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> pd.DataFrame:
        """
        블로그 검색 API 결과를 가져옵니다.
        """
        url = "https://openapi.naver.com/v1/search/blog.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        data = self._call_api_get(url, params)
        items = data.get("items", [])
        return pd.DataFrame(items)

    def get_news_search(self, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> pd.DataFrame:
        """
        뉴스 검색 API 결과를 가져옵니다.
        """
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        data = self._call_api_get(url, params)
        items = data.get("items", [])
        return pd.DataFrame(items)

    def get_cafe_search(self, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> pd.DataFrame:
        """
        카페글 검색 API 결과를 가져옵니다.
        """
        url = "https://openapi.naver.com/v1/search/cafearticle.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        data = self._call_api_get(url, params)
        items = data.get("items", [])
        return pd.DataFrame(items)

    def get_shop_search(self, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> pd.DataFrame:
        """
        쇼핑 검색 API 결과를 가져옵니다.
        """
        url = "https://openapi.naver.com/v1/search/shop.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        data = self._call_api_get(url, params)
        items = data.get("items", [])
        return pd.DataFrame(items)
