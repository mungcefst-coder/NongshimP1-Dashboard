import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 전역 데이터 소스 및 기준선 선언부
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

MAIN_BLUE = "#4A90E2"       # 26년 누적 실적 (블루)
COMP_GRAY = "#B0BEC5"       # 25년 누적 실적 (그레이)
ALERT_RED = "#E74C3C"       # 리스크 강조 (레드)

# 1. 페이지 세팅 및 전역 UI 스타일링 
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# [CSS 튜닝] 메인 제목(42px) 및 KPI 카드 글자 크기 대폭 확대
st.markdown(f"""
    <style>
        .stApp {{
            background-color: #F8FAFC !important;
        }}
        
        /* 사이드바 스타일 */
        [data-testid="stSidebar"] {{
            background-color: #F1F5F9 !important;
            border-right: 1px solid #E2E8F0;
        }}
        [data-testid="stSidebar"] .stMarkdown h2 {{
            color: #ADB5BD !important; font-size: 14px !important; font-weight: 700 !important; letter-spacing: 1px !important;
        }}
        span[data-baseweb="tag"] {{
            background-color: {ALERT_RED} !important;
            border-radius: 4px !important;
            padding: 2px 6px !important;
        }}
        span[data-baseweb="tag"] span {{
            color: white !important; font-weight: 700 !important; font-size: 12px !important;
        }}

        /* --- [확대] KPI 카드 매트릭스 타일 구조 --- */
        .mes-kpi-wrapper {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-bottom: 10px;
        }}
        .mes-kpi-card {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 26px 28px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }}
        .mes-kpi-label {{
            font-size: 16px; /* 14px에서 확대 */
            font-weight: 700; 
            color: #64748B; 
            margin-bottom: 15px;
        }}
        .mes-kpi-value-box {{
            display: flex; align-items: baseline;
        }}
        .mes-kpi-value {{
            font-size: 48px; /* 34px에서 대폭 확대 */
            font-weight: 800; 
            color: #1E293B; 
            line-height: 1;
        }}
        .mes-kpi-unit {{
            font-size: 22px; /* 18px에서 확대 */
            font-weight: 600; 
            color: #64748B; 
            margin-left: 6px;
        }}
        .mes-kpi-status {{
            font-size: 15px; /* 13px에서 확대 */
            font-weight: 700; 
            margin-top: 15px;
        }}

        /* 하단 장표 스타일 유지 */
        .stTabs [data-baseweb="tab"] p {{ font-size: 14px !important; }}
        .dataframe {{ font-size: 14px !important; }}
        .bottom-filter-label {{ font-size: 12.5px !important; color: #7F8C8D; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# 사이드바 (기존 유지)
with st.sidebar:
    st.header("⚙️ SYSTEM ADMIN")
    st.markdown("---")
    selected_months = st.multiselect("🗓️ 관제 대상 년월", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    st.markdown("---")
    search_keyword = st.text_input("🔍 품목 필터 검색", placeholder="품목명을 입력하세요...")

# 상단 타이틀 구성 (메인제목 42px)
h_left, h_right = st.columns([4.5, 1])
with h_left:
    st.markdown("""
        <div style="color: #3B82F6; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 8px;">
            MES INTEGRATED OPERATIONAL MONITORING
        </div>
        <h1 style="color: #002D5B; font-size: 42px; font-weight: 800; margin: 0; padding: 0; line-height: 1.1;">
            생산1팀 <span style="color:#3B82F6;">Smart 수율 모니터링</span> Portal
        </h1>
    """, unsafe_allow_html=True)

with h_right:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 15px;">
            <div style="background: #EBF5FF; color: #3B82F6; padding: 7px 16px; border-radius: 6px; font-weight: 800; display: inline-block; font-size: 13.5px; border: 1px solid #BFDBFE;">
                ● SYSTEM LIVE
            </div>
            <div style="color: #94A3B8; font-size: 11px; margin-top: 10px; font-weight: 600;">
                Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 2. 고속 캐싱 기반 데이터 처리 로직 (불변)
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
    return df[~((df['실제금액'] > 0) & ((df['이론금액']/df['실제금액']*100) < 50))]

@st.cache_data(ttl=3600)
def load_single_month_cached(sheet_id, m):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(m)}"
        return preprocess_df(pd.read_csv(url), m)
    except: return pd.DataFrame()

# 데이터 빌드 프로세스 (불변)
if selected_months:
    active_dfs = [load_single_month_cached(SHEET_ID, m) for m in selected_months]
    active_dfs = [d for d in active_dfs if not d.empty]
            
    if active_dfs:
        team_df = pd.concat(active_dfs, ignore_index=True)
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # ----------------------------------------------------------------------
        # [수정부] 상단 핵심 KPI (글자 크기 확대 및 스타일 적용)
        # ----------------------------------------------------------------------
        df_26_kpi = team_df[team_df['연도'] == '26년 누적']
        if not df_26_kpi.empty:
            kpi_th, kpi_ac = df_26_kpi['이론금액'].sum(), df_26_kpi['실제금액'].sum()
            total_26_yield = (kpi_th / kpi_ac * 100) if kpi_ac > 0 else 0
            total_cost_billion = kpi_ac / 100000000 
            risk_item_df = df_26_kpi.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
            risk_item_df['items_yd'] = (risk_item_df['이론금액'] / risk_item_df['실제금액'] * 100)
            risk_count = len(risk_item_df[(risk_item_df['실제금액'] >= 400000000) & (risk_item_df['items_yd'] <= 98.0)])
        else:
            total_26_yield, total_cost_billion, risk_count = 0, 0, 0

        st.markdown(f"""
            <div class="mes-kpi-wrapper">
                <div class="mes-kpi-card" style="border-top: 5px solid #10B981;">
                    <div class="mes-kpi-label">종합 수율</div>
                    <div class="mes-kpi-value-box">
                        <span class="mes-kpi-value">{total_26_yield:.2f}</span><span class="mes-kpi-unit">%</span>
                    </div>
                    <div class="mes-kpi-status" style="color: #10B981;">▲ 목표치 대조 관리 중</div>
                </div>
                <div class="mes-kpi-card" style="border-top: 5px solid #3B82F6;">
                    <div class="mes-kpi-label">누적 실제 투입 금액</div>
                    <div class="mes-kpi-value-box">
                        <span class="mes-kpi-value">{total_cost_billion:,.1f}</span><span class="mes-kpi-unit">억 원</span>
                    </div>
                    <div class="mes-kpi-status" style="color: #64748B;">생산 운영 스케일</div>
                </div>
                <div class="mes-kpi-card" style="border-top: 5px solid {ALERT_RED};">
                    <div class="mes-kpi-label">4억 이상 고위험 자재 수</div>
                    <div class="mes-kpi-value-box">
                        <span class="mes-kpi-value" style="color: {ALERT_RED};">{risk_count:02d}</span><span class="mes-kpi-unit">개 품목</span>
                    </div>
                    <div class="mes-kpi-status" style="color: {ALERT_RED};">⚠️ 집중 검토 요망</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 15px 0 20px 0; opacity: 0.2;'>", unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # 1단: 생산1팀 수율 종합 상황판 (불변)
        # ----------------------------------------------------------------------
        st.subheader("📋 생산1팀 수율 종합 상황판")
        depts_list = ['면 1과', '면 5과', '스프실', '전체 총합']
        selected_dept_tab = st.tabs(depts_list)
        for i, d in enumerate(depts_list):
            with selected_dept_tab[i]:
                tab_col1, tab_col2 = st.columns([50, 50])
                target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                with tab_col1:
                    st.markdown(f"<span style='font-size:14px; font-weight:bold;'>📊 {d} 수율 지표</span>", unsafe_allow_html=True)
                    if not target_df.empty:
                        base_summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        base_summ['수율(%)'] = (base_summ['이론금액'] / base_summ['실제금액'] * 100)
                        pivot_df = base_summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                        flat_cols = [f"{yr[:3]} {'수율' if val == '수율(%)' else val}" for yr in ['25년 누적', '26년 누적'] for val in ['이론금액', '실제금액', '수율(%)']]
                        pivot_df.columns = flat_cols
                        pivot_df = pivot_df.reindex(['원자재', '부자재', '반제품', '전체 수율'])
                        st.dataframe(pivot_df.style.format('{:,.0f}').set_properties(subset=[c for c in pivot_df.columns if '수율' in c], **{'background-color': 'rgba(74, 144, 226, 0.1)'}), use_container_width=True)
                    else: st.caption("데이터 없음")
                    st.markdown(f"<div style='font-size:14px; margin-top:-5px;'>📌 <b>{d} 관리 기준 :</b> {YIELD_THRESHOLD[d]:.2f}% 이상</div>", unsafe_allow_html=True)
                with tab_col2:
                    st.markdown(f"<span style='font-size:14px; font-weight:bold;'>📈 수율 변화 추이</span>", unsafe_allow_html=True)
                    if not target_df.empty:
                        trend = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                        trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                        trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        fig = px.line(trend, x='월표시', y='누적수율', color='연도', markers=True, text='누적수율', color_discrete_map={'25년 누적':COMP_GRAY, '26년 누적':MAIN_BLUE})
                        fig.update_layout(height=280, margin=dict(l=10,r=10,t=25,b=10), yaxis=dict(range=[trend['누적수율'].min()-2, trend['누적수율'].max()+2]), xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{d}")

        # ----------------------------------------------------------------------
        # 2단 - 분석 지표 현황 (불변)
        # ----------------------------------------------------------------------
        st.markdown("---")
        r2_col1, r2_col2 = st.columns([50, 50])
        with r2_col1:
            st.subheader("📊 자재 유형별 수율 현황")
            mat_choice = st.selectbox("조회 자재 선택", ["원자재", "부자재", "반제품"], key="mat_opt")
            f_df = team_df[team_df['자재 유형 내역'] == mat_choice]
            if not f_df.empty:
                d_sum = f_df.groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
                d_sum['수율'] = (d_sum['이론금액'] / d_sum['실제금액'] * 100).round(2)
                fig1 = px.bar(d_sum, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                fig1.update_layout(height=330, yaxis=dict(range=[80, 108]), xaxis_title=None)
                st.plotly_chart(fig1, use_container_width=True)
        with r2_col2:
            st.subheader("🔍 수율 리스크 매트릭스")
            scatter_dept = st.selectbox("조회 부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="m_dept")
            plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
            if not plot_df.empty:
                item_scat = plot_df.groupby(['연도', '생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                item_scat['수율'] = (item_scat['이론금액'] / item_scat['실제금액'] * 100).round(2)
                item_scat['actual_billion'] = item_scat['실제금액'] / 100000000
                fig3 = px.scatter(item_scat, x='actual_billion', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                fig3.add_hline(y=100.0, line_dash="dash", line_color="gray", opacity=0.5)
                fig3.update_layout(height=330, xaxis_title="금액(억원)", yaxis_title="수율 (%)")
                st.plotly_chart(fig3, use_container_width=True)

        # ----------------------------------------------------------------------
        # 3단 - 핵심 관리 자재 Top 5 (불변)
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("🚨 핵심 관리 자재 Top 5")
        v_mode = st.radio("보기", ["📊 선택 기간 전체 누적", "🎯 특정 년월 단독"], horizontal=True, label_visibility="collapsed")
        t_month = st.selectbox("월 선택", options=sorted(selected_months), label_visibility="collapsed") if v_mode == "🎯 특정 년월 단독" else "전체"
        
        tab_26, tab_25 = st.tabs(["📅 2026년 분석", "📅 2025년 분석"])
        for target_yr, current_tab in [("26년 누적", tab_26), ("25년 누적", tab_25)]:
            with current_tab:
                yr_df = team_df[team_df['월'] == t_month] if v_mode == "🎯 특정 년월 단독" else team_df[team_df['연도'] == target_yr]
                if not yr_df.empty:
                    item_sum = yr_df[yr_df['생산부문명'] != '스프실'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                    item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
                    c1, c2 = st.columns(2)
                    for idx, d in enumerate(['면 1과', '면 5과']):
                        with [c1, c2][idx]:
                            st.markdown(f"**📍 {d} 중점 관리 품목**")
                            m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율').head(5)
                            fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text_auto=True)
                            fig_m.update_traces(marker_color=MAIN_BLUE if target_yr == "26년 누적" else COMP_GRAY)
                            fig_m.update_layout(height=340, xaxis=dict(range=[0, 140]), yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_m, use_container_width=True, key=f"top5_{target_yr}_{d}")
        
        st.markdown("<div class='bottom-filter-label'>⚙️ 데이터 조회 범위 세부 튜닝 (하단 필터)</div>", unsafe_allow_html=True)
else:
    st.warning("⚠️ 사이드바에서 분석할 년월을 선택해 주세요.")
