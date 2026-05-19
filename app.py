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
        
        team_df['자재 유형 내역'] = team_df['자재 유형 내역'].astype(str).str.strip()
        pure_categories = ['원자재', '부자재', '반제품']
        team_df = team_df[team_df['자재 유형 내역'].isin(pure_categories)]
        
        # 콤마, 공백 모두 무시하고 강제 숫자 변환
        for col in ['이론금액', '실제금액']:
            team_df[col] = team_df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            team_df[col] = pd.to_numeric(team_df[col], errors='coerce').fillna(0)
        
        return team_df
    except Exception as e:
        st.error(f"구글 시트를 읽어오는 중 오류가 발생했습니다. 에러: {e}")
        return pd.DataFrame()

# 메인 화면 구성
if selected_month:
    team_df = load_and_process_gsheet(selected_month, SHEET_ID)
    
    if not team_df.empty:
        # 검색어 필터링 적용
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]
            st.info(f"💡 '{search_keyword}'(이)가 포함된 품목만 분석한 결과입니다.")

        # 3. 최상단 KPI 대시보드
        total_theory = team_df['이론금액'].sum()
        total_actual = team_df['실제금액'].sum()
        total_yield = (total_theory / total_actual * 100) if total_actual > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("🎯 이론 금액", f"{total_theory:,.0f} 원")
        col2.metric("💰 실제 금액", f"{total_actual:,.0f} 원")
        col3.metric("🏆 종합 수율", f"{total_yield:.2f} %")
        st.markdown("---")

        # 4. 시각화 분석 탭
        tab1, tab2, tab3 = st.tabs(["📊 과별 비교 분석", "🚨 집중 관리 대상 (Top 5)", "🔍 이상치 탐지 (산포도)"])
        
        with tab1:
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            
            custom_colors = {
                '원자재': '#90CAF9',
                '부자재': '#A5D6A7',
                '반제품': '#FFAB91' 
            }
            
            fig1 = px.bar(
                dept_sum, 
                x='생산부문명', 
                y='수율(%)', 
                color='자재 유형 내역', 
                barmode='group', 
                text='수율(%)', 
                title="부서 및 자재별 수율 비교",
                category_orders={'자재 유형 내역': ['원자재', '부자재', '반제품']},
                color_discrete_map=custom_colors
            )
            fig1.update_layout(yaxis=dict(range=[80, 105]), template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            st.markdown("#### 손실액 기준 집중 개선 품목 Top 5")
            item_sum = team_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_sum['손실액'] = item_sum['실제금액'] - item_sum['이론금액']
            
            top_losers = item_sum.sort_values(['생산부문명', '손실액'], ascending=[True, False]).groupby('생산부문명').head(5)
            
            fig2 = px.bar(top_losers, x='손실액', y='하위품목 텍스트', color='생산부문명', orientation='h', text='손실액', title="과별 핵심 손실 품목 (단위: 원)")
            fig2.update_traces(texttemplate='%{text:,.0f}')
            fig2.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            st.markdown("#### 이론금액 vs 실제금액 산포도 (점 위치가 기준선 아래로 멀어질수록 이상치)")
            item_scatter = team_df.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
            fig3 = px.scatter(item_scatter, x='이론금액', y='실제금액', hover_name='하위품목 텍스트', color='실제금액', color_continuous_scale='Reds', title="품목별 투입 금액 분포")
            
            max_val = max(item_scatter['실제금액'].max(), item_scatter['이론금액'].max())
            fig3.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="LightSeaGreen", width=2, dash="dash"))
            fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        
        # 5. 상세 현황 표 (신호등 서식 및 순서 적용)
        st.subheader("📋 과별 상세 수율 현황")
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
                
                # ⚡ [요청 1] 표 행 순서 고정 (없는 항목은 건너뛰고 있는 항목만 정렬)
                desired_order = ['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율']
                existing_order = [idx for idx in desired_order if idx in final_summ.index]
                final_summ = final_summ.reindex(existing_order)
                
                # ⚡ [요청 2~5] 각 과별 맞춤형 수율 기준 색상 함수 (빨강/파랑)
                def get_custom_color(val, dept_name=d):
                    if pd.isna(val): return ''
                    
                    # 과별 기준 타겟 설정
                    targets = {
                        '1팀 면1과': 98.92,
                        '1팀 면5과': 97.92,
                        '1팀 스프': 99.53,
                        '전체 총합': 98.73
                    }
                    limit = targets.get(dept_name, 95.0) # 기본값
                    
                    if val < limit:
                        # 기준 미달: 눈에 띄는 빨간색 + 굵은 글씨
                        return 'color: #FF5252; font-weight: bold;'
                    else:
                        # 기준 달성: 안정적인 파란색 + 굵은 글씨
                        return 'color: #448AFF; font-weight: bold;'
                
                # 표에 색상 및 숫자 포맷 적용
                styled_df = final_summ.style.map(get_custom_color, subset=['수율(%)']).format({
                    '이론금액': '{:,.0f}',
                    '실제금액': '{:,.0f}',
                    '수율(%)': '{:.2f}%'
                })
                
                st.dataframe(styled_df, use_container_width=True)
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 구글 시트 상태를 확인해 주세요.")
