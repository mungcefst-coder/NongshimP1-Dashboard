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

if selected_months:
    sorted_display_months = sorted(selected_months)
    st.markdown(f"**현재 선택 기간:** `{', '.join(sorted_display_months)}`")
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

data_pool = load_all_raw_data(SHEET_ID, ALL_MONTHS)

if data_pool and selected_months:
    active_dfs = [data_pool[m] for m in selected_months if m in data_pool]
    team_df = pd.concat(active_dfs, ignore_index=True)
    team_df['연도'] = team_df['월'].apply(lambda x: '2025년' if str(x).startswith('25.') else '26년')
    
    if search_keyword:
        team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

    # 1단 - 수율 종합 지표 (상단 고정)
    st.subheader("📋 생산1팀 수율 종합 지표")
    # ... (상단 KPI 및 표 로직 유지) ...

    # ⚡ 2단 - 컨트롤러 추가 및 로직 적용
    st.markdown("---")
    r2_col1, r2_col2 = st.columns([45, 55])
    
    with r2_col1:
        st.subheader("📊 부서/자재별 수율 비교")
        year_filter1 = st.radio("연도 선택", ["2026년", "2025년"], key="y1", horizontal=True)
        plot_df1 = team_df[team_df['연도'] == year_filter1]
        
        dept_sum = plot_df1.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
        dept_sum['수율'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
        fig1 = px.bar(dept_sum, x='생산부문명', y='수율', color='자재 유형 내역', barmode='group', text='수율',
                      color_discrete_map={'원자재': '#34495E', '부자재': '#85C1E9', '반제품': '#D6EAF8'})
        fig1.update_layout(template='plotly_white', height=300)
        st.plotly_chart(fig1, use_container_width=True)

    with r2_col2:
        st.subheader("🔍 수율 리스크 매트릭스")
        year_filter2 = st.radio("연도 선택", ["2026년", "2025년"], key="y2", horizontal=True)
        scatter_dept = st.selectbox("부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="m1")
        
        plot_df2 = team_df[(team_df['연도'] == year_filter2)]
        if scatter_dept != "전체 1팀": plot_df2 = plot_df2[plot_df2['생산부문명'] == scatter_dept]
        
        item_scatter = plot_df2.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_scatter['수율'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
        
        fig3 = px.scatter(item_scatter, x=item_scatter['실제금액']/100000000, y='수율', hover_name='하위품목 텍스트', color_discrete_sequence=[MAIN_BLUE])
        fig3.add_hline(y=100.0, line_dash="dash", line_color="#7F8C8D")
        fig3.update_layout(template='plotly_white', height=300)
        st.plotly_chart(fig3, use_container_width=True)

    # 3단 - Top 5
    st.subheader("🚨 과별 핵심 관리 대상 Top 5")
    year_filter3 = st.radio("연도 선택", ["2026년", "2025년"], key="y3", horizontal=True)
    item_sum = team_df[team_df['연도'] == year_filter3].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
    item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
    # ... (상단 로직 유지) ...
