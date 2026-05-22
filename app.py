import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 1. 전역 설정 및 디자인 상수
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = [
    "25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
    "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
    "26.01", "26.02", "26.03", "26.04"
]

YIELD_THRESHOLD = {'면 1과': 98.92, '면 5과': 97.93, '스프실': 99.53, '전체 총합': 98.73}

MAIN_BLUE = "#4A90E2"   # 26년 실적 블루
COMP_GRAY = "#94A3B8"   # 25년 대비 그레이
ALERT_RED = "#E74C3C"   # 고위험 레드
BG_COLOR = "#F8FAFC"    # SaaS 배경색

st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# ==============================================================================
# 2. 고퀄리티 SaaS UI 스타일링 (유령 박스 제거 버전)
# ==============================================================================
st.markdown(f"""
    <style>
        /* 기본 배경색 스킨 */
        .stApp {{ background-color: {BG_COLOR} !important; }}
        
        /* 레이아웃 여백 최적화 */
        .block-container {{ padding-top: 1.5rem !important; max-width: 97% !important; }}

        /* 순백색 카드 디자인 (Streamlit Container 오버라이딩) */
        div[data-testid="stContainer"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 24px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            margin-bottom: 20px !important;
        }}

        /* 전문가용 KPI 타일 */
        .kpi-tile {{
            background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid {MAIN_BLUE};
            border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }}
        .kpi-tile.risk {{ border-left-color: {ALERT_RED}; }}
        .kpi-label {{ font-size: 13.5px; font-weight: 700; color: #64748B; margin-bottom: 8px; letter-spacing: 0.5px; }}
        .kpi-value {{ font-size: 32px; font-weight: 800; color: #0F172A; line-height: 1.1; }}
        .kpi-delta {{ font-size: 12.5px; font-weight: 600; color: #94A3B8; margin-top: 6px; }}

        /* 폰트 및 탭 가시성 고정 */
        .stTabs [data-baseweb="tab"] p {{ font-size: 14px !important; font-weight: bold !important; color: #475569 !important; }}
        h1 {{ font-size: 26px !important; font-weight: 800 !important; color: #1E293B !important; margin-bottom: 25px !important; }}
        h3 {{ font-size: 18px !important; font-weight: 700 !important; color: #1E293B !important; margin-top: 0 !important; }}
        
        /* 사이드바 텍스트 크기 조절 */
        [data-testid="stSidebar"] .stMarkdown p {{ font-size: 13.5px !important; }}
    </style>
""", unsafe_allow_html=True)

# 사이드바 컨트롤러
with st.sidebar:
    st.header("📂 데이터 관제")
    st.info("📊 통합 수율 관리 시스템 가동 중")
    selected_months = st.multiselect("분석 대상 년월 선택", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="품목명 입력...")

st.title("⚙️ 생산1팀 Smart 수율 모니터링 시스템")

# ==============================================================================
# 3. 데이터 로직 (캐싱 및 전처리)
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
# 4. 대시보드 렌더링
# ==============================================================================
if selected_months:
    team_df = load_data(SHEET_ID, selected_months)
    if not team_df.empty:
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- 상단 KPI 타일 (3열) ---
        df_26 = team_df[team_df['연도'] == '26년 누적']
        if not df_26.empty:
            total_yd = (df_26['이론금액'].sum() / df_26['실제금액'].sum() * 100)
            total_amt = df_26['실제금액'].sum() / 100000000
            risk_data = df_26.groupby('하위품목 텍스트')[['이론금액','실제금액']].sum().reset_index()
            risk_data['yd'] = risk_data['이론금액'] / risk_data['실제금액'] * 100
            risk_count = len(risk_data[(risk_data['실제금액'] >= 400000000) & (risk_data['yd'] <= 98.0)])
        else: total_yd, total_amt, risk_count = 0, 0, 0

        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f'<div class="kpi-tile"><div class="kpi-label">📈 2026년 종합 수율</div><div class="kpi-value">{total_yd:.2f}%</div><div class="kpi-delta">✓ 관리 기준선 대조 관제 중</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="kpi-tile"><div class="kpi-label">💰 2026년 실제 투입 금액</div><div class="kpi-value">{total_amt:,.1f}억</div><div class="kpi-delta">⚡ 생산 가동 전체 스케일</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="kpi-tile risk"><div class="kpi-label">🚨 고위험 자재 수 (4억↑)</div><div class="kpi-value" style="color:{ALERT_RED}">{risk_count}개</div><div class="kpi-delta" style="color:{ALERT_RED}">⚠️ 즉시 집중 검토 요망</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # --- 1단: 종합 상황판 ---
        with st.container(border=True):
            st.subheader("📋 생산1팀 수율 종합 상황판")
            depts = ['면 1과', '면 5과', '스프실', '전체 총합']
            tabs = st.tabs(depts)
            for i, d in enumerate(depts):
                with tabs[i]:
                    t_col1, t_col2 = st.columns([50, 50])
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    
                    with t_col1:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px; color:#475569;'>📊 {d} 상세 지표</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                            summ['수율(%)'] = (summ['이론금액'] / summ['실제금액'] * 100)
                            pivot = summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                            pivot.columns = [f"{yr[:3]} {v}" for v, yr in pivot.columns]
                            # matplotlib 에러 방지용 안전 스타일링
                            try:
                                st.dataframe(pivot.style.format('{:,.0f}').background_gradient(cmap='Blues', subset=[c for c in pivot.columns if '수율' in c]), use_container_width=True)
                            except:
                                st.dataframe(pivot.style.format('{:,.0f}'), use_container_width=True)
                        else: st.caption("데이터 없음")

                    with t_col2:
                        st.markdown(f"<div style='font-size:14px; font-weight:700; margin-bottom:12px; color:#475569;'>📈 누적 수율 변화 추이</div>", unsafe_allow_html=True)
                        if not target_df.empty:
                            trend = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                            trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                            trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                            fig = px.line(trend, x='월표시', y='누적수율', color='연도', markers=True, text='누적수율', color_discrete_map={'25년 누적':COMP_GRAY, '26년 누적':MAIN_BLUE})
                            fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=12))
                            st.plotly_chart(fig, use_container_width=True, key=f"trend_{d}")

        # --- 2단: 분석 매트릭스 ---
        c2_1, c2_2 = st.columns(2)
        with c2_1:
            with st.container(border=True):
                st.subheader("📊 부문별 수율 비교")
                comp = team_df.groupby(['연도','생산부문명'])[['이론금액','실제금액']].sum().reset_index()
                comp['수율'] = (comp['이론금액'] / comp['실제금액'] * 100).round(2)
                fig_bar = px.bar(comp, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적':COMP_GRAY, '26년 누적':MAIN_BLUE})
                fig_bar.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0), yaxis=dict(range=[85, 105]))
                st.plotly_chart(fig_bar, use_container_width=True)

        with c2_2:
            with st.container(border=True):
                st.subheader("🔍 수율 리스크 매트릭스")
                risk_scat = team_df.groupby(['연도','하위품목 텍스트'])[['이론금액','실제금액']].sum().reset_index()
                risk_scat['수율'] = (risk_scat['이론금액'] / risk_scat['실제금액'] * 100).round(2)
                risk_scat['금액(억)'] = risk_scat['실제금액'] / 100000000
                fig_scat = px.scatter(risk_scat, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적':COMP_GRAY, '26년 누적':MAIN_BLUE})
                fig_scat.add_hline(y=100, line_dash="dash", line_color=COMP_GRAY)
                fig_scat.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_scat, use_container_width=True)

        # --- 3단: 핵심 관리 품목 ---
        with st.container(border=True):
            st.subheader("🚨 핵심 관리 자재 리스크 Top 5")
            st.markdown("<div style='font-size:12px; font-weight:bold; color:#64748B; margin-bottom:10px;'>⚙️ 데이터 조회 범위 설정</div>", unsafe_allow_html=True)
            v_mode = st.radio("rm", ["📊 선택 기간 전체 누적", "🎯 특정 년월 단독"], horizontal=True, label_visibility="collapsed")
            
            top5_df = team_df[team_df['연도'] == '26년 누적']
            top5 = top5_df.groupby('하위품목 텍스트')[['이론금액','실제금액']].sum().reset_index()
            top5['수율'] = (top5['이론금액'] / top5['실제금액'] * 100).round(2)
            top5 = top5.sort_values('실제금액', ascending=False).head(15).sort_values('수율').head(5)
            
            fig_top = px.bar(top5, x='수율', y='하위품목 텍스트', orientation='h', text_auto=True)
            fig_top.update_traces(marker_color=MAIN_BLUE)
            fig_top.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), xaxis=dict(range=[0, 140]))
            st.plotly_chart(fig_top, use_container_width=True)
    else: st.error("데이터 로드 실패")
else: st.warning("📂 분석 대상 년월을 선택해 주세요.")
