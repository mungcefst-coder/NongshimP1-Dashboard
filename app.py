import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. 전역 설정 및 디자인 상수 (이미지 추출 컬러 및 규격)
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

# UI 컬러 팔레트
COLOR_NAVY = "#002D5B"      # 메인 타이틀 네이비
COLOR_RED_TAG = "#FF4B4B"   # 사이드바 태그 및 경고 레드
COLOR_BLUE_ACCENT = "#3B82F6" # 강조 블루
COLOR_BG = "#F8FAFC"        # SaaS 배경색

st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

# ==============================================================================
# 2. 고해상도 MES 포털 전용 CSS (이미지 기반 하이엔드 튜닝)
# ==============================================================================
st.markdown(f"""
    <style>
        /* [SaaS 스킨] 전체 배경 */
        .stApp {{
            background-color: {COLOR_BG} !important;
        }}
        
        /* [사이드바] 레드 태그 및 SYSTEM ADMIN 폰트 */
        [data-testid="stSidebar"] {{
            background-color: #F1F5F9 !important;
        }}
        [data-testid="stSidebar"] .stMarkdown h2 {{
            color: #ADB5BD; font-size: 14px !important; font-weight: 700; letter-spacing: 1px;
        }}
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

        /* [카드박스] 유령박스 없는 순백색 Portal 카드 */
        div[data-testid="stContainer"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 24px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            margin-bottom: 20px !important;
        }}

        /* [상단 헤더] MES 타이틀 규격 */
        .mes-sub-title {{
            color: {COLOR_BLUE_ACCENT}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 5px;
        }}
        .mes-main-title {{
            color: {COLOR_NAVY}; font-size: 32px; font-weight: 800; margin: 0;
        }}

        /* [KPI 타일] 3열 구조 인포그래픽 */
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }}
        .kpi-card {{
            background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .kpi-label {{ font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 15px; }}
        .kpi-value-container {{ display: flex; align-items: baseline; }}
        .kpi-value {{ font-size: 32px; font-weight: 800; color: #1E293B; }}
        .kpi-unit {{ font-size: 18px; font-weight: 600; color: #64748B; margin-left: 4px; }}
        .kpi-status {{ font-size: 13px; font-weight: 700; margin-top: 12px; }}
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
# 4. 상단 포털 헤더 영역 (시스템 버튼 및 타이틀)
# ==============================================================================
h_left, h_right = st.columns([4, 1])

with h_left:
    st.markdown(f"""
        <div class="mes-sub-title">MES INTEGRATED OPERATIONAL MONITORING</div>
        <h1 class="mes-main-title">생산1팀 <span style="color:{COLOR_BLUE_ACCENT};">Smart 수율 모니터링</span> Portal</h1>
    """, unsafe_allow_html=True)

with h_right:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 10px;">
            <div style="background: #EBF5FF; color: {COLOR_BLUE_ACCENT}; padding: 6px 15px; border-radius: 6px; font-weight: 800; display: inline-block; font-size: 13px; border: 1px solid #BFDBFE;">
                + SYSTEM LIVE
            </div>
            <div style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 600;">
                Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 5. 데이터 처리 로직 (안정화 버전)
# ==============================================================================
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
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    return df[~((df['실제금액'] > 0) & ((df['이론금액']/df['실제금액']*100) < 50))]

@st.cache_data(ttl=3600)
def load_data(sheet_id, months):
    dfs = []
    for m in months:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(m)}"
            processed = preprocess_df(pd.read_csv(url), m)
            if not processed.empty: dfs.append(processed)
        except: pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ==============================================================================
# 6. 메인 렌더링 영역
# ==============================================================================
if selected_months:
    team_df = load_data(SHEET_ID, selected_months)
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- [KPI 섹션] 이미지 디자인 완벽 반영 (데이터 신뢰도 삭제 후 3열) ---
        df_26 = team_df[team_df['연도'] == '26년 누적']
        if not df_26.empty:
            k_th, k_ac = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            total_yd = (k_th / k_ac * 100) if k_ac > 0 else 0
            risk_cnt = len(df_26.groupby('하위품목 텍스트').filter(lambda x: x['실제금액'].sum() >= 400000000 and (x['이론금액'].sum()/x['실제금액'].sum()*100) <= 98.0))
        else: total_yd, k_ac, risk_cnt = 0, 0, 0

        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">종합 수율</div><div class="kpi-value-container"><span class="kpi-value">{total_yd:.2f}</span><span class="kpi-unit">%</span></div><div class="kpi-status" style="color:#10B981;">● 목표치 대조 관리 중</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">누적 실제 투입</div><div class="kpi-value-container"><span class="kpi-value">{(k_ac/100000000):,.1f}</span><span class="kpi-unit">억</span></div><div class="kpi-status" style="color:#64748B;">생산 운영 스케일</div></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">고위험 자재</div><div class="kpi-value-container"><span class="kpi-value" style="color:{COLOR_RED_TAG};">{risk_cnt:02d}</span><span class="kpi-unit">건</span></div><div class="kpi-status" style="color:{COLOR_RED_TAG};">▲ 집중 점검 필요</div></div>""", unsafe_allow_html=True)

        # --- [메인 상세 지표] 컨테이너 기반 상황판 ---
        with st.container(border=True):
            st.subheader("📋 실시간 수율 지표 상황판")
            depts = ['면 1과', '면 5과', '스프실', '전체 총합']
            tabs = st.tabs(depts)
            for i, d in enumerate(depts):
                with tabs[i]:
                    t_col1, t_col2 = st.columns([52, 48])
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    with t_col1:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px; color:#475569;'>📊 {d} 상세 지표</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            summ['수율(%)'] = (summ['이론금액'] / summ['실제금액'] * 100)
                            pivot = summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                            pivot.columns = [f"{yr[:3]} {v}" for v, yr in pivot.columns]
                            st.dataframe(pivot.style.format('{:,.0f}').set_properties(**{'background-color': '#F8FAFC'}, subset=[c for c in pivot.columns if '수율' in c]), use_container_width=True)
                        else: st.caption("데이터 없음")
                    with t_col2:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px; color:#475569;'>📈 수율 변화 추이</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            trend = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                            trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                            trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                            fig = px.line(trend, x='월표시', y='누적수율', color='연도', markers=True, text='누적수율', color_discrete_map={'25년 누적':'#B0BEC5', '26년 누적':COLOR_BLUE_ACCENT})
                            fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=12))
                            st.plotly_chart(fig, use_container_width=True, key=f"trend_{d}")

        # --- [하단 리스크 분석] 5:5 격자 ---
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("📊 부문별 수율 비교")
                comp = team_df.groupby(['연도','생산부문명'])[['이론금액','실제금액']].sum().reset_index()
                comp['수율'] = (comp['이론금액'] / comp['실제금액'] * 100).round(2)
                fig_bar = px.bar(comp, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적':'#B0BEC5', '26년 누적':COLOR_BLUE_ACCENT})
                fig_bar.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0), yaxis=dict(range=[max(0, comp['수율'].min()-5), 105]))
                st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            with st.container(border=True):
                st.subheader("🔍 리스크 매트릭스")
                risk_scat = team_df.groupby(['연도','하위품목 텍스트'])[['이론금액','실제금액']].sum().reset_index()
                risk_scat['수율'] = (risk_scat['이론금액'] / risk_scat['실제금액'] * 100).round(2)
                risk_scat['금액(억)'] = risk_scat['실제금액'] / 100000000
                fig_scat = px.scatter(risk_scat, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적':'#B0BEC5', '26년 누적':COLOR_BLUE_ACCENT})
                fig_scat.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_scat, use_container_width=True)

    else: st.error("데이터 로드 실패")
else: st.warning("📂 분석 대상 년월을 선택해 주십시오.")
