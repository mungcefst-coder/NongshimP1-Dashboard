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

# 과별 관리 기준 수율 - 이 수치 미달 시 붉은색 강조 적용
YIELD_THRESHOLD = {
    '면 1과': 98.92, 
    '면 5과': 97.93, 
    '스프실': 99.53, 
    '전체 총합': 98.73
}

MAIN_BLUE = "#4A90E2"       
COMP_GRAY = "#B0BEC5"       
ALERT_RED = "#E74C3C"       # 경고 색상

# 1. 페이지 세팅 및 전역 UI 스타일링 
st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

st.markdown(f"""
    <style>
        .stApp {{ background-color: #F8FAFC !important; }}
        [data-testid="stSidebar"] {{ background-color: #F1F5F9 !important; border-right: 1px solid #E2E8F0; }}
        [data-testid="stSidebar"] .stMarkdown h2 {{ color: #ADB5BD !important; font-size: 14px !important; font-weight: 700; letter-spacing: 1px; }}
        span[data-baseweb="tag"] {{ background-color: {ALERT_RED} !important; border-radius: 4px !important; padding: 2px 6px !important; }}
        span[data-baseweb="tag"] span {{ color: white !important; font-weight: 700 !important; font-size: 12px !important; }}

        /* KPI 카드 디자인 및 폰트 확대 (48px) */
        .mes-kpi-wrapper {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 10px; }}
        .mes-kpi-card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 26px 28px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); }}
        .mes-kpi-label {{ font-size: 16px; font-weight: 700; color: #64748B; margin-bottom: 15px; }}
        .mes-kpi-value-box {{ display: flex; align-items: baseline; }}
        .mes-kpi-value {{ font-size: 48px; font-weight: 800; color: #1E293B; line-height: 1; }}
        .mes-kpi-unit {{ font-size: 22px; font-weight: 600; color: #64748B; margin-left: 6px; }}
        .mes-kpi-status {{ font-size: 15px; font-weight: 700; margin-top: 15px; }}

        .stTabs [data-baseweb="tab"] p {{ font-size: 14px !important; font-weight: bold !important; }}
        .dataframe {{ font-size: 14px !important; }}
    </style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("⚙️ SYSTEM ADMIN")
    st.markdown("---")
    selected_months = st.multiselect("🗓️ 관제 대상 년월", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    st.markdown("---")
    search_keyword = st.text_input("🔍 품목 필터 검색", placeholder="품목명을 입력하세요...")

# 상단 타이틀 (42px)
h_left, h_right = st.columns([4.5, 1])
with h_left:
    st.markdown("""
        <div style="color: #3B82F6; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 8px;">MES INTEGRATED OPERATIONAL MONITORING</div>
        <h1 style="color: #002D5B; font-size: 42px; font-weight: 800; margin: 0; padding: 0; line-height: 1.1;">
            생산1팀 <span style="color:#3B82F6;">Smart 수율 모니터링</span> Portal
        </h1>
    """, unsafe_allow_html=True)
with h_right:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 15px;">
            <div style="background: #EBF5FF; color: #3B82F6; padding: 7px 16px; border-radius: 6px; font-weight: 800; display: inline-block; font-size: 13.5px; border: 1px solid #BFDBFE;">● SYSTEM LIVE</div>
            <div style="color: #94A3B8; font-size: 11px; margin-top: 10px; font-weight: 600;">Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 2. 데이터 연산 및 로드 함수
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

# 3. 메인 로직 구동
if selected_months:
    active_dfs = [load_single_month_cached(SHEET_ID, m) for m in selected_months]
    active_dfs = [d for d in active_dfs if not d.empty]
            
    if active_dfs:
        team_df = pd.concat(active_dfs, ignore_index=True)
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        if search_keyword: team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # --- [상단 KPI 섹션] ---
        df_26_kpi = team_df[team_df['연도'] == '26년 누적']
        if not df_26_kpi.empty:
            k_th, k_ac = df_26_kpi['이론금액'].sum(), df_26_kpi['실제금액'].sum()
            total_26_yd = (k_th / k_ac * 100) if k_ac > 0 else 0
            cost_billion = k_ac / 100000000 
            risk_item_df = df_26_kpi.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
            risk_item_df['yd'] = (risk_item_df['이론금액'] / risk_item_df['실제금액'] * 100)
            risk_cnt = len(risk_item_df[(risk_item_df['실제금액'] >= 400000000) & (risk_item_df['yd'] <= 98.0)])
        else: total_26_yd, cost_billion, risk_cnt = 0, 0, 0

        st.markdown(f"""
            <div class="mes-kpi-wrapper">
                <div class="mes-kpi-card" style="border-top: 5px solid #10B981;">
                    <div class="mes-kpi-label">종합 수율</div>
                    <div class="mes-kpi-value-box"><span class="mes-kpi-value">{total_26_yd:.2f}</span><span class="mes-kpi-unit">%</span></div>
                    <div class="mes-kpi-status" style="color: #10B981;">▲ 목표치 대조 관리 중</div>
                </div>
                <div class="mes-kpi-card" style="border-top: 5px solid #3B82F6;">
                    <div class="mes-kpi-label">누적 실제 투입 금액</div>
                    <div class="mes-kpi-value-box"><span class="mes-kpi-value">{cost_billion:,.1f}</span><span class="mes-kpi-unit">억 원</span></div>
                    <div class="mes-kpi-status" style="color: #64748B;">생산 운영 스케일</div>
                </div>
                <div class="mes-kpi-card" style="border-top: 5px solid {ALERT_RED};">
                    <div class="mes-kpi-label">4억 이상 고위험 자재 수</div>
                    <div class="mes-kpi-value-box"><span class="mes-kpi-value" style="color: {ALERT_RED};">{risk_cnt:02d}</span><span class="mes-kpi-unit">개 품목</span></div>
                    <div class="mes-kpi-status" style="color: {ALERT_RED};">⚠️ 집중 검토 요망</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- [1단: 종합 상황판] ---
        st.subheader("📋 생산1팀 수율 종합 상황판")
        depts_nav = ['면 1과', '면 5과', '스프실', '전체 총합']
        tabs = st.tabs(depts_nav)
        
        for i, d in enumerate(depts_nav):
            with tabs[i]:
                c1, c2 = st.columns(2)
                target = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                
                with c1:
                    st.markdown(f"**📊 {d} 상세 실적 (소수점 2자리 & 미달 강조)**")
                    if not target.empty:
                        # 데이터 집계
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
                        
                        # 피벗 및 정렬
                        pivot = summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율'])
                        reorder_cols = [(v, y) for y in ['25년 누적', '26년 누적'] for v in ['이론금액', '실제금액', '수율']]
                        pivot = pivot.reindex(columns=reorder_cols, fill_value=0)
                        
                        # [버그 수정 완료 지점] y -> yr 변수명 매칭 완료
                        pivot.columns = [f"{yr[:3]} {v}" for v, yr in pivot.columns]
                        pivot = pivot.reindex(['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율'])
                        
                        # --- [하이라이트 로직] ---
                        def highlight_low_yield(val, threshold):
                            return f'color: {ALERT_RED}; font-weight: bold;' if val < threshold else ''

                        # 과별 임계치 로드
                        current_threshold = YIELD_THRESHOLD[d]
                        yield_cols = [c for c in pivot.columns if '수율' in c]
                        
                        # 스타일링 적용
                        styled_df = pivot.style.format({c: '{:,.2f}%' if '수율' in c else '{:,.0f}' for c in pivot.columns})
                        styled_df = styled_df.set_properties(subset=yield_cols, **{'background-color': 'rgba(74, 144, 226, 0.05)'})
                        
                        for col in yield_cols:
                            styled_df = styled_df.map(highlight_low_yield, threshold=current_threshold, subset=[col])
                        
                        st.dataframe(styled_df, use_container_width=True)
                    else: st.caption("데이터 없음")
                    st.info(f"💡 {d} 관리 기준 수율: **{YIELD_THRESHOLD[d]:.2f}% 이상** (미달 시 붉은색 강조)")

                with c2:
                    st.markdown(f"**📈 {d} 수율 변화 추이**")
                    if not target.empty:
                        trend = target.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index().sort_values(['연도', '월'])
                        trend['누적수율'] = (trend.groupby('연도')['이론금액'].cumsum() / trend.groupby('연도')['실제금액'].cumsum() * 100).round(2)
                        trend['월표시'] = trend['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        fig = px.line(trend, x='월표시', y='누적수율', color='연도', markers=True, text='누적수율', color_discrete_map={'25년 누적':COMP_GRAY, '26년 누적':MAIN_BLUE})
                        fig.update_traces(texttemplate='%{text:.2f}%', textposition='top center', textfont=dict(size=11, weight='bold'))
                        fig.update_layout(height=280, margin=dict(l=10,r=10,t=25,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(gridcolor='#F1F5F9'), xaxis=dict(gridcolor='#F1F5F9'))
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{d}")

        # --- [하단 분석 매트릭스] ---
        st.markdown("---")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.subheader("📊 부문별 수율 비교 분석")
            m_opt = st.selectbox("조회 자재 선택", ["원자재", "부자재", "반제품"], key="m_opt")
            f_df = team_df[team_df['자재 유형 내역'] == m_opt]
            if not f_df.empty:
                ds = f_df.groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
                ds['수율'] = (ds['이론금액'] / ds['실제금액'] * 100).round(2)
                fig1 = px.bar(ds, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                fig1.update_traces(texttemplate='%{text:.2f}%', textposition='outside', textfont=dict(weight='bold'))
                fig1.update_layout(height=330, yaxis=dict(range=[ds['수율'].min()-3, 105]), xaxis_title=None)
                st.plotly_chart(fig1, use_container_width=True)

        with r2c2:
            st.subheader("🔍 수율 리스크 매트릭스")
            s_dept = st.selectbox("조회 부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="s_dept")
            p_df = team_df.copy() if s_dept == "전체 1팀" else team_df[team_df['생산부문명'] == s_dept].copy()
            if not p_df.empty:
                isc = p_df.groupby(['연도', '생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                isc['수율'] = (isc['이론금액'] / isc['실제금액'] * 100).round(2)
                isc['억'] = isc['실제금액'] / 100000000
                fig3 = px.scatter(isc, x='억', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                fig3.add_hline(y=100.0, line_dash="dash", line_color="gray", opacity=0.5)
                fig3.update_layout(height=330, xaxis_title="금액(억원)", yaxis_title="수율 (%)")
                st.plotly_chart(fig3, use_container_width=True)

        # --- [하단 핵심 관리 TOP 5] ---
        st.markdown("---")
        st.subheader("🚨 핵심 관리 자재 리스크 Top 5")
        v_m = st.radio("필터", ["📊 선택 기간 전체 누적", "🎯 특정 년월 단독"], horizontal=True, label_visibility="collapsed")
        t_m = st.selectbox("월", options=sorted(selected_months), label_visibility="collapsed") if v_m == "🎯 특정 년월 단독" else "전체"
        
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
                            fig_m.update_traces(marker_color=MAIN_BLUE if ty == "26년 누적" else COMP_GRAY, texttemplate='%{text:.2f}%', textposition='outside', textfont=dict(weight='bold'))
                            fig_m.update_layout(height=340, xaxis=dict(range=[0, 140]), yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_m, use_container_width=True, key=f"t5_{ty}_{d_name}")
else:
    st.warning("⚠️ 사이드바에서 분석할 년월을 선택해 주세요.")
