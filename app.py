import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. 전역 데이터 소스 및 설정
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = [
    "25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
    "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
    "26.01", "26.02", "26.03", "26.04"
]

YIELD_THRESHOLD = {'면 1과': 98.92, '면 5과': 97.93, '스프실': 99.53, '전체 총합': 98.73}

MAIN_BLUE = "#3B82F6"       
COMP_GRAY = "#94A3B8"       
ALERT_RED = "#EF4444"       
SUCCESS_GREEN = "#10B981"   

st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

# CSS 스타일링
st.markdown(f"""
    <style>
        .stApp {{ background-color: #F8FAFC; }}
        .premium-divider {{
            height: 2px;
            background: linear-gradient(to right, {MAIN_BLUE}, rgba(148, 163, 184, 0.3), rgba(0,0,0,0));
            margin: 40px 0 25px 0;
            border-radius: 2px; opacity: 0.8;
        }}
        .section-header {{
            display: flex; align-items: center; margin-bottom: 20px;
            padding-left: 10px; border-left: 5px solid {MAIN_BLUE};
        }}
        .section-header h2 {{ margin: 0 !important; font-size: 24px !important; font-weight: 800 !important; color: #1E293B !important; }}
        .mes-kpi-wrapper {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 5px; }}
        .mes-kpi-card {{ 
            background-color: white; color: #1E293B; border: 1px solid #E2E8F0;
            border-radius: 12px; padding: 18px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        }}
        .mes-kpi-label {{ font-size: 14px; font-weight: 700; color: #64748B; margin-bottom: 6px; }}
        .mes-kpi-value-box {{ display: flex; align-items: baseline; }}
        .mes-kpi-value {{ font-size: 32px; font-weight: 800; line-height: 1.1; }}
        .mes-kpi-unit {{ font-size: 15px; font-weight: 600; color: #64748B; margin-left: 5px; }}
        .mes-kpi-status {{ font-size: 13px; font-weight: 700; margin-top: 8px; }}
        div[data-testid="stRadio"] {{ margin-top: -55px !important; padding-top: 0 !important; }}
        @media (prefers-color-scheme: dark) {{
            .stApp {{ background-color: #0E1117; }}
            .mes-kpi-card {{ background-color: #1A1C23; color: #F1F5F9; border: 1px solid #2D2F39; }}
            .section-header h2 {{ color: #F1F5F9 !important; }}
        }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 시스템 세션 제어
# ------------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

def login():
    if st.session_state.username == "busan1" and st.session_state.password == "team1234":
        st.session_state['logged_in'] = True
    else: st.error("⚠️ 아이디 또는 비밀번호가 틀렸습니다.")

# ------------------------------------------------------------------------------
# 데이터 로드
# ------------------------------------------------------------------------------
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy(); df['월'] = month_label
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {'生産部門명': '생산부문명', '生産部門名': '생산부문명', '資재 유형 내역': '자재 유형 내역', '資재 유형내역': '자재 유형 내역', '品목텍스트': '하위품목 텍스트', '품목 텍스트': '하위품목 텍스트', '理論金額': '이론금액', '實際金額': '실제금액'}
    df.rename(columns=rename_map, inplace=True)
    if '생산부문명' in df.columns:
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실', '면 1과': '면 1과', '면 5과': '면 5과', '스프실': '스프실'}
        df = df[df['생산부문명'].isin(dept_map.keys())].copy()
        df['생산부문명'] = df['생산부문명'].map(dept_map)
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
    return df

@st.cache_data(ttl=3600)
def load_single_month_cached(sheet_id, m):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(m)}"
        return preprocess_df(pd.read_csv(url), m)
    except: return pd.DataFrame()

# ------------------------------------------------------------------------------
# 4. 앱 레이아웃
# ------------------------------------------------------------------------------
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.subheader("🔐 시스템 로그인")
        st.text_input("아이디", key="username")
        st.text_input("비밀번호", type="password", key="password")
        st.button("로그인", on_click=login, use_container_width=True)
else:
    with st.sidebar:
        st.header("⚙️ SYSTEM ADMIN")
        st.markdown("<div style='color: #64748B; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; margin-top: -10px; margin-bottom: 20px;'>BUSAN PLANT PRODUCTION TEAM 1</div>", unsafe_allow_html=True)
        st.button("🔓 로그아웃", on_click=lambda: st.session_state.update({'logged_in': False}), use_container_width=True)
        st.markdown("---")
        selected_months = st.multiselect("🗓️ 관제 대상 년월", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
        st.markdown("---")
        search_keyword = st.text_input("🔍 품목 필터 검색", placeholder="품목명을 입력하세요...")

    h_left, h_right = st.columns([4.5, 1])
    with h_left:
        st.markdown(f"""
            <div style="color: {MAIN_BLUE}; font-size: 12px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px;">MES INTEGRATED OPERATIONAL MONITORING</div>
            <h1 style="color: var(--text-color); font-size: 42px; font-weight: 800; margin: 0; padding: 0; line-height: 1.1;">
                생산1팀 <span style="color:{MAIN_BLUE};">Smart 수율 모니터링</span> Portal
            </h1>
        """, unsafe_allow_html=True)
    with h_right:
        st.markdown(f"""
            <div style='text-align: right; margin-top: 15px;'>
                <div style='background: white; color: {MAIN_BLUE}; padding: 8px 18px; border-radius: 8px; font-weight: 800; display: inline-block; font-size: 14px; border: 1px solid {MAIN_BLUE}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>● SYSTEM LIVE</div>
                <div style='color: #94A3B8; font-size: 11px; margin-top: 10px; font-weight: 600;'>Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    if selected_months:
        active_dfs = [load_single_month_cached(SHEET_ID, m) for m in selected_months]
        active_dfs = [d for d in active_dfs if not d.empty]
        if active_dfs:
            team_df = pd.concat(active_dfs, ignore_index=True)
            team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
            if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

            # KPI 연산
            df_26_kpi = team_df[team_df['연도'] == '26년 누적']
            if not df_26_kpi.empty:
                k_th, k_ac = df_26_kpi['이론금액'].sum(), df_26_kpi['실제금액'].sum()
                total_26_yd = (k_th / k_ac * 100) if k_ac > 0 else 0
                cost_billion = k_ac / 100000000 
                agg_items = df_26_kpi.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
                agg_items['수율'] = (agg_items['이론금액'] / agg_items['실제금액'] * 100)
                risk_cnt = len(agg_items[(agg_items['실제금액'] >= 400000000) & (agg_items['수율'] <= 98.0)])
            else: total_26_yd, cost_billion, risk_cnt = 0, 0, 0

            kpi_color = SUCCESS_GREEN if total_26_yd >= YIELD_THRESHOLD['전체 총합'] else ALERT_RED
            kpi_text = "▲ 목표 달성" if total_26_yd >= YIELD_THRESHOLD['전체 총합'] else "▼ 목표 미달"

            st.markdown(f"""
                <div class="mes-kpi-wrapper">
                    <div class="mes-kpi-card" style="border-top: 4px solid {kpi_color};">
                        <div class="mes-kpi-label">종합 수율</div>
                        <div class="mes-kpi-value-box"><span class="mes-kpi-value">{total_26_yd:.2f}</span><span class="mes-kpi-unit">%</span></div>
                        <div class="mes-kpi-status" style="color: {kpi_color};">{kpi_text}</div>
                    </div>
                    <div class="mes-kpi-card" style="border-top: 4px solid {MAIN_BLUE};">
                        <div class="mes-kpi-label">누적 실제 투입 금액</div>
                        <div class="mes-kpi-value-box"><span class="mes-kpi-value">{cost_billion:,.1f}</span><span class="mes-kpi-unit">억 원</span></div>
                        <div class="mes-kpi-status" style="color: #64748B;">생산 운영 스케일</div>
                    </div>
                    <div class="mes-kpi-card" style="border-top: 4px solid {ALERT_RED};">
                        <div class="mes-kpi-label">고위험 자재 건수</div>
                        <div class="mes-kpi-value-box"><span class="mes-kpi-value" style="color: {ALERT_RED};">{risk_cnt:02d}</span><span class="mes-kpi-unit">건</span></div>
                        <div class="mes-kpi-status" style="color: {ALERT_RED};">⚠️ 즉시 집중 점검 필요</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><h2>📋 생산1팀 수율 종합 상황판</h2></div>', unsafe_allow_html=True)
            
            tabs = st.tabs(['면 1과', '면 5과', '스프실', '전체 총합'])
            for i, d in enumerate(['면 1과', '면 5과', '스프실', '전체 총합']):
                with tabs[i]:
                    c1, c2 = st.columns(2)
                    target = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    with c1:
                        if not target.empty:
                            summ = target.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            summ['수율'] = (summ['이론금액'] / summ['실제금액'] * 100)
                            pivot = summ.pivot(index='자재 유형 내역', columns='연도', values='수율')
                            
                            def style_yield_cells(val):
                                try:
                                    v = float(val)
                                    if v > 0 and v < YIELD_THRESHOLD[d]:
                                        return f'color: {ALERT_RED}; background-color: rgba(239, 68, 68, 0.15);'
                                    else:
                                        return 'background-color: rgba(74, 144, 226, 0.12);'
                                except: return ''
                                
                            # ★ 오류 수정: applymap 대신 map 사용
                            styled_df = pivot.style.format('{:.2f}%').map(style_yield_cells)
                            st.dataframe(styled_df, use_container_width=True)
                        st.markdown(f"<div style='color: #64748B; font-size: 13px; font-weight: 700; margin-top: -12px; margin-bottom: 10px; padding-left: 5px;'>💡 {d} 기준 : {YIELD_THRESHOLD[d]:.2f}% 이상</div>", unsafe_allow_html=True)
                    with c2:
                        st.write("📈 상세 추이 생략 (상단 차트 로직과 동일 적용 가능)")
