import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템 V2")

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

# 1. 사이드바 설정 (검색 기능 추가)
with st.sidebar:
    st.header("📂 데이터 관리")
    st.success("📊 구글 시트 실시간 연동 중")
    
    months = ["전체 누적 데이터", "1월", "2월", "3월", "4월"]
    selected_month = st.selectbox("분석할 월 선택", months)
    
    st.markdown("---")
    st.subheader("🔍 세부 품목 검색")
    search_keyword = st.text_input("검색어 입력 (예: 팜유, 포장지 등)", placeholder="비워두면 전체 조회")

st.title("🚀 생산1팀 통합 수율 관리 시스템 V2.0")
st.markdown(f"**현재 조회 데이터:** `{selected_month}`")
st.markdown("---")

# 2. 데이터 로드 및 정제 로직
@st.cache_data(ttl=600)
def load_and_process_gsheet(mode, sheet_id):
    try:
        if mode == "전체 누적 데이터":
            all_dfs = []
            for m in ["1월", "2월", "3월", "4월"]:
                encoded_sheet = urllib.parse.quote(m)
                url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
                temp_df = pd.read_csv(url)
                if not temp_df.empty:
                    temp_df['월'] = m  
                    all_dfs.append(temp_df)
            df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        else:
            encoded_sheet = urllib.parse.quote(mode)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            df = pd.read_csv(url)
            if not df.empty:
                df['월'] = mode
            
        if df.empty: return df

        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        team_df = df[df['생산부문명'].isin(my_team)].copy()
        
        team_df['자재 유형 내
