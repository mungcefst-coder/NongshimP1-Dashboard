import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 전역 데이터 소스 및 기준선 선언부 (원본 100% 유지)
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
    '전체 총합': 98.73
}

MAIN_BLUE = "#1E40AF"
COMP_GRAY = "#B0BEC5"
ALERT_RED = "#E74C3C"

# 1. 페이지 세팅
st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

# [유령 박스 완벽 차단 CSS 개편]
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* SaaS 스킨 배경 */
        .stApp { background-color: #F8FAFC !important; }
        html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
        
        /* 상단 헤더 고정 */
        header[data-testid="stHeader"] { background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; }
        
        /* 유령 박스 방지: 스트림릿 수직 블록 요소를 정교한 하얀색 카드로 자동 변환 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            padding: 10px;
            margin-bottom: 15px;
        }

        /* 탭 내부 타이틀 20px 확대 */
        .sub-header-text {
            font-size: 20px;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 15px;
            display: block;
        }

        /* 고해상도 KPI 타일 */
        .kpi-tile { text-align: left; padding: 10px 15px; }
        .kpi-label { font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 8px; }
        .kpi-value { font-size: 36px; font-weight: 800; color: #0F172A; line-height: 1; }
        .kpi-unit { font-size: 18px; color: #94A3B8; margin-left: 3px; }
        .kpi-trend { font-size: 13px; margin-top: 10px; font-weight: 700; }

        /* 오리지널 폰트 세팅 및 여백 최적화 유지 */
        .stTabs [data-baseweb="tab"] p { font-size: 14px !important; }
        .target-period { font-size: 13.5px !important; color: #64748B; font-weight: 600; }
        .dataframe, .paint-table td, .paint-table th { font-size: 14px !important; }
        .threshold-info { font-size: 14px; color: #475569; margin-top: 10px; font-weight: 700; }
        
        /* 시스템 기본 에러/안내 상자 완전 차단 */
        .stAlert, [data-testid="stNotification"] { display: none !important; }
        
        /* 사이드바 스타일 */
        section[data-testid="stSidebar"] { background-color: #1E293B !important; color: white; }
        section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] p { color: white; }
        .stDataFrame { margin-bottom: 0px; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 처리 로직 (절대 불변 원본)
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
    if '자재 유형 내역' in df.columns:
        df = df[df['자재 유형 내역'].isin(['원자재', '부자재', '반제품'])]
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    calc_yield = (df['이론금액'] / df['실제금액']) * 100
    df = df[~((df['실제금액'] > 0) & (calc_yield < 50))]
    return df

@st.cache_data(ttl=3600)
def load_single_month_cached(sheet_id, m):
    try:
        encoded_sheet = urllib.parse.quote(m)
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
        return preprocess_df(pd.read_csv(url), m)
    except: return pd.DataFrame()

# 사이드바 컨트롤러
with st.sidebar:
    st.markdown("<h2 style='color:white;'>📂 데이터 관제</h2>", unsafe_allow_html=True)
    selected_months = st.multiselect("분석할 년월(YY.MM) 선택", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    search_keyword = st.text_input("🔍 세부 품목 검색")

# 기간 텍스트 바인딩 준비
sorted_display_months = sorted(selected_months) if selected_months else []
period_text = f"📆 관제 기간: {', '.join(sorted_display_months)}" if sorted_display_months else ""

# --- [메인 헤더] ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 25px; border-bottom: 2px solid #E2E8F0; padding-bottom: 15px;">
        <div>
            <p style="color:#1E40AF; font-weight:700; letter-spacing:4px; margin-bottom:2px; font-size:11px;">MES INTEGRATED OPERATIONAL MONITORING</p>
            <h1 style="font-size: 34px; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -1.2px; line-height: 1.1;">
                생산1팀 <span style="color:#1E40AF;">Smart 수율 모니터링</span> Portal
            </h1>
        </div>
        <div style="text-align: right; padding-bottom: 5px;">
            <div class="target-period" style="margin-bottom: 10px;"><b>{period_text}</b></div>
            <div style="background: #E0E7FF; color: #1E40AF; padding: 6px 14px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #C7D2FE; display: inline-block;">
                <span style="color: #22C55E; animation: blink 1.5s infinite;">●</span> SYSTEM LIVE
            </div>
        </div>
    </div>
    <style>@keyframes blink {{ 0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }} }}</style>
""", unsafe_allow_html=True)

if selected_months:
    active_dfs = [load_single_month_cached(SHEET_ID, m) for m in selected_months]
    team_df = pd.concat([d for d in active_dfs if not d.empty], ignore_index=True)
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- [CARD 1: KPI 연산 구역] ---
        df_26_kpi = team_df[team_df['연도'] == '26년 누적']
        if not df_26_kpi.empty:
            kpi_th = df_26_kpi['이론금액'].sum()
            kpi_ac = df_26_kpi['실제금액'].sum()
            total_26_yield = (kpi_th / kpi_ac * 100) if kpi_ac > 0 else 0
            risk_item_df = df_26_kpi.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
            risk_item_df['items_yd'] = (risk_item_df['이론금액'] / risk_item_df['실제금액'] * 100)
            risk_count = len(risk_item_df[(risk_item_df['실제금액'] >= 400000000) & (risk_item_df['items_yd'] <= 98.0)])
        else: total_26_yield, kpi_ac, risk_count = 0, 0, 0

        # ⚡ [교정 패치] f-string 내 에러 원천 차단: 포맷 구문 분리 선행 가공 완료
        yield_display = f"{total_26_yield:.2f}" if total_26_yield > 0 else "-"
        cost_display = f"{kpi_ac/100000000:,.1f}" if kpi_ac > 0 else "-"

        # 대시보드 KPI 카드 레이아웃
        with st.container():
            kpi_l, kpi_c, kpi_r = st.columns(3)
            kpi_l.markdown(f'<div class="kpi-tile"><p class="kpi-label">📈 2026년 선택기간 종합 수율</p><div class="kpi-value">{yield_display}<span class="kpi-unit">%</span></div><p class="kpi-trend" style="color:#22C55E;">● 목표치 대조 관리 중</p></div>', unsafe_allow_html=True)
            kpi_c.markdown(f'<div class="kpi-tile"><p class="kpi-label">💰 2026년 누적 실제 투입 금액</p><div class="kpi-value">{cost_display}<span class="kpi-unit">억 원</span></div><p class="kpi-trend" style="color:#64748B;">● 생산 운영 스케일</p></div>', unsafe_allow_html=True)
            kpi_r.markdown(f'<div class="kpi-tile"><p class="kpi-label">🚨 4억 이상 고위험 자재 수</p><div class="kpi-value" style="color:{ALERT_RED if risk_count > 0 else "#22C55E"};">{risk_count}<span class="kpi-unit">개 품목</span></div><p class="kpi-trend" style="color:{ALERT_RED if risk_count > 0 else "#22C55E"};">{"⚠️ 집중 검토 요망" if risk_count > 0 else "✅ 안정권 유지"}</p></div>', unsafe_allow_html=True)

        # --- [CARD 2: 상황판 구역] ---
        with st.container():
            selected_dept_tab = st.tabs(['면 1과', '면 5과', '스프실', '전체 총합'])
            for i, d in enumerate(['면 1과', '면 5과', '스프실', '전체 총합']):
                with selected_dept_tab[i]:
                    tab_col1, tab_col2 = st.columns([63, 37])
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    with tab_col1:
                        st.markdown(f"<span class='sub-header-text'>📊 {d} 수율 지표</span>", unsafe_allow_html=True)
                        if not target_df.empty:
                            base_summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            total_rows = [{'연도': yr, '자재 유형 내역': '전체 수율', '이론금액': base_summ[base_summ['연도']==yr]['이론금액'].sum(), '실제금액': base_summ[base_summ['연도']==yr]['실제금액'].sum()} for yr in base_summ['연도'].unique()]
                            base_summ = pd.concat([base_summ, pd.DataFrame(total_rows)], ignore_index=True)
                            base_summ['수율(%)'] = (base_summ['이론금액'] / base_summ['실제금액'] * 100)
                            pivot_df = base_summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                            all_cols = [(v, yr) for yr in ['25년 누적', '26년 누적'] for v in ['이론금액', '실제금액', '수율(%)']]
                            pivot_df = pivot_df.reindex(columns=all_cols, fill_value=0)
                            pivot_df.columns = [f"{yr[:3]} {'수율' if v=='수율(%)' else v}" for yr, v in [(c[1], c[0]) for c in pivot_df.columns]]
                            pivot_df = pivot_df.reindex(['원자재', '부자재', '반제품', '전체 수율'])

                            def style_table(styler, thresh_val):
                                styler.set_properties(**{'background-color': '#FFFFFF', 'color': '#0F172A'})
                                styler.format({c: '{:,.0f}' for c in styler.columns if '수율' not in c})
                                for col in [c for c in styler.columns if '수율' in col]:
                                    styler.set_properties(subset=[col], **{'background-color': 'rgba(74, 144, 226, 0.18)'})
                                    styler.data[col] = styler.data[col].apply(lambda x: f"{x:.2f}%" if x > 0 else "-")
                                    styler.map(lambda v: 'color: #FF5252; font-weight: bold;' if '%' in str(v) and float(str(v).replace('%','')) < thresh_val else '', subset=[col])
                                return styler
                            st.dataframe(pivot_df.style.pipe(style_table, thresh_val=YIELD_THRESHOLD[d]), use_container_width=True)
                        st.markdown(f'<div class="threshold-info">📌 {d} 관리 기준 수율 : {YIELD_THRESHOLD[d]:.2f}% 이상</div>', unsafe_allow_html=True)
                    
                    with tab_col2:
                        st.markdown(f"<span class='sub-header-text'>📈 수율 변화 추이</span>", unsafe_allow_html=True)
                        if not target_df.empty:
                            tr = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                            tr['누적수율'] = (tr.groupby('연도')['이론금액'].cumsum() / tr.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                            tr['표시월'] = tr['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                            fig = go.Figure()
                            for yr in sorted(tr['연도'].unique()):
                                yd = tr[tr['연도'] == yr]
                                fig.add_trace(go.Scatter(x=yd['표시월'], y=yd['누적수율'], mode='markers+lines+text', name=yr, text=yd['누적수율'].apply(lambda x: f"{x}%"), textposition='top center', line=dict(color=MAIN_BLUE if '26' in yr else COMP_GRAY, width=3.5), marker=dict(size=8), textfont=dict(size=11, weight='bold')))
                            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(range=[tr['누적수율'].min()-1.5, tr['누적수율'].max()+1.5], gridcolor='#F1F5F9'), xaxis=dict(gridcolor='#F1F5F9'), legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1), hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig, use_container_width=True, key=f"tr_{d}")

        # --- [CARD 3: 하단 그래프/리스크 구역] ---
        low_l, low_r = st.columns(2)
        with low_l:
            with st.container():
                st.markdown('<span class="sub-header-text">📊 자재 유형별 수율 현황</span>', unsafe_allow_html=True)
                mat_choice = st.selectbox("조회 자재 선택", ["원자재", "부자재", "반제품"], key="m_opt")
                f_df = team_df[team_df['자재 유형 내역'] == mat_choice]
                if not f_df.empty:
                    ds = f_df.groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
                    ds['수율'] = (ds['이론금액'] / ds['실제금액'] * 100).round(2)
                    f1 = px.bar(ds, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                    f1.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(range=[80, 108]), showlegend=False)
                    st.plotly_chart(f1, use_container_width=True)
        with low_r:
            with st.container():
                st.markdown('<span class="sub-header-text">🔍 수율 리스크 매트릭스</span>', unsafe_allow_html=True)
                s_dept = st.selectbox("조회 부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="s_dept")
                pdf = team_df.copy() if s_dept == "전체 1팀" else team_df[team_df['생산부문명'] == s_dept]
                if not pdf.empty:
                    isc = pdf.groupby(['연도', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                    isc['수율'] = (isc['이론금액'] / isc['실제금액'] * 100).round(2)
                    isc['actual_billion'] = isc['실제금액'] / 100000000
                    isc['분류'] = isc.apply(lambda r: '핵심관리(⚠️)' if r['연도']=='26년 누적' and r['actual_billion']>=4.0 and r['수율']<=98.0 else r['연도'], axis=1)
                    f3 = px.scatter(isc, x='actual_billion', y='수율', color='분류', size=isc['분류'].map({'25년 누적':6, '26년 누적':7, '핵심관리(⚠️)':12}), hover_name='하위품목 텍스트', color_discrete_map={'25년 누적':COMP_GRAY, '26년 누적':MAIN_BLUE, '핵심관리(⚠️)':ALERT_RED})
                    f3.add_hline(y=100.0, line_dash="dash", line_color="rgba(127,140,141,0.6)")
                    f3.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), showlegend=False, xaxis_title="금액(억원)", yaxis_title=None)
                    st.plotly_chart(f3, use_container_width=True)

        # --- [CARD 4: 하단 Top 5 중점 관리 구역] ---
        with st.container():
            st.markdown('<span class="sub-header-text">🚨 핵심 관리 자재 Top 5</span>', unsafe_allow_html=True)
            t26, t25 = st.tabs(["2026년 분석", "2025년 분석"])
            for target_yr, c_tab in [("26년 누적", t26), ("25년 누적", t25)]:
                with c_tab:
                    y_df = team_df[team_df['연도'] == target_yr]
                    if not y_df.empty:
                        isum = y_df[y_df['생산부문명'] != '스프실'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                        isum['수율'] = (isum['이론금액'] / isum['실제금액'] * 100).round(2)
                        c1, c2 = st.columns(2)
                        for idx, d in enumerate(['면 1과', '면 5과']):
                            with [c1, c2][idx]:
                                st.markdown(f"**📍 {d} 중점 관리**")
                                m_data = isum[isum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                                if not m_data.empty:
                                    m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {r['실제금액']/100000000:.2f}억", axis=1)
                                    fm = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                                    fm.update_traces(marker_color=MAIN_BLUE if '26' in target_yr else COMP_GRAY, textposition='outside', textfont=dict(size=12))
                                    fm.update_layout(height=280, margin=dict(l=0, r=10, t=10, b=10), xaxis=dict(range=[0, 130]), yaxis={'categoryorder':'total ascending'})
                                    st.plotly_chart(fm, use_container_width=True, key=f"top_{target_yr}_{d}")

st.markdown("<p style='text-align:center; color:#94A3B8; font-size:12px; margin-top:30px;'>Integrated Production Monitoring Portal System | © 2026 Production Team 1</p>", unsafe_allow_html=True)
