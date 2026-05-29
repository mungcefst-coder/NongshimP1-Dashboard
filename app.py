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

YIELD_THRESHOLD = {
    '면 1과': 98.92, 
    '면 5과': 97.93, 
    '스프실': 99.53,
    '면 종합': 98.42, 
    '전체 총합': 98.73
}

MAIN_BLUE = "#3B82F6"       
COMP_GRAY = "#94A3B8"       
ALERT_RED = "#EF4444"       
SUCCESS_GREEN = "#10B981"   
BRAND_NAVY = "#1E40AF"      

st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 System")

# 프리미엄 다크/그레이 톤 배경 및 기본 대시보드 컴포넌트 CSS 스타일 정의
st.markdown(f"""
    <style>
        /* 🎨 전체 배경을 세련된 딥 네이비 그라데이션 야간 모드로 변경 */
        .stApp {{
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }}
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
        /* 야간 모드에 잘 보이도록 메인 텍스트 색상을 화이트 계열로 조정 */
        .section-header h2 {{ margin: 0 !important; font-size: 24px !important; font-weight: 800 !important; color: #F1F5F9 !important; }}
        .mes-kpi-wrapper {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 5px; }}
        .mes-kpi-card {{ 
            background-color: rgba(255, 255, 255, 0.05); color: #F1F5F9; border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px; padding: 18px 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); backdrop-filter: blur(8px);
        }}
        .mes-kpi-label {{ font-size: 14px; font-weight: 700; color: #94A3B8; margin-bottom: 6px; }}
        .mes-kpi-value-box {{ display: flex; align-items: baseline; }}
        .mes-kpi-value {{ font-size: 32px; font-weight: 800; line-height: 1.1; }}
        .mes-kpi-unit {{ font-size: 15px; font-weight: 600; color: #94A3B8; margin-left: 5px; }}
        .mes-kpi-status {{ font-size: 13px; font-weight: 700; margin-top: 8px; }}
        div[data-testid="stRadio"] {{ margin-top: -55px !important; padding-top: 0 !important; }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. 이원화 로그인 시스템 세션 제어
# ------------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'is_admin' not in st.session_state: st.session_state['is_admin'] = False

def login():
    uid = st.session_state.username
    upw = st.session_state.password
    if uid == "admin" and upw == "admin5678":
        st.session_state['logged_in'] = True
        st.session_state['is_admin'] = True
    elif uid == "busan1" and upw == "team1234":
        st.session_state['logged_in'] = True
        st.session_state['is_admin'] = False
    else: 
        st.error("⚠️ 아이디 또는 비밀번호가 올바르지 않습니다.")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['is_admin'] = False

# ------------------------------------------------------------------------------
# 3. 데이터 로드 및 전처리 로직
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
        df['생산부문명'] = df['생산부num명'].map(dept_map) if '생산부num명' in df.columns else df['생산부문명'].map(dept_map)
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
# 4. 라우터 (개선된 유리 질감 로그인 UI 연결)
# ------------------------------------------------------------------------------
if not st.session_state['logged_in']:
    # 🎨 유리 질감(Glassmorphism) 카드 전용 커스텀 CSS 적용
    st.markdown("""
        <style>
            .glass-login-card {
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                text-align: center;
                margin-top: 10vh;
            }
            .card-title {
                color: #FFFFFF !important;
                font-size: 28px !important;
                font-weight: 800 !important;
                margin-bottom: 4px !important;
                letter-spacing: -0.5px;
            }
            .card-subtitle {
                color: #94A3B8 !important;
                font-size: 11px !important;
                font-weight: 700 !important;
                letter-spacing: 1.5px;
                margin-bottom: 30px !important;
            }
            div[data-testid="stForm"] {
                border: none !important;
                padding: 0 !important;
                background: transparent !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 🏢 레이아웃 중앙 정렬 배치
    _, login_container, _ = st.columns([1, 1.2, 1])
    
    with login_container:
        st.markdown("""
            <div class="glass-login-card">
                <div class="card-title">🔐 SYSTEM ACCESS</div>
                <div class="card-subtitle">BUSAN PLANT PRODUCTION TEAM 1</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 입력 양식 컨테이너
        with st.form("login_form"):
            st.text_input("Username", key="username", placeholder="ID를 입력하세요")
            st.text_input("Password", type="password", key="password", placeholder="PW를 입력하세요")
            st.form_submit_button("보안 시스템 로그인", on_click=login, use_container_width=True)
else:
    # --------------------------------------------------------------------------
    # 5. 메인 대시보드 구역 (로그인 완료 시 구동)
    # --------------------------------------------------------------------------
    with st.sidebar:
        if st.session_state['is_admin']:
            st.markdown("<span style='background-color:#EF4444; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;'>MASTER ADMIN</span>", unsafe_allow_html=True)
            st.markdown("### 🎯 관리자 전용: 목표 설정")
            adm_m1 = st.number_input("면 1과 목표수율(%)", value=98.92, step=0.01)
            adm_m5 = st.number_input("면 5과 목표수율(%)", value=97.93, step=0.01)
            adm_sp = st.number_input("스프실 목표수율(%)", value=99.53, step=0.01)
            adm_mtot = st.number_input("면 종합 통합 목표(%)", value=98.42, step=0.01)
            adm_tot = st.number_input("전체 총합 목표(%)", value=98.73, step=0.01)
            YIELD_THRESHOLD = {'면 1과': adm_m1, '면 5과': adm_m5, '스프실': adm_sp, '면 종합': adm_mtot, '전체 총합': adm_tot}
            st.markdown(f"[📂 구글 시트 원본](https://docs.google.com/spreadsheets/d/{SHEET_ID})")
            st.markdown("---")
        else:
            st.markdown("<span style='background-color:#3B82F6; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;'>TEAM MEMBER</span>", unsafe_allow_html=True)
            YIELD_THRESHOLD = {'면 1과': 98.92, '면 5과': 97.93, '스프실': 99.53, '면 종합': 98.42, '전체 총합': 98.73}

        st.header("⚙️ SYSTEM ADMIN")
        st.markdown("<div style='color: #94A3B8; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; margin-top: -10px; margin-bottom: 20px;'>BUSAN PLANT PRODUCTION TEAM 1</div>", unsafe_allow_html=True)
        st.button("🔓 로그아웃", on_click=logout, use_container_width=True)
        st.markdown("---")
        selected_months = st.multiselect("🗓️ 관제 대상 년월", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
        st.markdown("---")
        search_keyword = st.text_input("🔍 품목 필터 검색", placeholder="품목명을 입력하세요...")

    # 대시보드 헤더 영역 설정 (텍스트 컬러 화이트 최적화)
    h_left, h_right = st.columns([4.5, 1])
    with h_left:
        st.markdown(f"""
            <div style="color: {MAIN_BLUE}; font-size: 12px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px;">MES INTEGRATED OPERATIONAL MONITORING</div>
            <h1 style="color: #F8FAFC; font-size: 42px; font-weight: 800; margin: 0; padding: 0; line-height: 1.1;">
                생산1팀 <span style="color:{MAIN_BLUE};">Smart 수율 모니터링</span> System
            </h1>
        """, unsafe_allow_html=True)
    with h_right:
        st.markdown(f"""
            <div style='text-align: right; margin-top: 15px;'>
                <div style='background: rgba(255,255,255,0.05); color: {MAIN_BLUE}; padding: 8px 18px; border-radius: 8px; font-weight: 800; display: inline-block; font-size: 14px; border: 1px solid {MAIN_BLUE}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>● SYSTEM LIVE</div>
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

            # KPI 연산 부문
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
                        <div class="mes-kpi-status" style="color: #94A3B8;">생산 운영 스케일</div>
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
            
            departments = ['면 1과', '면 5과', '스프실', '면 종합', '전체 총합']
            tabs = st.tabs(departments)
            for i, d in enumerate(departments):
                with tabs[i]:
                    c1, c2 = st.columns(2)
                    if d == '전체 총합': target = team_df
                    elif d == '면 종합': target = team_df[team_df['생산부문명'].isin(['면 1과', '면 5과'])]
                    else: target = team_df[team_df['생산부문명'] == d]
                        
                    with c1:
                        st.markdown(f"**📊 {d} 상세 실적**")
                        if not target.empty:
                            summ = target.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            extra_rows = []
                            for yr in summ['연도'].unique():
                                yr_data = summ[summ['연도'] == yr]
                                rb_data = yr_data[yr_data['자재 유형 내역'].isin(['원자재', '부자재'])]
                                if not rb_data.empty: 
                                    extra_rows.append({'연도': yr, '자재 유형 내역': '원부자재 수율', '이론금액': rb_data['이론금액'].sum(), '실제금액': rb_data['실제금액'].sum()})
                                extra_rows.append({'연도': yr, '자재 유형 내역': '전체 수율', '이론금액': yr_data['이론금액'].sum(), '실제금액': yr_data['실제금액'].sum()})
                            summ = pd.concat([summ, pd.DataFrame(extra_rows)], ignore_index=True)
                            summ['수율'] = (summ['이론금액'] / summ['실제금액'] * 100)
                            
                            pivot = summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율'])
                            reorder_cols = [(v, y) for y in ['25년 누적', '26년 누적'] for v in ['이론금액', '실제금액', '수율']]
                            pivot = pivot.reindex(columns=reorder_cols, fill_value=0)
                            pivot.columns = [f"{yr[:3]} {v}" for v, yr in pivot.columns]
                            pivot = pivot.reindex(['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율'])
                            
                            current_threshold = YIELD_THRESHOLD[d]
                            yield_cols = [c for c in pivot.columns if '수율' in c]
                            styled_df = pivot.style.format({c: '{:,.2f}%' if '수율' in c else '{:,.0f}' for c in pivot.columns})
                            
                            def style_yield_cells(val):
                                try:
                                    v = float(val)
                                    if v > 0 and v < current_threshold:
                                        return f'color: {ALERT_RED}; background-color: rgba(239, 68, 68, 0.15);'
                                    else: return 'background-color: rgba(74, 144, 226, 0.12);'
                                except: return 'background-color: rgba(74, 144, 226, 0.12);'
                                
                            styled_df = styled_df.map(style_yield_cells, subset=yield_cols)
                            st.dataframe(styled_df, use_container_width=True)
                        else: st.caption("데이터 없음")
                        
                        st.markdown(f"<div style='color: #94A3B8; font-size: 13px; font-weight: 700; margin-top: -12px; margin-bottom: 10px; padding-left: 5px;'>💡 {d} 기준 : {YIELD_THRESHOLD[d]:.2f}% 이상</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**📈 {d} 수율 변화 추이**")
                        if not target.empty:
                            trend = target.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index()
                            trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                            trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                            trend_piv = trend.pivot(index='월표시', columns='연도', values='누적수율').reset_index()
                            
                            fig = go.Figure()
                            for yr_label in sorted(trend['연도'].unique()):
                                y_data = trend[trend['연도'] == yr_label].copy().sort_values('월')
                                text_positions = []
                                for idx, row in y_data.iterrows():
                                    m_lbl = row['월표시']
                                    current_val = row['누적수율']
                                    match_row = trend_piv[trend_piv['월표시'] == m_lbl]
                                    if not match_row.empty and '25년 누적' in trend_piv.columns and '26년 누적' in trend_piv.columns:
                                        val_25 = match_row['25년 누적'].values[0]
                                        val_26 = match_row['26년 누적'].values[0]
                                        if yr_label == '26년 누적': text_positions.append('top center' if current_val >= val_25 else 'bottom center')
                                        else: text_positions.append('top center' if current_val > val_26 else 'bottom center')
                                    else: text_positions.append('top center' if yr_label == '26년 누적' else 'bottom center')
                                
                                fig.add_trace(go.Scatter(
                                    x=y_data['월표시'], y=y_data['누적수율'], name=yr_label, mode='markers+lines+text',
                                    text=y_data['누적수율'].apply(lambda x: f"{x:.2f}%"), 
                                    textposition=text_positions, textfont=dict(size=14, color='#F8FAFC', weight='bold'),
                                    line=dict(color=MAIN_BLUE if '26년' in yr_label else COMP_GRAY, width=4), marker=dict(size=10)
                                ))
                            y_min, y_max = trend['누적수율'].min(), trend['누적수율'].max()
                            fig.update_layout(height=280, margin=dict(l=100,r=80,t=40,b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), yaxis=dict(range=[y_min-3, y_max+3], gridcolor='rgba(255,255,255,0.1)', zeroline=False, ticksuffix="  "), xaxis=dict(type='category', range=[-0.5, len(trend['월표시'].unique())-0.5], gridcolor='rgba(255,255,255,0.1)'), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

            # --- 섹션 2: 실시간 비교 및 리스크 분석 ---
            st.markdown('<div class="section-header"><h2>📊 실시간 비교 및 리스크 분석</h2></div>', unsafe_allow_html=True)
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                st.markdown("**📍 부문별 수율 비교**")
                s_col1, _ = st.columns([0.45, 0.55])
                with s_col1: m_opt = st.selectbox("조회 자재 선택", ["원자재", "부자재", "반제품"], key="m_opt")
                f_df = team_df[team_df['자재 유형 내역'] == m_opt]
                if not f_df.empty:
                    ds = f_df.groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
                    ds['수율'] = (ds['이론금액'] / ds['실제금액'] * 100).round(2)
                    fig1 = px.bar(ds, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                    fig1.update_traces(texttemplate='%{text:.2f}%', textposition='outside', textfont=dict(weight='bold', size=13, color='#F8FAFC'))
                    fig1.update_layout(height=330, margin=dict(l=80, r=20, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), yaxis=dict(range=[ds['수율'].min()-5, 105], gridcolor='rgba(255,255,255,0.1)'), xaxis_title=None)
                    st.plotly_chart(fig1, use_container_width=True)
            with r2c2:
                st.markdown("**🔍 수율 리스크 매트릭스**")
                s_col3, _ = st.columns([0.45, 0.55])
                with s_col3: s_dept = st.selectbox("조회 부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="s_dept")
                p_df = team_df.copy() if s_dept == "전체 1팀" else team_df[team_df['생산부문명'] == s_dept].copy()
                if not p_df.empty:
                    isc = p_df.groupby(['연도', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                    isc['수율'] = (isc['이론금액'] / isc['실제금액'] * 100).round(2); isc['억'] = isc['실제금액'] / 100000000
                    def amc(row):
                        if row['연도'] == '26년 누적' and row['억'] >= 4.0 and row['수율'] <= 98.0: return '🚨 집중 관리 대상'
                        return row['연도']
                    isc['분류'] = isc.apply(amc, axis=1)
                    fig3 = px.scatter(isc, x='억', y='수율', color='분류', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE, '🚨 집중 관리 대상': ALERT_RED})
                    fig3.update_traces(marker=dict(size=15, line=dict(width=1, color='white')))
                    fig3.update_layout(height=330, margin=dict(l=80, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), xaxis_title="투입 금액 (억원)", yaxis_title="수율 (%)", gridcolor='rgba(255,255,255,0.1)', legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02))
                    st.plotly_chart(fig3, use_container_width=True)

            st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

            # --- 섹션 3: 리스크 리스트 ---
            st.markdown('<div class="section-header"><h2>🚨 집중 관리 자재 리스크 Top 5</h2></div>', unsafe_allow_html=True)
            chart_block = st.container()
            v_m = st.radio("📊 데이터 조회 방식 선택", ["📊 선택 기간 전체 누적", "🎯 특정 년월 단독"], horizontal=True)
            if v_m == "🎯 특정 년월 단독":
                s_col_filter, _ = st.columns([0.3, 0.7])
                with s_col_filter: t_m = st.selectbox("📅 분석 대상 년월 선택", options=sorted(selected_months))
            else: t_m = "전체"
            with chart_block:
                t26, t25 = st.tabs(["📅 2026년 실적 분석", "📅 2025년 실적 분석"])
                for ty, tc in [("26년 누적", t26), ("25년 누적", t25)]:
                    with tc:
                        ydf = team_df[team_df['월'] == t_m] if v_m == "🎯 특정 년월 단독" else team_df[team_df['연도'] == ty]
                        if not ydf.empty:
                            isum = ydf[ydf['생산부문명'] != '스프실'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                            isum['수율'] = (isum['이론금액'] / isum['실제금액'] * 100).round(2)
                            cc1, cc2 = st.columns(2)
                            for idx, d_name in enumerate(['면 1과', '면 5과']):
                                with [cc1, cc2][idx]:
                                    st.markdown(f"**📍 {d_name} 중점 관리 리스트**")
                                    m_d = isum[isum['생산부문명'] == d_name].sort_values('실제금액', ascending=False).head(15).sort_values('수율').head(5)
                                    fig_m = px.bar(m_d, x='수율', y='하위품목 텍스트', orientation='h', text='수율')
                                    fig_m.update_traces(marker_color=MAIN_BLUE if ty == "26년 누적" else COMP_GRAY, texttemplate='%{text:.2f}%', textposition='outside', textfont=dict(weight='bold', color='#F8FAFC'))
                                    fig_m.update_layout(height=340, margin=dict(l=150, r=60, t=20, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), xaxis=dict(range=[0, 140], gridcolor='rgba(255,255,255,0.1)'))
                                    st.plotly_chart(fig_m, use_container_width=True, key=f"t5_{ty}_{d_name}")
    else:
        st.warning("📂 분석 대상 년월을 선택해 주세요.")
