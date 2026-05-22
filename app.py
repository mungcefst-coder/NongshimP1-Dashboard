import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# ==============================================================================
# [1] ERP 포털 스타일 시스템 디자인 (CSS Injection)
# ==============================================================================
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관제 포털")

st.markdown("""
    <style>
        /* 시스템 전체 배경 */
        .stApp {
            background-color: #F1F5F9;
        }
        
        /* 카드형 레이아웃 박스 */
        .portal-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 4px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        /* 섹션 헤더 디자인 (왼쪽 블루 포인트) */
        .section-header {
            font-size: 16px;
            font-weight: 700;
            color: #1E293B;
            border-left: 4px solid #1E40AF;
            padding-left: 12px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }
        
        /* KPI 타이틀 크기 고도화 (18px 요청 반영) */
        div[data-testid="stMetricLabel"] p {
            font-size: 18px !important;
            font-weight: bold !important;
            color: #475569 !important;
            margin-bottom: 8px !important;
        }
        
        /* KPI 수치 디자인 */
        div[data-testid="stMetricValue"] div {
            font-size: 36px !important;
            font-weight: 800 !important;
            color: #1E40AF !important;
            letter-spacing: -1px;
        }
        
        /* 데이터 테이블 정돈 */
        .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 4px;
        }
        
        /* 하단 미니 필터 바 */
        .bottom-filter-label {
            font-size: 12px;
            font-weight: bold;
            color: #64748B;
            margin-bottom: -15px;
        }
        div[data-testid="stRadio"] label span {
            font-size: 12.5px !important;
        }

        /* 탭 가독성 */
        .stTabs [data-baseweb="tab"] p {
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

YIELD_THRESHOLD = {'면 1과': 98.92, '면 5과': 97.93, '스프실': 99.53, '전체 총합': 98.73}
MAIN_BLUE = "#1E40AF"
COMP_GRAY = "#94A3B8"
ALERT_RED = "#E74C3C"

# ==============================================================================
# [3] 데이터 엔진 및 로직
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
def load_cached_data(sheet_id, month):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(month)}"
        return preprocess_df(pd.read_csv(url), month)
    except: return pd.DataFrame()

# ==============================================================================
# [4] 사이드바 & 시스템 헤더
# ==============================================================================
with st.sidebar:
    st.markdown("### 🏢 System Control")
    selected_months = st.multiselect("분석 기간 설정", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    search_keyword = st.text_input("🔍 품목 필터링", placeholder="품목명 입력")

st.title("🛡️ 통합 수율 관리 분석 포털 (Yield Portal)")
st.markdown("<p style='color:#64748B; margin-top:-15px; margin-bottom:25px;'>생산 1팀 핵심 제조 공정 데이터 모니터링 시스템</p>", unsafe_allow_html=True)

# ==============================================================================
# [5] 메인 관제 레이아웃
# ==============================================================================
if selected_months:
    active_dfs = [load_cached_data(SHEET_ID, m) for m in selected_months]
    team_df = pd.concat([d for d in active_dfs if not d.empty], ignore_index=True)
    
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- [1단] 핵심 지표 KPI 카드 ---
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        k_col1, k_col2, k_col3 = st.columns(3)
        df_26 = team_df[team_df['연도'] == '26년 누적']
        if not df_26.empty:
            th, ac = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            y_val = (th / ac * 100) if ac > 0 else 0
            k_col1.metric("📈 2026 종합 수율", f"{y_val:.2f}%", "정상 가동 중")
            k_col2.metric("💰 누적 투입 금액", f"{ac/100000000:,.1f} 억", "생산 규모")
            risk_cnt = len(df_26.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().query('실제금액 >= 400000000 and (이론금액/실제금액*100) <= 98.0'))
            k_col3.metric("🚨 고위험 자재 수", f"{risk_cnt} 건", "집중 검토 요망" if risk_cnt > 0 else "안정", delta_color="inverse")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [2단] 부문별 상세 수율 (탭 인터페이스) ---
        st.markdown('<div class="portal-card"><div class="section-header">📋 부문별 관리 현황 상세</div>', unsafe_allow_html=True)
        depts = ['면 1과', '면 5과', '스프실', '전체 총합']
        selected_tabs = st.tabs(depts)
        for idx, d in enumerate(depts):
            with selected_tabs[idx]:
                c_left, c_right = st.columns([50, 50])
                t_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                with c_left:
                    if not t_df.empty:
                        pivot = t_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        pivot['수율(%)'] = pivot['이론금액'] / pivot['실제금액'] * 100
                        display_df = pivot.pivot(index='자재 유형 내역', columns='연도', values='수율(%)')
                        st.dataframe(display_df.style.format("{:.2f}%").set_properties(**{'background-color': 'rgba(30, 64, 175, 0.05)'}), use_container_width=True)
                        st.markdown(f"<span style='font-size:12px; color:#64748B;'>※ {d} 목표: {YIELD_THRESHOLD[d]}%</span>", unsafe_allow_html=True)
                with c_right:
                    if not t_df.empty:
                        trend = t_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index()
                        trend['수율'] = (trend['이론금액'] / trend['실제금액'] * 100).round(2)
                        trend['표시월'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        fig_line = px.line(trend, x='표시월', y='수율', color='연도', markers=True, color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                        fig_line.update_layout(height=230, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=11))
                        st.plotly_chart(fig_line, use_container_width=True, key=f"line_{d}")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [3단] 분석 차트 그리드 (자재별/리스크) ---
        col_bar, col_risk = st.columns([50, 50])
        with col_bar:
            st.markdown('<div class="portal-card"><div class="section-header">📊 자재 유형별 실적 비교</div>', unsafe_allow_html=True)
            mat_opt = st.selectbox("조회 대상 선택", ["원자재", "부자재", "반제품"], key="mat_select")
            m_df = team_df[team_df['자재 유형 내역'] == mat_opt].groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
            m_df['수율'] = (m_df['이론금액'] / m_df['실제금액'] * 100).round(2)
            fig_bar = px.bar(m_df, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
            fig_bar.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[80, 105]), font=dict(size=11))
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_risk:
            st.markdown('<div class="portal-card"><div class="section-header">🔍 수율 리스크 매트릭스</div>', unsafe_allow_html=True)
            risk_dept = st.selectbox("부서 필터", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="risk_select")
            r_df = team_df.copy() if risk_dept == "전체 1팀" else team_df[team_df['생산부문명'] == risk_dept].copy()
            item_r = r_df.groupby(['연도', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_r['수율'] = (item_r['이론금액'] / item_r['실제금액'] * 100).round(2)
            item_r['금액(억)'] = item_r['실제금액'] / 100000000
            fig_sc = px.scatter(item_r, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
            fig_sc.add_hline(y=100.0, line_dash="dash", line_color="#94A3B8")
            fig_sc.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), font=dict(size=11))
            st.plotly_chart(fig_sc, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [4단] 중점 관리 품목 Top 5 ---
        st.markdown('<div class="portal-card"><div class="section-header">🚨 중점 관리 품목 (수율 하위 Top 5)</div>', unsafe_allow_html=True)
        t26, t25 = st.tabs(["2026년 집중 분석", "2025년 이력 참조"])
        
        # 하단 미니 필터 바 레이아웃
        if "v_mode" not in st.session_state: st.session_state["v_mode"] = "📊 선택한 기간 전체 누적 데이터"
        f_col1, f_col2, f_col3 = st.columns([33, 15, 52])
        v_mode = f_col1.radio("range", ["📊 선택한 기간 전체 누적 데이터", "🎯 특정 년월 단독 데이터"], horizontal=True, label_visibility="collapsed", key="v_mode")
        target_m = f_col2.selectbox("month", options=sorted(selected_months), label_visibility="collapsed") if "특정" in v_mode else None
        
        for yr_tag, current_tab in [("26년 누적", t26), ("25년 누적", t25)]:
            with current_tab:
                y_df = team_df[team_df['월'] == target_m] if target_m else team_df[team_df['연도'] == yr_tag]
                if not y_df.empty:
                    top_sum = y_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                    top_sum['수율'] = (top_sum['이론금액'] / top_sum['실제금액'] * 100).round(2)
                    tc1, tc2 = st.columns(2)
                    for i, d_n in enumerate(['면 1과', '면 5과']):
                        with [tc1, tc2][i]:
                            d_top = top_sum[top_sum['생산부문명'] == d_n].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                            fig_top = px.bar(d_top, x='수율', y='하위품목 텍스트', orientation='h', text='수율', color_discrete_sequence=[MAIN_BLUE if "26" in yr_tag else COMP_GRAY])
                            fig_top.update_layout(height=320, margin=dict(l=0,r=10,t=10,b=10), yaxis={'categoryorder':'total ascending'}, font=dict(size=10))
                            st.plotly_chart(fig_top, use_container_width=True, key=f"bar_{yr_tag}_{d_n}")
                else: st.caption("데이터가 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ 사이드바에서 분석 기간을 선택해 주세요.")
