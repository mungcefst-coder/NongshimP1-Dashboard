import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# ==============================================================================
# [1] 시스템 설정 및 테마 디자인 (CSS Injection)
# ==============================================================================
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# ERP 대시보드 스타일의 CSS 주입
st.markdown("""
    <style>
        /* 배경색 및 폰트 설정 */
        .main {
            background-color: #F8FAFC;
        }
        
        /* 섹션 카드 스타일 */
        .dashboard-card {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 25px;
        }
        
        /* 헤더 스타일 */
        .section-header {
            font-size: 18px;
            font-weight: 700;
            color: #1E293B;
            border-left: 5px solid #1E40AF;
            padding-left: 15px;
            margin-bottom: 20px;
        }
        
        /* 글자 크기 최적화 */
        p, li, label, .stMetric {
            font-size: 14px !important;
        }
        
        /* 상단 메트릭 강제 확대 */
        div[data-testid="stMetricLabel"] p {
            font-size: 16px !important;
            font-weight: 700 !important;
            color: #64748B !important;
        }
        div[data-testid="stMetricValue"] div {
            font-size: 32px !important;
            font-weight: 800 !important;
            color: #1E40AF !important;
        }
        
        /* 하단 슬림 필터 바 */
        .bottom-filter-label {
            font-size: 12.5px !important;
            color: #7F8C8D;
            margin-bottom: -12px !important;
            padding-left: 2px;
            font-weight: bold;
        }
        div[data-testid="stRadio"] label span {
            font-size: 12.5px !important;
        }
        
        /* 탭 디자인 정돈 */
        .stTabs [data-baseweb="tab"] {
            font-size: 14px !important;
            font-weight: 600 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# [2] 전역 데이터 소스 및 기준선
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = [
    "25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
    "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
    "26.01", "26.02", "26.03", "26.04"
]

YIELD_THRESHOLD = {
    '면 1과': 98.92, '면 5과': 97.93, '스프실': 99.53, '전체 총합': 98.73
}

MAIN_BLUE = "#1E40AF"
COMP_GRAY = "#94A3B8"
ALERT_RED = "#EF4444"

# ==============================================================================
# [3] 데이터 처리 엔진
# ==============================================================================
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy(); df['월'] = month_label
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        '生産部門명': '생산부문명', '生産部門名': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資재 유형내역': '자재 유형 내역',
        '品목텍스트': '하위품목 텍스트', '품목 텍스트': '하위품목 텍스트',
        '理論金額': '이론금액', '實際金額': '실제금액'
    }
    df.rename(columns=rename_map, inplace=True)
    
    if '생산부문명' in df.columns:
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실', '면 1과': '면 1과', '면 5과': '면 5과', '스프실': '스프실'}
        df = df[df['생산부문명'].isin(dept_map.keys())].copy()
        df['생산부문명'] = df['생산부문명'].map(dept_map)
    else: return pd.DataFrame()
    
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
    
    return df[~((df['실제금액'] > 0) & ((df['이론금액']/df['실제금액']*100) < 50))]

@st.cache_data(ttl=3600)
def load_single_month_cached(sheet_id, m):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(m)}"
        return preprocess_df(pd.read_csv(url), m)
    except: return pd.DataFrame()

# ==============================================================================
# [4] 사이드바 & 대시보드 헤더
# ==============================================================================
with st.sidebar:
    st.image("https://www.nongshim.com/common/img/header_logo.png", width=150) # 농심 로고 이미지 (예시)
    st.header("📊 관제 컨트롤러")
    selected_months = st.multiselect("분석 대상 년월 선택", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="검색어 입력 시 필터링")

st.title("🛡️ 생산1팀 통합 수율 관리 시스템 (Integrated Dashboard)")

# ==============================================================================
# [5] 메인 레이아웃 렌더링
# ==============================================================================
if selected_months:
    active_dfs = [load_single_month_cached(SHEET_ID, m) for m in selected_months]
    team_df = pd.concat([d for d in active_dfs if not d.empty], ignore_index=True)
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- [CARD 1] 상단 핵심 요약 (KPI) ---
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        df_26 = team_df[team_df['연도'] == '26년 누적']
        
        if not df_26.empty:
            th, ac = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            total_yield = (th / ac * 100) if ac > 0 else 0
            cost_bill = ac / 100000000
            risk_count = len(df_26.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().query('실제금액 >= 400000000 and (이론금액/실제금액*100) <= 98.0'))
            
            kpi_col1.metric("📊 2026년 종합 수율", f"{total_yield:.2f}%", "안정권 가동")
            kpi_col2.metric("💰 누적 실제 투입 금액", f"{cost_bill:,.1f} 억 원", "생산 규모")
            kpi_col3.metric("🚨 4억 이상 고위험 자재", f"{risk_count} 개 품목", "집중 관리 필요" if risk_count > 0 else "정상", delta_color="inverse")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 2] 수율 종합 상황판 (탭 인터페이스) ---
        st.markdown('<div class="dashboard-card"><div class="section-header">📋 부문별 수율 상세 분석</div>', unsafe_allow_html=True)
        depts = ['면 1과', '면 5과', '스프실', '전체 총합']
        selected_tabs = st.tabs(depts)
        
        for idx, d in enumerate(depts):
            with selected_tabs[idx]:
                col_left, col_right = st.columns(2)
                t_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                
                with col_left: # 테이블 구역
                    if not t_df.empty:
                        pivot = t_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        pivot['수율(%)'] = pivot['이론금액'] / pivot['실제금액'] * 100
                        display_df = pivot.pivot(index='자재 유형 내역', columns='연도', values='수율(%)')
                        st.dataframe(display_df.style.format("{:.2f}%").background_gradient(cmap='Blues', axis=1), use_container_width=True)
                
                with col_right: # 트렌드 구역
                    if not t_df.empty:
                        trend = t_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index()
                        trend['수율'] = (trend['이론금액'] / trend['실제금액'] * 100).round(2)
                        trend['표시월'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        fig_line = px.line(trend, x='표시월', y='수율', color='연도', markers=True, 
                                           color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                        fig_line.update_layout(height=250, margin=dict(l=0,r=0,t=20,b=0), font=dict(size=11))
                        st.plotly_chart(fig_line, use_container_width=True, key=f"line_{d}")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 3] 분석 지표 현황 (2열 정렬) ---
        col1, col2 = st.columns(2)
        
        with col1: # 자재 유형별 바 차트
            st.markdown('<div class="dashboard-card"><div class="section-header">📊 자재 유형별 성적 비교</div>', unsafe_allow_html=True)
            mat_choice = st.selectbox("자재 선택", ["원자재", "부자재", "반제품"], key="mat_box")
            m_df = team_df[team_df['자재 유형 내역'] == mat_choice].groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
            m_df['수율'] = (m_df['이론금액'] / m_df['실제금액'] * 100).round(2)
            fig_bar = px.bar(m_df, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', 
                             color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
            fig_bar.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0), yaxis=dict(range=[80, 105]))
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2: # 리스크 매트릭스
            st.markdown('<div class="dashboard-card"><div class="section-header">🔍 수율 리스크 매트릭스</div>', unsafe_allow_html=True)
            sc_dept = st.selectbox("부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="sc_box")
            plot_df = team_df.copy() if sc_dept == "전체 1팀" else team_df[team_df['생산부문명'] == sc_dept].copy()
            item_sc = plot_df.groupby(['연도', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_sc['수율'] = (item_sc['이론금액'] / item_sc['실제금액'] * 100).round(2)
            item_sc['금액(억)'] = item_sc['실제금액'] / 100000000
            fig_sc = px.scatter(item_sc, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', 
                                color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
            fig_sc.add_hline(y=100.0, line_dash="dash", line_color="gray")
            fig_sc.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_sc, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 4] 중점 관리 품목 Top 5 ---
        st.markdown('<div class="dashboard-card"><div class="section-header">🚨 중점 관리 대상 (수율 하위 Top 5)</div>', unsafe_allow_html=True)
        
        # 하단 미니 필터 바 적용
        if "top5_view" not in st.session_state: st.session_state["top5_view"] = "📊 선택한 기간 전체 누적 데이터"
        
        c1, c2, c3 = st.columns([33, 12, 55])
        view_mode = c1.radio("레이블 숨김", ["📊 선택한 기간 전체 누적 데이터", "🎯 특정 년월 단독 데이터"], horizontal=True, label_visibility="collapsed", key="top5_view")
        t_month = c2.selectbox("월 선택", options=sorted(selected_months), label_visibility="collapsed") if "특정" in view_mode else None
        
        tab_26_top, tab_25_top = st.tabs(["2026년 집중 품목", "2025년 참고 품목"])
        for yr_label, current_top_tab in [("26년 누적", tab_26_top), ("25년 누적", tab_25_top)]:
            with current_top_tab:
                yr_df = team_df[team_df['월'] == t_month] if t_month else team_df[team_df['연도'] == yr_label]
                if not yr_df.empty:
                    top_sum = yr_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                    top_sum['수율'] = (top_sum['이론금액'] / top_sum['실제금액'] * 100).round(2)
                    tc1, tc2 = st.columns(2)
                    for i, d_name in enumerate(['면 1과', '면 5과']):
                        with [tc1, tc2][i]:
                            d_top = top_sum[top_sum['생산부문명'] == d_name].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                            fig_top = px.bar(d_top, x='수율', y='하위품목 텍스트', orientation='h', text='수율', color_discrete_sequence=[MAIN_BLUE if "26" in yr_label else COMP_GRAY])
                            fig_top.update_layout(height=350, margin=dict(l=0,r=10,t=10,b=10), yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_top, use_container_width=True, key=f"top_{yr_label}_{d_name}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ 사이드바에서 년월을 선택해 주세요.")
