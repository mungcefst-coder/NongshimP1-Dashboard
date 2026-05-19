import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# ⚡ [본인의 구글 스프레드시트 ID를 입력하세요]
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

# 사이드바 설정
with st.sidebar:
    st.header("📂 데이터 관리")
    st.success("📊 구글 스프레드시트 연동 완료 (영구 저장)")
    
    months = ["전체 누적 데이터", "1월", "2월", "3월", "4월"]
    selected_month = st.selectbox("분석할 데이터 선택", months)

st.title("🚀 생산1팀 통합 수율 관리 시스템")
st.markdown(f"**현재 선택된 데이터:** `{selected_month}`")
st.markdown("---")

# 구글 스프레드시트 연동 로직
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
                    all_dfs.append(temp_df)
            df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        else:
            encoded_sheet = urllib.parse.quote(mode)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            df = pd.read_csv(url)
            
        if df.empty: return df

        # 생산1팀 데이터 정제
        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        team_df = df[df['생산부문명'].isin(my_team)].copy()
        
        team_df['자재 유형 내역'] = team_df['자재 유형 내역'].astype(str).str.strip()
        pure_categories = ['원자재', '부자재', '반제품']
        team_df = team_df[team_df['자재 유형 내역'].isin(pure_categories)]
        
        # ---------------------------------------------------------
        # ⚡ [새로 추가된 핵심 로직] 콤마(,) 제거 및 숫자 강제 변환
        # ---------------------------------------------------------
        for col in ['이론금액', '실제금액']:
            if team_df[col].dtype == 'object':  # 텍스트로 인식되었다면
                team_df[col] = team_df[col].astype(str).str.replace(',', '').astype(float)
        
        return team_df
    except Exception as e:
        st.error(f"구글 시트를 읽어오는 중 오류가 발생했습니다. 에러: {e}")
        return pd.DataFrame()

# 메인 화면 구성
if selected_month:
    team_df = load_and_process_gsheet(selected_month, SHEET_ID)
    
    if not team_df.empty:
        col1, col2 = st.columns([4, 6])
        
        with col1:
            st.subheader("🎯 수율 집중 개선 품목 (Targeting)")
            summary = team_df.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum()
            summary['수율(%)'] = (summary['이론금액'] / summary['실제금액']) * 100
            summary['손실액'] = summary['실제금액'] - summary['이론금액']
            
            critical = summary[(summary['수율(%)'] < 95) & (summary['손실액'] >= 1000000)].copy()
            if not critical.empty:
                st.error("🚨 즉각적인 확인 필요")
                st.dataframe(critical[['수율(%)', '손실액']].sort_values('손실액', ascending=False).style.format({'수율(%)': '{:.2f}%', '손실액': '{:,.0f}원'}), use_container_width=True)
            else:
                st.success("✅ 관리 기준 내 정상")

        with col2:
            st.subheader("📊 과별 수율 그래프")
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset
