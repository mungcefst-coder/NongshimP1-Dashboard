import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. 페이지 세팅 및 타이틀 
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# 디자인 테마 컬러 정의
MAIN_BLUE = "#4A90E2"       # 26년 (밝고 선명한 블루)
COMP_GRAY = "#B0BEC5"       # 25년 (슬레이트 그레이)
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
        # ⚡ [통합 로직] 연도 컬럼 생성
        team_df['연도'] = team_df['월'].apply(lambda x: '2025년 누적' if str(x).startswith('25.') else '2026년 누적')
        
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # 3. KPI 대시보드
        t_theory, t_actual = team_df['이론금액'].sum(), team_df['실제금액'].sum()
        t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🎯 선택 기간 이론 금액 총합", f"{t_theory:,.0f} 원")
        col2.metric("💰 선택 기간 실제 금액 총합", f"{t_actual:,.0f} 원")
        col3.metric("🏆 기간 평균 종합 수율", f"{t_yield:.2f} %")
        st.markdown("---")

        # 1단 - 수율 종합 지표
        st.subheader("📋 생산1팀 수율 종합 지표")
        depts_list = ['면 1과', '면 5과', '스프실', '전체 총합']
        selected_dept_tab = st.tabs(depts_list)
        
        for i, d in enumerate(depts_list):
            with selected_dept_tab[i]:
                tab_col1, tab_col2 = st.columns([53, 47])
                
                with tab_col1:
                    st.markdown(f"**📊 {d} 연도별 누적 지표 대조**")
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    if not target_df.empty:
                        base_summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        total_rows = []
                        for yr in base_summ['연도'].unique():
                            yr_df = base_summ[base_summ['연도'] == yr]
                            total_rows.append({'연도': yr, '자재 유형 내역': '전체 수율', '이론금액': yr_df['이론금액'].sum(), '실제금액': yr_df['실제금액'].sum()})
                        base_summ = pd.concat([base_summ, pd.DataFrame(total_rows)], ignore_index=True)
                        base_summ['수율(%)'] = (base_summ['이론금액'] / base_summ['실제금액'] * 100)
                        
                        pivot_df = base_summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                        # 컬럼 정리
                        flat_cols = []
                        for yr in ['2025년 누적', '2026년 누적']:
                            for val in ['이론금액', '실제금액', '수율(%)']:
                                flat_cols.append(f"{yr[:4]} {val.replace('(%)', '수율')}")
                        pivot_df.columns = flat_cols
                        pivot_df = pivot_df.reindex(['원자재', '부자재', '반제품', '전체 수율'])
                        st.dataframe(pivot_df.style.format('{:,.0f}'), use_container_width=True)
                    
                with tab_col2:
                    st.markdown(f"**📈 연도별 누적 수율 비교 (YoY)**")
                    agg_yoy = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                    agg_yoy['수율'] = (agg_yoy['이론금액'] / agg_yoy['실제금액'] * 100).round(2)
                    agg_yoy.rename(columns={'자재 유형 내역': '자재'}, inplace=True)
                    
                    fig_yoy = px.bar(
                        agg_yoy, x='자재', y='수율', color='연도', barmode='group', text='수율',
                        category_orders={'자재': ['원자재', '부자재', '반제품']},
                        color_discrete_map={'2025년 누적': COMP_GRAY, '2026년 누적': MAIN_BLUE}
                    )
                    fig_yoy.update_layout(template='plotly_white', height=280, legend=dict(orientation="h", y=1.1))
                    st.plotly_chart(fig_yoy, use_container_width=True)

        st.markdown("---")
        # 2단 - 자재별 비교 & 리스크 매트릭스
        r2_col1, r2_col2 = st.columns([45, 55])
        with r2_col1:
            st.subheader("📊 부서/자재별 수율 비교")
            # ⚡ 연도별 그룹화 적용
            dept_sum = team_df.groupby(['연도', '생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            fig1 = px.bar(
                dept_sum, x='생산부문명', y='수율', color='자재 유형 내역', facet_col='연도', barmode='group', text='수율',
                color_discrete_map={'원자재': '#34495E', '부자재': '#85C1E9', '반제품': '#D6EAF8'}
            )
            fig1.update_layout(template='plotly_white', height=350)
            st.plotly_chart(fig1, use_container_width=True)

        with r2_col2:
            st.subheader("🔍 수율 리스크 매트릭스")
            scatter_dept = st.selectbox("부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="matrix_filter")
            plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
            
            # ⚡ 연도별로 색상 구분
            fig3 = px.scatter(
                plot_df, x=plot_df['실제금액']/100000000, y=(plot_df['이론금액']/plot_df['실제금액']*100), 
                color='연도', hover_name='하위품목 텍스트', symbol='연도',
                color_discrete_map={'2025년 누적': COMP_GRAY, '2026년 누적': MAIN_BLUE}
            )
            fig3.add_hline(y=100.0, line_dash="dash", line_color="#7F8C8D")
            fig3.update_layout(template='plotly_white', height=350, xaxis_title="실제 투입 금액 (억원)")
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        # 3단 - Top 5
        st.subheader("🚨 과별 핵심 관리 대상 Top 5")
        year_filter = st.radio("연도 선택", ["2026년 누적", "2025년 누적"], horizontal=True)
        item_sum = team_df[team_df['연도'] == year_filter].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
        r3_c1, r3_c2 = st.columns(2)
        
        for i, d in enumerate(['면 1과', '면 5과']):
            with [r3_c1, r3_c2][i]:
                st.markdown(f"**📍 {d}**")
                m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(5)
                fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='수율', marker_color=MAIN_BLUE)
                fig_m.update_layout(template='plotly_white', height=300)
                st.plotly_chart(fig_m, use_container_width=True)
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 사이드바에서 날짜를 선택해 주세요.")
