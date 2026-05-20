import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# 메인 세팅 및 타이틀 버전 수정
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템 V2.0")

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

# 1. 사이드바 설정
with st.sidebar:
    st.header("📂 데이터 관리")
    st.success("📊 구글 시트 실시간 연동 중")
    months = ["전체 누적 데이터", "1월", "2월", "3월", "4월"]
    selected_month = st.selectbox("분석할 월 선택", months)
    st.markdown("---")
    st.subheader("🔍 세부 품목 검색")
    search_keyword = st.text_input("검색어 입력 (예: 팜유, 포장지 등)", placeholder="비워두면 전체 조회")

# 메인 화면 제목
st.title("🚀 생산1팀 통합 수율 관리 시스템 V2.0")
st.markdown(f"**현재 조회 데이터:** `{selected_month}`")
st.markdown("---")

# 데이터 로드 로직
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
            if not df.empty: df['월'] = mode
        if df.empty: return df
        if '生産部門명' in df.columns: df.rename(columns={'生産部門명': '생산부문명'}, inplace=True)
        # (기존 V2.0 컬럼 매핑 로직...)
        df.rename(columns={'生産部門名': '생산부문명', '資材タイプテキスト': '자재 유형 내역', '品목텍스트': '하위품목 텍스트', '理論金額': '이론금액', '實際金額': '실제금액', 'Actual Amount': '실제금액', '实际金额': '실제금액'}, inplace=True)
        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        team_df = df[df['생산부문명'].isin(my_team)].copy()
        for col in ['이론금액', '실제금액']:
            team_df[col] = pd.to_numeric(team_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return team_df
    except: return pd.DataFrame()

team_df = load_and_process_gsheet(selected_month, SHEET_ID)

if not team_df.empty:
    if search_keyword:
        team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]
    
    # KPI 
    t_theory, t_actual = team_df['이론금액'].sum(), team_df['실제금액'].sum()
    t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
    k1, k2, k3 = st.columns(3)
    k1.metric("🎯 이론 금액", f"{t_theory:,.0f} 원")
    k2.metric("💰 실제 금액", f"{t_actual:,.0f} 원")
    k3.metric("🏆 종합 수율", f"{t_yield:.2f} %")

    # 1단: 상세 표
    st.subheader("📋 과별 상세 수율 현황")
    tabs = st.tabs(['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합'])
    for i, d in enumerate(['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']):
        with tabs[i]:
            target = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
            final = target.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
            final.loc['전체 수율'] = [final['이론금액'].sum(), final['실제금액'].sum()]
            final['수율(%)'] = (final['이론금액'] / final['실제금액'] * 100)
            
            def sig(v, dn=d):
                trg = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 총합': 98.73}
                limit = trg.get(dn, 95.0)
                return f"🟢 {v:.2f}%" if v >= limit else f"🔴 {v:.2f}%"
            
            final['수율(%)'] = final['수율(%)'].apply(sig)
            st.dataframe(final.style.format({'이론금액': '{:,.0f}', '실제금액': '{:,.0f}'}), use_container_width=True)

    st.markdown("""<div style="background-color:#262730; padding:12px; border-radius:8px; border-left:5px solid #448AFF;">🎯 과별 수율 가이드: 🔹면1과 98.92% | 🔹면5과 97.92% | 🔹스프 99.53% | 🔹총합 98.73%</div>""", unsafe_allow_html=True)
    st.markdown("---")

    # 2단/3단: 기존 V2.0 그래프 로직 배치...
    row2_c1, row2_c2 = st.columns([45, 55])
    # ... (중략: 기존 그래프 코드와 동일) ...
