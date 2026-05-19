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

        if '生産部門名' in df.columns: df.rename(columns={'生産部門名': '생산부문명'}, inplace=True)
        if '資材タイプテキスト' in df.columns: df.rename(columns={'資材タイプテキスト': '자재 유형 내역'}, inplace=True)
        if '品目テキスト' in df.columns: df.rename(columns={'品目テキスト': '하위품목 텍스트'}, inplace=True)
        if '理論金額' in df.columns: df.rename(columns={'理論金額': '이론금액'}, inplace=True)
        if 'Actual Amount' in df.columns: df.rename(columns={'Actual Amount': '실제금액'}, inplace=True)
        if '实际金额' in df.columns: df.rename(columns={'实际金额': '실제금액'}, inplace=True)
        if '實際金額' in df.columns: df.rename(columns={'實際金額': '실제금액'}, inplace=True)
        if '실제금액' not in df.columns and '실적금액' in df.columns: df.rename(columns={'실적금액': '실제금액'}, inplace=True)

        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        team_df = df[df['생산부문명'].isin(my_team)].copy()
        
        if '하위품목 텍스트' in team_df.columns:
            team_df['하위품목 텍스트'] = team_df['하위품목 텍스트'].astype(str).str.strip()
            exclude_keywords = ['소계', '합계', '총합', '총계', '결과', '부문명']
            for kw in exclude_keywords:
                team_df = team_df[~team_df['하위품목 텍스트'].str.contains(kw, na=False)]

        team_df['자재 유형 내역'] = team_df['자재 유형 내역'].astype(str).str.strip()
        pure_categories = ['원자재', '부자재', '반제품']
        team_df = team_df[team_df['자재 유형 내역'].isin(pure_categories)]
        
        for col in ['이론금액', '실제금액']:
            team_df[col] = team_df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            team_df[col] = pd.to_numeric(team_df[col], errors='coerce').fillna(0)
            
        calculated_yield = (team_df['이론금액'] / team_df['실제금액']) * 100
        team_df = team_df[~((team_df['실제금액'] > 0) & (calculated_yield < 50))]
        
        return team_df
    except Exception as e:
        st.error(f"구글 시트를 읽어오는 중 오류가 발생했습니다. 에러: {e}")
        return pd.DataFrame()

if selected_month:
    team_df = load_and_process_gsheet(selected_month, SHEET_ID)
    
    if not team_df.empty:
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

        # =========================================================================
        # ⚡ [1단 - 최상단 고정] 과별 상세 수율 현황 표 + 관리 기준 한 줄 배너
        # =========================================================================
        st.subheader("📋 과별 상세 수율 현황")
        depts_list = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
        tabs = st.tabs(depts_list)
        
        for i, d in enumerate(depts_list):
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
                
                desired_order = ['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율']
                existing_order = [idx for idx in desired_order if idx in final_summ.index]
                final_summ = final_summ.reindex(existing_order)
                
                def get_custom_color(val, dept_name=d):
                    if pd.isna(val): return ''
                    targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 총합': 98.73}
                    limit = targets.get(dept_name, 95.0)
                    if val < limit: return 'color: #FF5252; font-weight: bold;'
                    else: return 'color: #448AFF; font-weight: bold;'
                
                styled_df = final_summ.style.format({
                    '이론금액': '{:,.0f}', '실제금액': '{:,.0f}', '수율(%)': '{:.2f}%'
                }).map(get_custom_color, subset=['수율(%)'])
                st.dataframe(styled_df, use_container_width=True)
                
        # 초슬림 한 줄 배너 가이드 라인
        st.markdown("""
        <div style="background-color: #262730; padding: 12px 18px; border-radius: 8px; border-left: 5px solid #448AFF; margin-top: 10px; margin-bottom: 25px;">
            <span style="font-size: 14px; color: #B9F6CA; font-weight: bold; margin-right: 15px;">🎯 생산1팀 과별 수율 관리 기준 :</span>
            <span style="font-size: 13px; color: #E0E0E0; font-weight: 500;">
                🟢 <b>1팀 면1과 :</b> 수율 98.92% 이상 &nbsp;&nbsp;|&nbsp;&nbsp; 
                🟢 <b>1팀 면5과 :</b> 수율 97.92% 이상 &nbsp;&nbsp;|&nbsp;&nbsp; 
                🟢 <b>1팀 스프 :</b> 수율 99.53% 이상
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # =========================================================================
        # ⚡ [2단 - 중간 좌우 배치] 부서별 수율 비교 바 차트(좌) & 수율 리스크 매트릭스(우)
        # =========================================================================
        row2_col1, row2_col2 = st.columns([45, 55]) # 황금 가로 비율 4.5 : 5.5 분할
        
        with row2_col1:
            st.subheader("📊 부서 및 자재별 수율 비교")
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            
            custom_colors = {'원자재': '#0c4da2', '부자재': '#5a9bd5', '반제품': '#a6c8e0'}
            fig1 = px.bar(dept_sum, x='생산부문명', y='수율(%)', color='자재 유형 내역', barmode='group', text='수율(%)', 
                          category_orders={'자재 유형 내역': ['원자재', '부자재', '반제품']}, color_discrete_map=custom_colors)
            fig1.update_layout(yaxis=dict(range=[80, 105]), template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)

        with row2_col2:
            st.subheader("🔍 수율 리스크 매트릭스")
            
            # 한 줄 슬림 선택박스 정렬 적용
            lbl_col, select_col, _ = st.columns([30, 35, 35])
            with lbl_col:
                st.markdown("<p style='padding-top: 35px; font-weight: bold; font-size: 14px;'>🎯 분석할 부서 선택 :</p>", unsafe_allow_html=True)
            with select_col:
                scatter_dept = st.selectbox("", ["전체 1팀", "1팀 면1과", "1팀 면5과", "1팀 스프"], key="matrix_dept_filter")
            
            if scatter_dept == "전체 1팀":
                plot_df = team_df.copy()
            else:
                plot_df = team_df[team_df['생산부문명'] == scatter_dept].copy()
            
            item_scatter = plot_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
            item_scatter['수율(%)'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
            item_scatter['실제 투입 금액 (억 원)'] = item_scatter['실제금액'] / 100000000
            
            def get_scatter_status(row):
                targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53}
                limit = targets.get(row['생산부문명'], 95.0)
                return '기준 달성' if row['수율(%)'] >= limit else '기준 미달'
                
            if not item_scatter.empty:
                item_scatter['관리 상태'] = item_scatter.apply(get_scatter_status, axis=1)
                scatter_colors = {'기준 달성': '#448AFF', '기준 미달': '#FF5252'}
                
                fig3 = px.scatter(item_scatter, x='실제 투입 금액 (억 원)', y='수율(%)', hover_name='하위품목 텍스트',
                    color='관리 상태', color_discrete_map=scatter_colors, category_orders={'관리 상태': ['기준 미달', '기준 달성']})
                fig3.update_traces(hovertemplate="<b>%{hovertext}</b><br><br>실제 투입 금액: %{x:.2f}억 원<br>수율: %{y:.2f}%<extra></extra>",
                    marker=dict(size=10, opacity=0.9, line=dict(width=1, color='rgba(255,255,255,0.4)')))
                
                targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53}
                if scatter_dept in targets:
                    specific_limit = targets[scatter_dept]
                    fig3.add_hline(y=specific_limit, line_dash="dash", line_color="#FF5252", opacity=0.8, annotation_text=f"{specific_limit}%", annotation_position="top left")
                else:
                    fig3.add_hline(y=98.0, line_dash="dash", line_color="#FFF", opacity=0.3, annotation_text="98%", annotation_position="top left")
                    
                fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(ticksuffix="억"))
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("데이터 없음")

        st.markdown("---")

        # =========================================================================
        # ⚡ [3단 - 최하단 전면 배치] 과별 리스크 최상위 집중 관리 대상 Top 5 좌우 듀얼 배치
        # =========================================================================
        st.subheader("🚨 과별 핵심 관리 대상 Top 5")
        
        item_sum = team_df[team_df['생산부문명'] != '1팀 스프'].copy()
        item_sum = item_sum.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_sum['수율(%)'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
        
        premium_blue_palette = ['#0c4da2', '#2a69bd', '#4d88db', '#75a8f5', '#a3c7ff']
        row3_col1, row3_col2 = st.columns(2)
        
        with row3_col1:
            st.markdown("**📍 면 1과 관리 품목**")
            m1_data = item_sum[item_sum['생산부문명'] == '1팀 면1과'].copy()
            if not m1_data.empty:
                m1_large = m1_data.sort_values('실제금액', ascending=False).head(15)
                m1_top5 = m1_large.sort_values('수율(%)', ascending=True).head(5)
                m1_top5['표시텍스트'] = m1_top5.apply(lambda r: f"수율: {r['수율(%)']:.2f}% | 실제: {(r['실제금액']/100000000):.2f}억", axis=1)
                fig_m1 = px.bar(m1_top5, x='수율(%)', y='하위품목 텍스트', orientation='h', text='표시텍스트', color='하위품목 텍스트', color_discrete_sequence=premium_blue_palette)
                fig_m1.update_layout(showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 115]), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_m1, use_container_width=True)
            else: st.write("데이터 없음")

        with row3_col2:
            st.markdown("**📍 면 5과 관리 품목**")
            m5_data = item_sum[item_sum['생산부문명'] == '1팀 면5과'].copy()
            if not m5_data.empty:
                m5_large = m5_data.sort_values('실제금액', ascending=False).head(15)
                m5_top5 = m5_large.sort_values('수율(%)', ascending=True).head(5)
                m5_top5['표시텍스트'] = m5_top5.apply(lambda r: f"수율: {r['수율(%)']:.2f}% | 실제: {(r['실제금액']/100000000):.2f}억", axis=1)
                fig_m5 = px.bar(m5_top5, x='수율(%)', y='하위품목 텍스트', orientation='h', text='표시텍스트', color='하위품목 텍스트', color_discrete_sequence=premium_blue_palette)
                fig_m5.update_layout(showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 115]), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_m5, use_container_width=True)
            else: st.write("데이터 없음")
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 구글 시트 상태를 확인해 주세요.")
