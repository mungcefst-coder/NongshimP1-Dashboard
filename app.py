import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# 서버 전용 로컬 저장 폴더
DATA_DIR = "Smart_Yield_Data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 사이드바 - 파일 업로드 및 월 선택
with st.sidebar:
    st.header("📂 데이터 관리")
    uploaded_files = st.file_uploader("월별 Raw 데이터 업로드 (여러 파일 가능)", type=["xlsx", "XLSX"], accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success("데이터가 서버에 임시 저장되었습니다!")
        st.cache_data.clear()

    files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.xlsx')]
    if files:
        selected_file = st.selectbox("분석할 데이터 선택", ["전체 누적 데이터"] + sorted(files, reverse=True))
    else:
        selected_file = None
        st.info("파일을 먼저 업로드해주세요.")

st.title("🚀 생산1팀 통합 수율 관리 시스템")
st.markdown(f"**현재 선택된 데이터:** `{selected_file}`")
st.markdown("---")

# 데이터 로드 및 전처리 로직
@st.cache_data
def load_and_process_data(mode):
    if mode == "전체 누적 데이터":
        all_dfs = []
        for f in os.listdir(DATA_DIR):
            if f.lower().endswith('.xlsx'):
                temp_df = pd.read_excel(os.path.join(DATA_DIR, f))
                all_dfs.append(temp_df)
        df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    else:
        df = pd.read_excel(os.path.join(DATA_DIR, mode))
    
    if df.empty: return df

    my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
    team_df = df[df['생산부문명'].isin(my_team)].copy()
    
    team_df['자재 유형 내역'] = team_df['자재 유형 내역'].astype(str).str.strip()
    pure_categories = ['원자재', '부자재', '반제품']
    team_df = team_df[team_df['자재 유형 내역'].isin(pure_categories)]
    
    return team_df

if selected_file:
    team_df = load_and_process_data(selected_file)
    
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
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            
            fig = px.bar(dept_sum, x='생산부문명', y='수율(%)', color='자재 유형 내역', barmode='group', text='수율(%)')
            fig.update_layout(yaxis=dict(range=[80, 105]), template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 과별 수율 현황")
        depts = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
        tabs = st.tabs(depts)
        
        for i, d in enumerate(depts):
            with tabs[i]:
                target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                final_summ = target_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                
                raw_sub_theory = final_summ.loc[final_summ.index.isin(['원자재', '부자재']), '이론금액'].sum()
                raw_sub_actual = final_summ.loc[final_summ.index.isin(['원자재', '부자재']), '실제금액'].sum()
                all_theory = final_summ.loc[final_summ.index.isin(['원자재', '부자재', '반제품']), '이론금액'].sum()
                all_actual = final_summ.loc[final_summ.index.isin(['원자재', '부자재', '반제품']), '실제금액'].sum()
                
                final_summ.loc['원부자재 수율'] = [raw_sub_theory, raw_sub_actual]
                final_summ.loc['전체 수율'] = [all_theory, all_actual]
                final_summ['수율(%)'] = (final_summ['이론금액'] / final_summ['실제금액'] * 100)
                
                st.dataframe(final_summ.style.format({
                    '이론금액': '{:,.0f}',
                    '실제금액': '{:,.0f}',
                    '수율(%)': '{:.2f}%'
                }), use_container_width=True)
else:
    st.warning("👈 왼쪽 사이드바에서 데이터를 업로드하고 분석을 시작하세요!")
