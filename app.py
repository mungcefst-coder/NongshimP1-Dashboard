import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. 전역 설정 및 디자인 상수 (이미지 기반 컬러 추출)
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

# 포털 전용 컬러 테마
COLOR_MAIN_BLUE = "#3B82F6"   # 강조 블루
COLOR_NAVY = "#002D5B"        # 메인 타이틀 네이비
COLOR_RED_TAG = "#FF4B4B"     # 사이드바 레드 태그
COLOR_BG_LIGHT = "#F8FAFC"    # SaaS 배경 그레이
COLOR_SUB_TEXT = "#64748B"    # 서브 텍스트

st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

# ==============================================================================
# 2. 고해상도 Portal UI 커스텀 스타일링 (CSS)
# ==============================================================================
st.markdown(f"""
    <style>
        /* [SaaS형 스킨] 전체 배경색 제어 */
        .stApp {{
            background-color: {COLOR_BG_LIGHT} !important;
        }}
        
        /* [커스텀 그리드] 메인 컨테이너 패딩 및 여백 강제 고정 */
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 96% !important;
        }}

        /* [사이드바] 이미지와 동일한 레드 태그 및 스타일 적용 */
        [data-testid="stSidebar"] {{
            background-color: #F1F5F9 !important;
            border-right: 1px solid #E2E8F0;
        }}
        [data-testid="stSidebar"] .stMarkdown h2 {{
            color: #475569; font-size: 15px !important; font-weight: 800; letter-spacing: 0.5px;
        }}
        /* 멀티셀렉트 태그 박스 커스텀 */
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

        /* [Portal 카드] Streamlit 컨테이너를 순백색 카드로 변환 */
        div[data-testid="stContainer"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 10px !important;
            padding: 24px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
            margin-bottom: 20px !important;
        }}

        /* [전문가용 KPI] 인포그래픽 타일 스타일 */
        .kpi-tile {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 22px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .kpi-label {{
            font-size: 14px; font-weight: 700; color: {COLOR_SUB_TEXT}; margin-bottom: 12px;
        }}
        .kpi-value {{
            font-size: 32px; font-weight: 800; color: #1E293B; line-height: 1;
        }}
        .kpi-unit {{
            font-size: 18px; font-weight: 600; color: {COLOR_SUB_TEXT}; margin-left: 2px;
        }}
        .kpi-status {{
            font-size: 13px; font-weight: 700; margin-top: 10px;
        }}

        /* 폰트 및 탭 컴포넌트 최적화 */
        .stTabs [data-baseweb="tab"] p {{ font-size: 14px !important; font-weight: bold !important; }}
        h1, h2, h3 {{ font-family: 'Inter', 'Malgun Gothic', sans-serif !important; }}
        .mes-main-title {{ color: {COLOR_NAVY}; font-size: 34px; font-weight: 800; margin: 0; }}
        .mes-sub-title {{ color: {COLOR_MAIN_BLUE}; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 4px; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. 사이드바 구성 (이미지 디자인 준수)
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
# 4. 상단 포털 헤더 영역 (이미지 디자인 완벽 반영)
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
                + SYSTEM LIVE
            </div>
            <div style="color: #94A3B8; font-size: 11px; margin-top: 10px; font-weight: 600; letter-spacing: 0.2px;">
                Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 5. 데이터 처리 로직 (캐싱 기반)
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
    
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
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
# 6. 메인 렌더링 영역
# ==============================================================================
if selected_months:
    team_df = load_data(SHEET_ID, selected_months)
    
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- [KPI 섹션] 이미지와 동일한 3열 고해상도 타일 (데이터 신뢰도 삭제) ---
        df_26 = team_df[team_df['연도'] == '26년 누적']
        kpi_th, kpi_ac = df_26['이론금액'].sum(), df_26['실제금액'].sum()
        total_yd = (kpi_th / kpi_ac * 100) if kpi_ac > 0 else 0
        
        # 고위험 자재 연산
        risk_item_df = df_26.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
        risk_item_df['yd'] = (risk_item_df['이론금액'] / risk_item_df['실제금액'] * 100)
        risk_count = len(risk_item_df[(risk_item_df['실제금액'] >= 400000000) & (risk_item_df['yd'] <= 98.0)])

        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""<div class="kpi-tile"><div class="kpi-label">종합 수율</div><div class="kpi-value">{total_yd:.2f}<span class="kpi-unit">%</span></div><div class="kpi-status" style="color:#10B981;">▲ 목표치 대조 관리 중</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="kpi-tile"><div class="kpi-label">누적 실제 투입</div><div class="kpi-value">{(kpi_ac/100000000):,.1f}<span class="kpi-unit">억 원</span></div><div class="kpi-status" style="color:{COLOR_SUB_TEXT};">생산 운영 전체 스케일</div></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="kpi-tile" style="border-left: 5px solid {COLOR_RED_TAG};"><div class="kpi-label">고위험 자재</div><div class="kpi-value" style="color:{COLOR_RED_TAG};">{risk_count:02d}<span class="kpi-unit">건</span></div><div class="kpi-status" style="color:{COLOR_RED_TAG};">🚨 집중 점검 및 분석 필요</div></div>""", unsafe_allow_html=True)

        # --- [1단] 상황판 섹션 (st.container 통합 래핑) ---
        with st.container(border=True):
            st.subheader("📋 실시간 생산 수율 종합 상황판")
            depts = ['면 1과', '면 5과', '스프실', '전체 총합']
            tabs = st.tabs(depts)
            for i, d in enumerate(depts):
                with tabs[i]:
                    t_col1, t_col2 = st.columns([50, 50])
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    
                    with t_col1:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px;'>📊 {d} 유형별 상세 실적</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            base_summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            base_summ['수율(%)'] = (base_summ['이론금액'] / base_summ['실제금액'] * 100)
                            pivot_df = base_summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                            pivot_df.columns = [f"{yr[:3]} {v}" for v, yr in pivot_df.columns]
                            st.dataframe(pivot_df.style.format('{:,.0f}').background_gradient(cmap='Blues', subset=[c for c in pivot_df.columns if '수율' in c]), use_container_width=True)
                        else: st.caption("데이터 없음")

                    with t_col2:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px;'>📈 누적 수율 변화 추이</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            trend = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                            trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                            trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                            fig = px.line(trend, x='월표시', y='누적수율', color='연도', markers=True, text='누적수율', color_discrete_map={'25년 누적':'#94A3B8', '26년 누적':COLOR_MAIN_BLUE})
                            fig.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=12))
                            st.plotly_chart(fig, use_container_width=True)

        # --- [2단] 분석 매트릭스 (5:5 분할) ---
        c2_1, c2_2 = st.columns(2)
        with c2_1:
            with st.container(border=True):
                st.subheader("📊 부문별 수율 비교")
                fig_bar = px.bar(team_df.groupby(['연도','생산부문명'])['이론금액','실제금액'].sum().reset_index().assign(수율=lambda x: x.이론금액/x.실제금액*100), 
                                 x='생산부문명', y='수율', color='연도', barmode='group', color_discrete_map={'25년 누적':'#94A3B8', '26년 누적':COLOR_MAIN_BLUE})
                fig_bar.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_bar, use_container_width=True)

        with c2_2:
            with st.container(border=True):
                st.subheader("🔍 수율 리스크 매트릭스")
                risk_data = team_df.groupby(['연도','하위품목 텍스트'])['이론금액','실제금액'].sum().reset_index()
                risk_data['수율'] = (risk_data['이론금액']/risk_data['실제금액']*100).round(2)
                risk_data['금액(억)'] = risk_data['실제금액']/100000000
                fig_scat = px.scatter(risk_data, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적':'#94A3B8', '26년 누적':COLOR_MAIN_BLUE})
                fig_scat.add_hline(y=100, line_dash="dash", line_color="#94A3B8")
                fig_scat.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_scat, use_container_width=True)

        # --- [3단] 중점 관리 품목 ---
        with st.container(border=True):
            st.subheader("🚨 핵심 관리 자재 리스크 Top 5")
            st.markdown("<div class='bottom-filter-label'>⚙️ 관제 대시보드 데이터 조회 범위 설정</div>", unsafe_allow_html=True)
            v_mode = st.radio("rm", ["📊 선택 기간 전체 누적", "🎯 특정 년월 단독"], horizontal=True, label_visibility="collapsed")
            
            curr_df = team_df[team_df['연도'] == '26년 누적']
            top5 = curr_df.groupby('하위품목 텍스트')[['이론금액','실제금액']].sum().reset_index()
            top5['수율'] = (top5['이론금액']/top5['실제금액']*100).round(2)
            top5 = top5.sort_values('실제금액', ascending=False).head(15).sort_values('수율').head(5)
            
            fig_top = px.bar(top5, x='수율', y='하위품목 텍스트', orientation='h', text_auto=True)
            fig_top.update_traces(marker_color=COLOR_MAIN_BLUE)
            fig_top.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_top, use_container_width=True)

    else: st.error("데이터 로드 실패")
else: st.warning("분석 대상을 선택하세요.")
