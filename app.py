import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. 페이지 세팅 및 타이틀 
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# 디자인 테마 컬러 정의
MAIN_BLUE = "#4A90E2"       # 26년 혹은 최신년도 누적 실적 (밝고 선명한 블루)
COMP_GRAY = "#B0BEC5"       # 25년 혹은 과거년도 누적 실적 (슬레이트 그레이)
BG_WHITE = "#FFFFFF"

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = [
    "25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
    "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
    "26.01", "26.02", "26.03", "26.04"
]

# 사이드바 컨트롤러
with st.sidebar:
    st.header("📂 데이터 관제")
    st.info("📊 연도별 누적 교차 비교 기능 가동 중")
    
    # 년월 복수 선택 바스켓 (기본값으로 25년 1분기와 26년 1분기를 모두 넣어 비교 예시 구성)
    selected_months = st.multiselect(
        "분석할 년월(YY.MM) 복수 선택 가능", 
        options=ALL_MONTHS, 
        default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"]
    )
    
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="비워두면 전체 조회")

# 메인 화면 제목
st.title("⚙️ 생산1팀 통합 수율 관리 시스템")

# 조회 기간 가독성 포맷팅
if selected_months:
    sorted_display_months = sorted(selected_months)
    st.markdown(f"**현재 선택 기간:** `{', '.join(sorted_display_months)}` (연도별 자동 그룹화 누적 연산)")
else:
    st.warning("⚠️ 사이드바에서 분석할 년월을 최소 1개 이상 선택해 주세요.")
st.markdown("---")

# 2. 데이터 처리 로직
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy(); df['월'] = month_label
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        '生産部門名': '생산부문명', '生産部門명': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資材タイプテキスト': '자재 유형 내역',
        '品목텍스트': '하위품목 텍스트', '品목 텍스트': '하위품목 텍스트', '品目テキスト': '하위품목 텍스트', '하위품목텍스트': '하위품목 텍스트',
        '理論金額': '이론금액', '實際金額': '실제금액', 'Actual Amount': '실제금액', '实际金額': '실제금액', 'Actual金额': '실제금액'
    }
    df.rename(columns=rename_map, inplace=True)
    
    if '생산부문명' in df.columns:
        df['생산부문명'] = df['생산부문명'].strip() if hasattr(df['생산부문명'], 'strip') else df['생산부문명']
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실'}
        df = df[df['생산부문명'].isin(dept_map.keys())].copy()
        df['생산부문명'] = df['생산부문명'].map(dept_map)
    else: 
        return pd.DataFrame()
    
    if '자재 유형 내역' in df.columns:
        df = df[df['자재 유형 내역'].isin(['원자재', '부자재', '반제품'])]
        
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    calc_yield = (df['이론금액'] / df['실제금액']) * 100
    df = df[~((df['실제금액'] > 0) & (calc_yield < 50))]
    return df

@st.cache_data(ttl=600)
def load_all_raw_data(sheet_id, month_list):
    month_data_dict = {}
    for m in month_list:
        try:
            encoded_sheet = urllib.parse.quote(m)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            raw_df = pd.read_csv(url)
            processed = preprocess_df(raw_df, m)
            if not processed.empty: month_data_dict[m] = processed
        except: pass
    return month_data_dict

# 마스터 데이터 로드
data_pool = load_all_raw_data(SHEET_ID, ALL_MONTHS)

if data_pool and selected_months:
    active_dfs = [data_pool[m] for m in selected_months if m in data_pool]
    
    if active_dfs:
        team_df = pd.concat(active_dfs, ignore_index=True)
        
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # 3. KPI 대시보드 연산 (선택된 전체 기간 통합 기준)
        t_theory, t_actual = team_df['이론금액'].sum(), team_df['실제금액'].sum()
        t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🎯 선택 기간 이론 금액 총합", f"{t_theory:,.0f} 원")
        col2.metric("💰 선택 기간 실제 금액 총합", f"{t_actual:,.0f} 원")
        col3.metric("🏆 기간 평균 종합 수율", f"{t_yield:.2f} %")
        st.markdown("---")

        # ⚡ 1단 - 생산1팀 수율 종합 지표
        st.subheader("📋 생산1팀 수율 종합 지표")
        depts_list = ['면 1과', '면 5과', '스프실', '전체 총합']
        selected_dept_tab = st.tabs(depts_list)
        
        for i, d in enumerate(depts_list):
            with selected_dept_tab[i]:
                tab_col1, tab_col2 = st.columns([50, 50])
                
                with tab_col1:
                    st.markdown(f"**📊 {d} 기간 병합 지표**")
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    if not target_df.empty:
                        base_summ = target_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                        order_list = [c for c in ['원자재', '부자재', '반제품'] if c in base_summ.index]
                        final_summ = base_summ.reindex(order_list)
                        
                        final_summ.loc['전체 수율'] = [final_summ['이론금액'].sum(), final_summ['실제금액'].sum()]
                        final_summ['수율(%)'] = (final_summ['이론금액'] / final_summ['실제금액'] * 100)
                        
                        def sig(v, dn=d):
                            trg = {'면 1과': 98.92, '면 5과': 97.92, '스프실': 99.53, '전체 총합': 98.73}
                            limit = trg.get(dn, 98.73)
                            return f"🟢 {v:.2f}%" if v >= limit else f"🔴 {v:.2f}%"
                        
                        final_summ['수율(%)'] = final_summ['수율(%)'].apply(sig)
                        st.dataframe(final_summ.style.format({'이론금액': '{:,.0f}', '실제금액': '{:,.0f}'}), use_container_width=True)
                    else:
                        st.caption("선택된 내역에 부서 데이터가 매칭되지 않습니다.")
                    
                    st.markdown(f"""<div style="background-color:#F0F7FF; padding:10px; border-radius:8px; border-left:5px solid {MAIN_BLUE}; font-size:12px; color:#34495E;">
                        🎯 <b>{d} 기준 :</b> { '98.92%' if d=='면 1과' else '97.92%' if d=='면 5과' else '99.53%' if d=='스프실' else '98.73%' } 이상</div>""", unsafe_allow_html=True)

                with tab_col2:
                    # ⚡ [핵심 알고리즘 수정] 선택 기간 자재별 누적 '연도 분리' 교차 대조 차트
                    st.markdown(f"**📈 선택 기간 연도별 누적 수율 비교 (YoY)**")
                    
                    if not target_df.empty:
                        # 1. 각 데이터가 어떤 연도 그룹에 속하는지 식별자 컬럼 생성 (예: '25.'로 시작하면 '2025년 누적', 아니면 '2026년 누적')
                        chart_df = target_df.copy()
                        chart_df['연도구분'] = chart_df['월'].apply(lambda x: '2025년 누적' if str(x).startswith('25.') else '2026년 누적')
                        
                        # 2. 연도구분 및 자재유형별로 이론금액과 실제금액을 완전히 합산(누적)
                        agg_yoy = chart_df.groupby(['연도구분', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        agg_yoy['수율'] = (agg_yoy['이론금액'] / agg_yoy['실제금액'] * 100).round(2)
                        agg_yoy.rename(columns={'자재 유형 내역': '자재'}, inplace=True)
                        
                        # 3. X축은 자재로 고정하고, 연도구분으로 막대를 갈라 나란히(barmode='group') 배치
                        fig_yoy = px.bar(
                            agg_yoy, x='자재', y='수율', color='연도구분', barmode='group', text='수율',
                            category_orders={'자재': ['원자재', '부자재', '반제품'], '연도구분': ['2025년 누적', '2026년 누적']},
                            color_discrete_map={'2025년 누적': COMP_GRAY, '2026년 누적': MAIN_BLUE}
                        )
                        fig_yoy.update_layout(
                            template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            yaxis=dict(range=[85, 103], title="누적 수율 (%)"), xaxis=dict(title=None),
                            margin=dict(l=0, r=0, t=30, b=0), height=280, 
                            legend=dict(title=None, orientation="h", y=1.1, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_yoy, use_container_width=True)
                    else:
                        st.caption("차트를 그릴 데이터가 없습니다.")

        st.markdown("---")
        # 2단 - 자재별 비교 & 리스크 매트릭스 (선택 기간 자동 누적 반영)
        r2_col1, r2_col2 = st.columns([45, 55])
        with r2_col1:
            st.subheader("📊 부서/자재별 수율 비교")
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            fig1 = px.bar(dept_sum, x='생산부문명', y='수율', color='자재 유형 내역', barmode='group', text='수율',
                          color_discrete_map={'원자재': '#34495E', '부자재': '#85C1E9', '반제품': '#D6EAF8'})
            
            fig1.update_layout(
                template='plotly_white', 
                yaxis=dict(range=[80, 105]), 
                xaxis=dict(categoryorder='array', categoryarray=['원자재', '부자재', '반제품']),
                height=350
            )
            st.plotly_chart(fig1, use_container_width=True)

        with r2_col2:
            st.subheader("🔍 수율 리스크 매트릭스")
            
            select_box_col, _, _ = st.columns([30, 35, 35])
            with select_box_col:
                scatter_dept = st.selectbox("부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="matrix_filter")
                
            plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
            
            if not plot_df.empty:
                item_scatter = plot_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
                item_scatter['수율'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
                item_scatter['actual_billion'] = item_scatter['실제금액'] / 100000000
                
                def classify_risk(row):
                    if row['수율'] < 100.0 and row['actual_billion'] >= (2.0 * len(selected_months)):
                        return '고위험 관리품목 (수율 미달 & 대형 자재)'
                    return '일반 품목'
                    
                item_scatter['관리 등급'] = item_scatter.apply(classify_risk, axis=1)
                
                fig3 = px.scatter(
                    item_scatter, x='actual_billion', y='수율', 
                    hover_name='하위품목 텍스트', color='관리 등급',
                    color_discrete_map={
                        '일반 품목': MAIN_BLUE,
                        '고위험 관리품목 (수율 미달 & 대형 자재)': '#FF4D4D'
                    }
                )
                fig3.add_hline(y=100.0, line_dash="dash", line_color="#7F8C8D", opacity=0.8, annotation_text="수율 100.0% 기준선")
                fig3.update_layout(
                    template='plotly_white', 
                    xaxis=dict(title="실제 투입 금액 (억원)", ticksuffix="억"), 
                    yaxis=dict(title="수율 (%)"),
                    legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=350
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.caption("조회할 자재 리스크 내역이 없습니다.")

        st.markdown("---")
        # 3단 - Top 5 (채도 감쇄 그라데이션)
        st.subheader("🚨 과별 핵심 관리 대상 Top 5")
        item_sum = team_df[team_df['생산부문명'] != '스프실'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
        r3_c1, r3_c2 = st.columns(2)
        
        blue_grad = ['#D6EAF8', '#AED6F1', '#85C1E9', '#5DADE2', '#2E86C1'] 
        
        for i, d in enumerate(['면 1과', '면 5과']):
            with [r3_c1, r3_c2][i]:
                st.markdown(f"**📍 {d}**")
                m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                if not m_data.empty:
                    m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                    fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                    fig_m.update_traces(marker_color=blue_grad, textposition='inside')
                    fig_m.update_layout(template='plotly_white', showlegend=False, xaxis=dict(range=[0, 115]), height=300, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_m, use_container_width=True)
