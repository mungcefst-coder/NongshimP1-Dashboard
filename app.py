import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# ⚡ [여기에 본인의 구글 스프레드시트 ID를 붙여넣으세요]
# 예: SHEET_ID = "1A2B3C4D5E..."
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

# 사이드바 설정
with st.sidebar:
    st.header("📂 데이터 관리")
    st.success("📊 구글 스프레드시트 연동 완료 (영구 저장)")
    
    # 분석할 월 선택 메뉴 (구글 시트의 탭 이름과 일치해야 합니다)
    months = ["전체 누적 데이터", "1월", "2월", "3월", "4월"]
    selected_month = st.selectbox("분석할 데이터 선택", months)

st.title("🚀 생산1팀 통합 수율 관리 시스템")
st.markdown(f"**현재 선택된 데이터:** `{selected_month}`")
st.markdown("---")

# 구글 스프레드시트에서 실시간으로 데이터를 긁어오는 로직
@st.cache_data(ttl=600) # 10분간 캐시 유지 (구글 시트 변경 시 10분 뒤 자동 반영)
def load_and_process_gsheet(mode, sheet_id):
    try:
        if mode == "전체 누적 데이터":
            all_dfs = []
            # 전체 누적일 경우 1월부터 4월까지 탭을 다 불러와서 합칩니다.
            for m in ["1월", "2월", "3월", "4월"]:
                url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={m}"
                temp_df = pd.read_csv(url)
                if not temp_df.empty:
                    all_dfs.append(temp_df)
            df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        else:
            # 특정 월만 선택했을 경우 해당 탭만 불러옵니다.
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={mode}"
            df = pd.read_csv(url)
            
        if df.empty: return df

        # 생산1팀 데이터 정제
        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        team_df = df[df['생산부문명'].isin(my_team)].copy()
        
        team_df['자재 유형 내역'] = team_df['자재 유형 내역'].astype(str).str.strip()
        pure_categories = ['원자재', '부자재', '반제품']
        team_df = team_df[team_df['자재 유형 내역'].isin(pure_categories)]
        return team_df
    except Exception as e:
        st.error(f"구글 시트를 읽어오는 중 오류가 발생했습니다. 탭 이름이나 권한을 확인하세요. 에러: {e}")
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
