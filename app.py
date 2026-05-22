import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. 전역 설정 및 디자인 상수 (제공된 UI 양식 가이드라인 100% 반영)
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

# 관제 포털 전용 헥사 컬러
COLOR_MAIN_BLUE = "#3B82F6"   # 강조 블루
COLOR_NAVY = "#002D5B"        # 메인 타이틀 네이비
COLOR_RED_TAG = "#FF4B4B"     # 사이드바 레드 태그 및 경고색
COLOR_BG_LIGHT = "#F8FAFC"    # SaaS 배경 그레이
COLOR_SUB_TEXT = "#64748B"    # 서브 텍스트 슬레이트

st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

# ==============================================================================
# 2. 고해상도 Portal UI 커스텀 스타일링 (CSS) - 유령 박스 제거 및 칼날 정렬
# ==============================================================================
st.markdown(f"""
    <style>
        /* SaaS형 통합 배경색 제어 */
        .stApp {{
            background-color: {COLOR_BG_LIGHT} !important;
        }}
        
        /* 대형 관제 모니터용 메인 컨테이너 레이아웃 패딩 고정 */
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 96% !important;
        }}

        /* 사이드바 UI 커스텀 (제공 양식의 강렬한 레드 멀티 태그 완벽 구현) */
        [data-testid="stSidebar"] {{
            background-color: #F1F5F9 !important;
            border-right: 1px solid #E2E8F0;
        }}
        [data-testid="stSidebar"] .stMarkdown h2 {{
            color: #475569; font-size: 15px !important; font-weight: 800; letter-spacing: 0.5px;
        }}
        /* 멀티셀렉트 선택된 태그 스타일 강제 오버라이딩 */
        span[data-baseweb="tag"] {{
            background-color: {COLOR_RED_TAG} !important;
            border-radius: 4px !important;
            padding: 2px 6px !important;
        }}
        span[data-baseweb="tag"] span {{
            color: white !important; font-weight: 700 !important; font-size: 12px !important;
        }}
        span[data-baseweb="tag"] svg {{
            fill: white !important;
        }}

        /* Streamlit 기본 테두리를 순백색 포털 전용 카드 박스로 튜닝 */
        div[data-testid="stContainer"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 10px !important;
            padding: 24px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
            margin-bottom: 20px !important;
        }}

        /* 양식 맞춤형 고해상도 3열 KPI 인포그래픽 타일 */
        .kpi-row {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 25px;
        }}
        .kpi-tile {{
            flex: 1;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 22px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        .kpi-label {{
            font-size: 14px; font-weight: 700; color: {COLOR_SUB_TEXT}; margin-bottom: 12px;
        }}
        .kpi-value-container {{
            display: flex;
            align-items: baseline;
        }}
        .kpi-value {{
            font-size: 34px; font-weight: 800; color: #1E293B; line-height: 1;
        }}
        .kpi-unit {{
            font-size: 18px; font-weight: 600; color: {COLOR_SUB_TEXT}; margin-left: 4px;
        }}
        .kpi-status {{
            font-size: 13px; font-weight: 700; margin-top: 12px;
        }}

        /* 폰트 표준화 및 헤더 폰트 세팅 */
        .stTabs [data-baseweb="tab"] p {{ font-size: 14px !important; font-weight: bold !important; }}
        h1, h2, h3 {{ font-family: 'Inter', 'Malgun Gothic', sans-serif !important; }}
        .mes-main-title {{ color: {COLOR_NAVY}; font-size: 34px; font-weight: 800; margin: 0; }}
        .mes-sub-title {{ color: {COLOR_MAIN_BLUE}; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 4px; }}
        
        /* 데이터프레임 내부 폰트 고정 */
        .dataframe {{ font-size: 14px !important; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. 사이드바 구성 (제공된 프로토타입 형태 준수)
# ==============================================================================
with st.sidebar:
    st.markdown("## 🖥️ SYSTEM ADMIN")
    st.markdown("---")
    
    st.markdown("### 📅 관제 대상 년월")
    selected_months = st.multiselect(
        "label_hidden", options=ALL_MONTHS, 
        default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 🔍 품목 필터 검색")
    search_keyword = st.text_input("label_hidden", placeholder="품목명을 입력하세요...", label_visibility="collapsed")

# ==============================================================================
# 4. 상단 포털 헤더 영역 (UI 양식 완벽 반영형 멀티 레이아웃)
# ==============================================================================
head_left, head_right = st.columns([4, 1])

with head_left:
    st.markdown(f"""
        <div class="mes-sub-title">MES INTEGRATED OPERATIONAL MONITORING</div>
        <h1 class="mes-main-title">생산1팀 <span style="color:{COLOR_MAIN_BLUE};">Smart 수율 모니터링</span> Portal</h1>
    """, unsafe_allow_html=True)

with head_right:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 12px;">
            <div style="background: #EBF5FF; color: {COLOR_MAIN_BLUE}; padding: 7px 15px; border-radius: 6px; font-weight: 800; display: inline-block; font-size: 13px; border: 1px solid #BFDBFE;">
                • SYSTEM LIVE
            </div>
            <div style="color: #94A3B8; font-size: 11px; margin-top: 10px; font-weight: 600; letter-spacing: 0.2px;">
                Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 5. 고속 연산 데이터 전처리 로직
# ==============================================================================
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy()
    df['월'] = month_label
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
    
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
    
    return df[~((df['실제금액'] > 0) & ((df['이론금액']/df['실제금액']*100) < 50))]

@st.cache_data(ttl=3600)
def load_data(sheet_id, months):
    all_dfs = []
    for m in months:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(m)}"
            df = preprocess_df(pd.read_csv(url), m)
            if not df.empty: all_dfs.append(df)
        except: pass
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

# ==============================================================================
# 6. 메인 포털 화면 데이터 매핑 및 시각화 렌더링
# ==============================================================================
if selected_months:
    team_df = load_data(SHEET_ID, selected_months)
    
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: 
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # ----------------------------------------------------------------------
        # 데이터 신뢰도가 삭제된 양식 맞춤형 3열 고해상도 KPI 컴포넌트
        # ----------------------------------------------------------------------
        df_26 = team_df[team_df['연도'] == '26년 누적']
        if not df_26.empty:
            kpi_th, kpi_ac = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            total_yd = (kpi_th / kpi_ac * 100) if kpi_ac > 0 else 0
            
            risk_item_df = df_26.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
            risk_item_df['yd'] = (risk_item_df['이론금액'] / risk_item_df['실제금액'] * 100)
            risk_count = len(risk_item_df[(risk_item_df['실제금액'] >= 400000000) & (risk_item_df['yd'] <= 98.0)])
        else:
            total_yd, kpi_ac, risk_count = 0, 0, 0

        # 데이터 신뢰도가 누락된 공간을 3개 카드가 균등 분할(칼날 정렬)
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""
                <div class="kpi-tile" style="border-top: 4px solid #10B981;">
                    <div class="kpi-label">종합 수율</div>
                    <div class="kpi-value-container">
                        <span class="kpi-value">{total_yd:.2f}</span><span class="kpi-unit">%</span>
                    </div>
                    <div class="kpi-status" style="color:#10B981;">▲ 목표치 대조 관리 중</div>
                </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
                <div class="kpi-tile" style="border-top: 4px solid {COLOR_MAIN_BLUE};">
                    <div class="kpi-label">누적 실제 투입</div>
                    <div class="kpi-value-container">
                        <span class="kpi-value">{(kpi_ac/100000000):,.1f}</span><span class="kpi-unit">억 원</span>
                    </div>
                    <div class="kpi-status" style="color:{COLOR_SUB_TEXT};">생산 운영 전체 스케일</div>
                </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
                <div class="kpi-tile" style="border-top: 4px solid {COLOR_RED_TAG};">
                    <div class="kpi-label">고위험 자재</div>
                    <div class="kpi-value-container">
                        <span class="kpi-value" style="color:{COLOR_RED_TAG};">{risk_count:02d}</span><span class="kpi-unit">건</span>
                    </div>
                    <div class="kpi-status" style="color:{COLOR_RED_TAG};">⚠️ 집중 점검 및 분석 필요</div>
                </div>
            """, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # [1단] 상황판 섹션 (st.container 통합 분리 및 matplotlib 기반 그라데이션)
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.subheader("📋 실시간 생산 수율 종합 상황판")
            depts = ['면 1과', '면 5과', '스프실', '전체 총합']
            tabs = st.tabs(depts)
            
            for i, d in enumerate(depts):
                with tabs[i]:
                    t_col1, t_col2 = st.columns([52, 48])
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    
                    with t_col1:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px;'>📊 {d} 유형별 상세 실적</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            base_summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            base_summ['수율(%)'] = (base_summ['이론금액'] / base_summ['실제금액'] * 100)
                            
                            pivot_df = base_summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                            pivot_df.columns = [f"{yr[:3]} {v}" for v, yr in pivot_df.columns]
                            
                            # 천단위 콤마 포맷 및 수율 컬럼 전용 그라데이션 매핑 (matplotlib 라이브러리 연동부)
                            styled_pivot = pivot_df.style.format('{:,.0f}').background_gradient(
                                cmap='Blues', 
                                subset=[c for c in pivot_df.columns if '수율' in c]
                            )
                            st.dataframe(styled_pivot, use_container_width=True)
                        else: 
                            st.caption("조회 가능한 데이터 범위가 존재하지 않습니다.")

                    with t_col2:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px;'>📈 누적 수율 변화 추이 마일스톤</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            trend = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                            trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                            trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                            
                            fig = px.line(trend, x='월표시', y='누적수율', color='연도', markers=True, text='누적수율',
                                          color_discrete_map={'25년 누적':'#94A3B8', '26년 누적':COLOR_MAIN_BLUE})
                            fig.update_traces(textposition="top center", textfont=dict(size=11, weight='bold'))
                            fig.update_layout(
                                height=280, margin=dict(l=10,r=10,t=15,b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(gridcolor='#F1F5F9'), yaxis=dict(gridcolor='#F1F5F9'), xaxis_title=None, yaxis_title=None
                            )
                            st.plotly_chart(fig, use_container_width=True, key=f"trend_chart_{d}")

        # ----------------------------------------------------------------------
        # [2단] 분석 매트릭스 (부문별 바 차트 & 분산형 산점도 매트릭스 5:5 밸런싱)
        # ----------------------------------------------------------------------
        c2_1, c2_2 = st.columns(2)
        with c2_1:
            with st.container(border=True):
                st.subheader("📊 부문별 수율 비교 분석")
                if not team_df.empty:
                    dept_comp = team_df.groupby(['연도','생산부문명'])[['이론금액','실제금액']].sum().reset_index()
                    dept_comp['수율'] = (dept_comp['이론금액'] / dept_comp['실제금액'] * 100).round(2)
                    
                    fig_bar = px.bar(dept_comp, x='생산부문명', y='수율', color='연도', barmode='group', text='수율',
                                     color_discrete_map={'25년 누적':'#94A3B8', '26년 누적':COLOR_MAIN_BLUE})
                    fig_bar.update_traces(textposition='outside', textfont=dict(size=11, weight='bold'))
                    fig_bar.update_layout(
                        height=290, margin=dict(l=5,r=5,t=25,b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(range=[max(0, dept_comp['수율'].min() - 3), 105], gridcolor='#F1F5F9'), xaxis_title=None, yaxis_title=None
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

        with c2_2:
            with st.container(border=True):
                st.subheader("🔍 수율 리스크 산점도 매트릭스")
                if not team_df.empty:
                    risk_data = team_df.groupby(['연도','하위품목 텍스트'])[['이론금액','실제금액']].sum().reset_index()
                    risk_data = risk_data[risk_data['실제금액'] > 0].copy()
                    risk_data['수율'] = (risk_data['이론금액'] / risk_data['실제금액'] * 100).round(2)
                    risk_data['금액(억)'] = risk_data['실제금액'] / 100000000
                    
                    fig_scat = px.scatter(risk_data, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트',
                                          color_discrete_map={'25년 누적':'#94A3B8', '26년 누적':COLOR_MAIN_BLUE})
                    fig_scat.add_hline(y=100, line_dash="dash", line_color="#94A3B8", opacity=0.6)
                    fig_scat.update_layout(
                        height=290, margin=dict(l=5,r=5,t=25,b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(gridcolor='#F1F5F9'), yaxis=dict(gridcolor='#F1F5F9'), xaxis_title="투입 금액 (억원)", yaxis_title="수율 (%)"
                    )
                    st.plotly_chart(fig_scat, use_container_width=True)

        # ----------------------------------------------------------------------
        # [3단] 핵심 관리 자재 리스크 오더 세션 (Top 5 하단 튜닝 제어 바 포함)
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.subheader("🚨 핵심 관리 자재 리스크 Top 5")
            
            st.markdown("<div class='bottom-filter-label'>⚙️ 관제 대시보드 데이터 조회 범위 설정</div>", unsafe_allow_html=True)
            top5_ctrl1, top5_ctrl2, _ = st.columns([35, 15, 50])
            with top5_ctrl1:
                v_mode = st.radio("rm", ["📊 선택 기간 전체 누적", "🎯 특정 년월 단독"], horizontal=True, label_visibility="collapsed", key="v_mode_wp")
            with top5_ctrl2:
                if v_mode == "🎯 특정 년월 단독":
                    t_month = st.selectbox("ms", options=sorted(selected_months), label_visibility="collapsed", key="t_month_wp")
                else:
                    t_month = sorted(selected_months)[0] if selected_months else "25.01"
                    st.empty()

            tab_26_b, tab_25_b = st.tabs(["📅 2026년 실적 중점 자재", "📅 2025년 실적 중점 자재"])
            
            for target_yr, current_tab in [("26년 누적", tab_26_b), ("25년 누적", tab_25_b)]:
                with current_tab:
                    yr_df = team_df[team_df['월'] == t_month] if v_mode == "🎯 특정 년월 단독" else team_df[team_df['연도'] == target_yr]
                    suffix = f"({t_month} 단독)" if v_mode == "🎯 특정 년월 단독" else f"({target_yr[:3]} 선택 누적)"
                    
                    if not yr_df.empty:
                        item_sum = yr_df[yr_df['생산부문명'] != '스프실'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                        item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
                        
                        r3_c1, r3_c2 = st.columns(2)
                        for idx, d in enumerate(['면 1과', '면 5과']):
                            with [r3_c1, r3_c2][idx]:
                                st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:10px;'>📍 {d} 중점 리스크 자재 {suffix}</div>", unsafe_allow_html=True)
                                m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                                
                                if not m_data.empty:
                                    m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                                    fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                                    fig_m.update_traces(marker_color=COLOR_MAIN_BLUE if target_yr == "26년 누적" else "#94A3B8", textposition='outside', textfont=dict(size=11, weight='bold'))
                                    fig_m.update_layout(
                                        height=330, margin=dict(l=5, r=5, t=10, b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                        xaxis=dict(range=[0, 145], gridcolor='#F1F5F9'), yaxis={'categoryorder':'total ascending'}
                                    )
                                    st.plotly_chart(fig_m, use_container_width=True, key=f"top5_bar_{target_yr}_{d}")
                                else:
                                    st.caption("조건에 부합하는 중점 관리 자재 내역이 없습니다.")
                    else:
                        st.caption("분석 대상 연도의 데이터 세트가 비어있습니다.")
    else: 
        st.error("구글 스프레드시트연동 혹은 전처리 파이프라인에서 데이터를 정상 로드하지 못했습니다.")
else: 
    st.warning("📂 좌측 사이드바 패널에서 분석 대상 년월을 최소 1개 이상 복수 선택해 주십시오.")
