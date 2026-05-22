import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# 전역 데이터 소스 및 기준선 선언부 (원본 유지)
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

MAIN_BLUE = "#1E40AF"       # 26년 누적 실적 (SaaS 테마에 맞춘 Yield Blue)
COMP_GRAY = "#B0BEC5"       # 25년 누적 실적
ALERT_RED = "#E74C3C"       # 리스크 매트릭스 고위험 강조

# 1. 페이지 세팅 및 전역 UI 스타일링 (SaaS형 대시보드 스킨 적용)
st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* [SaaS 스킨] 배경은 옅은 회색, 폰트는 Inter/Noto Sans 체계 */
        .stApp { background-color: #F8FAFC !important; }
        html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
        
        /* [상단 포털 바] 고정 헤더 디자인 트랙 */
        header[data-testid="stHeader"] {
            background-color: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
        }
        
        /* [커스텀 그리드] 정교한 순백색 카드 박스 모델 */
        .portal-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        
        /* 탭 내부 타이틀 크기 고정 (20px) */
        .sub-header-text {
            font-size: 20px;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 15px;
            display: block;
        }

        /* [전문가용 인포그래픽] HTML 커스텀 KPI 타일 */
        .kpi-tile { text-align: left; padding: 10px 5px; }
        .kpi-label { font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 8px; }
        .kpi-value { font-size: 38px; font-weight: 800; color: #0F172A; line-height: 1; }
        .kpi-unit { font-size: 18px; color: #94A3B8; margin-left: 3px; }
        .kpi-trend { font-size: 13px; margin-top: 10px; font-weight: 700; }

        /* 오리지널 폰트 세팅 유지 */
        .stTabs [data-baseweb="tab"] p { font-size: 14px !important; }
        .target-period { font-size: 14px !important; }
        .dataframe, .paint-table td, .paint-table th { font-size: 14px !important; }
        .bottom-filter-label { font-size: 12.5px !important; color: #7F8C8D; margin-bottom: -12px !important; padding-left: 2px; font-weight: bold; }
        div[data-testid="stRadio"] label span { font-size: 12.5px !important; }
        
        /* 사이드바 관리자 스타일 */
        section[data-testid="stSidebar"] { background-color: #1E293B !important; color: white; }
        section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] p { color: white; }
        
        /* 여백 최적화 */
        .stDataFrame { margin-bottom: 0px; }
        .threshold-info { font-size: 14px; color: #475569; margin-top: 12px; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# 사이드바 컨트롤러 (가이드 박스 st.info 완전 제거)
with st.sidebar:
    st.markdown("<h2 style='font-size: 22px; font-weight: 700; color: white; margin-top: 10px; margin-bottom: 20px;'>📂 데이터 관제</h2>", unsafe_allow_html=True)
    
    selected_months = st.multiselect(
        "분석할 년월(YY.MM) 복수 선택", 
        options=ALL_MONTHS, 
        default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"]
    )
    
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="비워두면 전체 조회")

# --- [메인 헤더 구역: 브랜드 커스텀 타이틀] ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 25px; border-bottom: 2px solid #E2E8F0; padding-bottom: 15px;">
        <div>
            <p style="color:#1E40AF; font-weight:700; letter-spacing:4px; margin-bottom:2px; font-size:11px;">MES INTEGRATED OPERATIONAL MONITORING</p>
            <h1 style="font-size: 34px; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -1.2px; line-height: 1.1;">
                생산1팀 <span style="color:#1E40AF;">Smart 수율 모니터링</span> Portal
            </h1>
        </div>
        <div style="text-align: right; padding-bottom: 5px;">
            <div style="background: #E0E7FF; color: #1E40AF; padding: 6px 14px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #C7D2FE; display: inline-block;">
                <span style="color: #22C55E; animation: blink 1.5s infinite;">●</span> SYSTEM LIVE
            </div>
            <p style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 600;">Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
    <style>@keyframes blink {{ 0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }} }}</style>
""", unsafe_allow_html=True)

# 2. 고속 캐싱 기반 데이터 처리 로직 (절대 불변 원본 복사)
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
        df['생산부문명'] = df['생산부문명'].astype(str).str.strip()
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실', '면 1과': '면 1과', '면 5과': '면 5과', '스프실': '스프실'}
        df = df[df['생산부문명'].isin(dept_map.keys())].copy()
        df['생산부문명'] = df['생산부문명'].map(dept_map)
    else: 
        return pd.DataFrame()
    
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
        raw_df = pd.read_csv(url)
        processed = preprocess_df(raw_df, m)
        return processed
    except:
        return pd.DataFrame()

# 데이터 렌더링 검증 및 바인딩
if selected_months:
    active_dfs = []
    for m in selected_months:
        month_df = load_single_month_cached(SHEET_ID, m)
        if not month_df.empty:
            active_dfs.append(month_df)
            
    if active_dfs:
        team_df = pd.concat(active_dfs, ignore_index=True)
        team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
        
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        sorted_display_months = sorted(selected_months)
        st.markdown(f"<div class='portal-card' style='padding: 15px 20px; margin-bottom: 15px;'><span class='target-period'><b>📆 분석 대상 기간:</b> `{', '.join(sorted_display_months)}`</span></div>", unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # 고해상도 전문가용 KPI 타일
        # ----------------------------------------------------------------------
        df_26_kpi = team_df[team_df['연도'] == '26년 누적']
        if not df_26_kpi.empty:
            kpi_th = df_26_kpi['이론금액'].sum()
            kpi_ac = df_26_kpi['실제금액'].sum()
            total_26_yield = (kpi_th / kpi_ac * 100) if kpi_ac > 0 else 0
            total_cost_billion = kpi_ac / 100000000 
            
            risk_item_df = df_26_kpi.groupby('하위품목 텍스트')[['이론금액', '실제금액']].sum().reset_index()
            risk_item_df['items_yd'] = (risk_item_df['이론금액'] / risk_item_df['실제금액'] * 100)
            risk_count = len(risk_item_df[(risk_item_df['실제금액'] >= 400000000) & (risk_item_df['items_yd'] <= 98.0)])
        else:
            total_26_yield, total_cost_billion, risk_count = 0, 0, 0

        yield_display = f"{total_26_yield:.2f}" if total_26_yield > 0 else "-"
        cost_display = f"{total_cost_billion:,.1f}" if total_cost_billion > 0 else "-"

        # SaaS 전용 고해상도 수치 시각화 그리드
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        kpi_l, kpi_c, kpi_r = st.columns(3)
        with kpi_l:
            st.markdown(f'<div class="kpi-tile"><p class="kpi-label">📈 2026년 선택기간 종합 수율</p><div class="kpi-value">{yield_display}<span class="kpi-unit">%</span></div><p class="kpi-trend" style="color:#22C55E;">● 목표치 대조 관리 중</p></div>', unsafe_allow_html=True)
        with kpi_c:
            st.markdown(f'<div class="kpi-tile"><p class="kpi-label">💰 2026년 누적 실제 투입 금액</p><div class="kpi-value">{cost_display}<span class="kpi-unit">억 원</span></div><p class="kpi-trend" style="color:#64748B;">● 생산 운영 스케일</p></div>', unsafe_allow_html=True)
        with kpi_r:
            status_color = "#E74C3C" if risk_count > 0 else "#22C55E"
            status_msg = "⚠️ 집중 검토 요망" if risk_count > 0 else "✅ 안정권 유지"
            st.markdown(f'<div class="kpi-tile"><p class="kpi-label">🚨 4억 이상 고위험 자재 수</p><div class="kpi-value" style="color:{status_color};">{risk_count}<span class="kpi-unit">개 품목</span></div><p class="kpi-trend" style="color:{status_color};">{status_msg}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # 1단: 생산1팀 수율 종합 상황판 (section-header-text 자막 전면 제거)
        # ----------------------------------------------------------------------
        depts_list = ['면 1과', '면 5과', '스프실', '전체 총합']
        
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        selected_dept_tab = st.tabs(depts_list)
        
        for i, d in enumerate(depts_list):
            with selected_dept_tab[i]:
                tab_col1, tab_col2 = st.columns([63, 37]) 
                target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                
                with tab_col1:
                    st.markdown(f"<span class='sub-header-text'>📊 {d} 수율 지표</span>", unsafe_allow_html=True)
                    if not target_df.empty:
                        base_summ = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        total_rows = []
                        for yr in base_summ['연도'].unique():
                            yr_df = base_summ[base_summ['연도'] == yr]
                            total_rows.append({'연도': yr, '자재 유형 내역': '전체 수율', '이론금액': yr_df['이론금액'].sum(), '실제금액': yr_df['실제금액'].sum()})
                        if total_rows:
                            base_summ = pd.concat([base_summ, pd.DataFrame(total_rows)], ignore_index=True)
                        base_summ['수율(%)'] = (base_summ['이론금액'] / base_summ['실제금액'] * 100)
                        
                        pivot_df = base_summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율(%)'])
                        all_cols = []
                        for yr in ['25년 누적', '26년 누적']:
                            for val in ['이론금액', '실제금액', '수율(%)']:
                                all_cols.append((val, yr))
                        pivot_df = pivot_df.reindex(columns=all_cols, fill_value=0)
                        
                        flat_cols = []
                        for yr in ['25년 누적', '26년 누적']:
                            for val in ['이론금액', '실제금액', '수율(%)']:
                                display_val = "수율" if val == "수율(%)" else val
                                flat_cols.append(f"{yr[:3]} {display_val}")
                        pivot_df.columns = flat_cols
                        pivot_df = pivot_df.reindex(['원자재', '부자재', '반제품', '전체 수율'])
                        
                        def style_yield_table(styler, threshold_val):
                            styler.set_properties(**{'background-color': '#FFFFFF', 'color': '#0F172A'})
                            format_map = {}
                            for col in styler.columns:
                                if '수율' not in col: format_map[col] = '{:,.0f}'
                            styler.format(format_map)
                            
                            for col in styler.columns:
                                if '수율' in col:
                                    styler.set_properties(subset=[col], **{'background-color': 'rgba(74, 144, 226, 0.18)'})
                                    
                            def apply_cell_logic(val):
                                if isinstance(val, str) and '%' in val:
                                    try:
                                        num_val = float(val.replace('%', ''))
                                        if num_val < threshold_val:
                                            return 'color: #FF5252; font-weight: bold;'
                                    except: pass
                                return ''
                                
                            for col in styler.columns:
                                if '수율' in col:
                                    styler.data[col] = styler.data[col].apply(lambda x: f"{x:.2f}%" if x > 0 else "-")
                                    styler.map(apply_cell_logic, subset=[col])
                            return styler
                        
                        thresh = YIELD_THRESHOLD[d]
                        styled_df = pivot_df.style.pipe(style_yield_table, threshold_val=thresh)
                        st.dataframe(styled_df, use_container_width=True)
                    else: 
                        st.caption("조회 가능한 데이터가 없습니다.")
                    
                    st.markdown(f"""
                    <div class="threshold-info">
                        📌 <b>{d} 관리 기준 수율 :</b> {thresh:.2f}% 이상
                    </div>
                    """, unsafe_allow_html=True)
                    
                with tab_col2:
                    st.markdown(f"<span class='sub-header-text'>📈 수율 변화 추이</span>", unsafe_allow_html=True)
                    if not target_df.empty:
                        trend_raw = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index()
                        trend_raw = trend_raw.sort_values(['연도', '월']).reset_index(drop=True)
                        trend_raw['누적이론'] = trend_raw.groupby('연도')['이론금액'].cumsum()
                        trend_raw['누적실제'] = trend_raw.groupby('연도')['실제금액'].cumsum()
                        trend_raw['누적수율'] = (trend_raw['누적이론'] / trend_raw['누적실제'] * 100).round(2)
                        trend_raw['표시월'] = trend_raw['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        
                        df_25 = trend_raw[trend_raw['연도'] == '25년 누적'].set_index('표시월')
                        df_26 = trend_raw[trend_raw['연도'] == '26년 누적'].set_index('표시월')
                        
                        fig_line = go.Figure()
                        for yr_label in sorted(trend_raw['연도'].unique()):
                            yr_data = trend_raw[trend_raw['연도'] == yr_label]
                            color = MAIN_BLUE if '26년' in yr_label else COMP_GRAY
                            
                            position_list = []
                            for m_lbl in yr_data['표시월']:
                                if m_lbl in df_25.index and m_lbl in df_26.index:
                                    val_25 = df_25.loc[m_lbl, '누적수율']
                                    val_26 = df_26.loc[m_lbl, '누적수율']
                                    if '26년' in yr_label:
                                        position_list.append('top center' if val_26 >= val_25 else 'bottom center')
                                    else:
                                        position_list.append('top center' if val_25 > val_26 else 'bottom center')
                                else:
                                    position_list.append('top center')
                            
                            fig_line.add_trace(go.Scatter(
                                x=yr_data['표시월'], y=yr_data['누적수율'],
                                mode='markers+lines+text',
                                name=yr_label,
                                text=yr_data['누적수율'].apply(lambda x: f"{x}%"),
                                textposition=position_list,
                                line=dict(color=color, width=3.5),
                                marker=dict(size=8),
                                textfont=dict(size=11, weight='bold')
                            ))

                        fig_line.update_layout(
                            height=250, 
                            margin=dict(l=10, r=10, t=10, b=10), 
                            yaxis=dict(range=[trend_raw['누적수율'].min()-1.5, trend_raw['누적수율'].max()+1.5], gridcolor='#F1F5F9'),
                            xaxis=dict(gridcolor='#F1F5F9'),
                            xaxis_title=None, yaxis_title=None, 
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                            hovermode="x unified",
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_line, use_container_width=True, key=f"trend_chart_{d}")
                    else: 
                        st.caption("추이 데이터가 존재하지 않습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # 2단 - 분석 지표 현황 (section-header-text 자막 전면 제거)
        # ----------------------------------------------------------------------
        r2_col1, r2_col2 = st.columns([50, 50])
        
        with r2_col1:
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            st.markdown('<span class="sub-header-text">📊 자재 유형별 수율 현황</span>', unsafe_allow_html=True)
            sub_col_box1, sub_col_space1 = st.columns([40, 60])
            with sub_col_box1:
                mat_choice = st.selectbox("조회 자재 선택", ["원자재", "부자재", "반제품"], key="mat_opt")
                
            filtered_r2_1 = team_df[team_df['자재 유형 내역'] == mat_choice]
            if not filtered_r2_1.empty:
                dept_sum = filtered_r2_1.groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
                dept_sum['수율'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
                fig1 = px.bar(dept_sum, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
                fig1.update_traces(textposition='outside', textfont=dict(size=11))
                fig1.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(range=[80, 108]), xaxis_title=None, showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
            else: 
                st.caption("해당 자재 내역이 없습니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        with r2_col2:
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            st.markdown('<span class="sub-header-text">🔍 수율 리스크 매트릭스</span>', unsafe_allow_html=True)
            sub_col_box2, sub_col_space2 = st.columns([40, 60])
            with sub_col_box2:
                scatter_dept = st.selectbox("조회 부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="m_dept")
                
            plot_df2 = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
            
            if not plot_df2.empty:
                item_scatter = plot_df2.groupby(['연도', '생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
                item_scatter['수율'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
                item_scatter['actual_billion'] = item_scatter['실제금액'] / 100000000
                
                def assign_risk_status(row):
                    if row['연도'] == '26년 누적' and row['actual_billion'] >= 4.0 and row['수율'] <= 98.0:
                        return '26년 핵심 관리 대상 (⚠️고위험)'
                    return row['연도']
                item_scatter['분류'] = item_scatter.apply(assign_risk_status, axis=1)
                size_map = {'25년 누적': 6, '26년 누적': 7, '26년 핵심 관리 대상 (⚠️고위험)': 12}
                item_scatter['점크기'] = item_scatter['분류'].map(size_map)
                
                fig3 = px.scatter(
                    item_scatter, x='actual_billion', y='수율', color='분류', size='점크기', size_max=12, hover_name='하위품목 텍스트',
                    color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE, '26년 핵심 관리 대상 (⚠️고위험)': ALERT_RED},
                    category_orders={'분류': ['25년 누적', '26년 누적', '26년 핵심 관리 대상 (⚠️고위험)']}
                )
                fig3.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
                fig3.add_hline(y=100.0, line_dash="dash", line_color="rgba(127, 140, 141, 0.6)", opacity=0.7)
                fig3.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0), xaxis_title="금액(억원)", yaxis_title=None, showlegend=False)
                st.plotly_chart(fig3, use_container_width=True)
            else: 
                st.caption("분석할 리스크 데이터가 부족합니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # 3단 - 핵심 관리 자재 Top 5 (section-header-text 자막 전면 제거)
        # ----------------------------------------------------------------------
        if "top5_view_mode" not in st.session_state:
            st.session_state["top5_view_mode"] = "📊 선택한 기간 전체 누적 데이터"
        if "top5_single_month_select" not in st.session_state:
            st.session_state["top5_single_month_select"] = sorted(selected_months)[0]

        view_mode = st.session_state["top5_view_mode"]
        target_single_month = st.session_state["top5_single_month_select"]
        
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        st.markdown('<span class="sub-header-text">🚨 핵심 관리 자재 Top 5</span>', unsafe_allow_html=True)
        tab_26, tab_25 = st.tabs(["📅 2026년 실적 분석", "📅 2025년 실적 분석"])
        
        for target_yr, current_tab in [("26년 누적", tab_26), ("25년 누적", tab_25)]:
            with current_tab:
                if view_mode == "🎯 특정 년월 단독 데이터":
                    yr_df = team_df[team_df['월'] == target_single_month]
                    chart_title_suffix = f"({target_single_month} 단독)"
                else:
                    yr_df = team_df[team_df['연도'] == target_yr]
                    chart_title_suffix = f"({target_yr[:3]} 선택 기간 누적)"
                    
                if not yr_df.empty:
                    item_sum = yr_df[yr_df['생산부문명'] != '스프실'].groupby(['生産部門명' if '生産部門명' in yr_df.columns else '생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                    item_sum.rename(columns={'生産部門명': '생산부문명'}, errors='ignore', inplace=True)
                    item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
                    
                    r3_c1, r3_c2 = st.columns([50, 50])
                    for idx, d in enumerate(['면 1과', '면 5과']):
                        with [r3_c1, r3_c2][idx]:
                            st.markdown(f"<span class='sub-header-text' style='font-size: 16px;'>📍 {d} 중점 관리 품목 {chart_title_suffix}</span>", unsafe_allow_html=True)
                            m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                            
                            if not m_data.empty:
                                m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                                fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                                fig_m.update_traces(marker_color=MAIN_BLUE if target_yr == "26년 누적" else COMP_GRAY, textposition='outside', textfont=dict(size=12))
                                fig_m.update_layout(height=280, margin=dict(l=0, r=10, t=10, b=10), xaxis=dict(range=[0, 130]), yaxis={'categoryorder':'total ascending'})
                                st.plotly_chart(fig_m, use_container_width=True, key=f"top5_bar_{target_yr}_{d}")
                            else: 
                                st.caption("해당 기준에 매칭되는 품목 데이터가 존재하지 않습니다.")
                else: 
                    st.caption(f"선택한 조건의 {target_yr[:3]} 데이터가 로드되지 않았습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

        # 하단 초슬림 필터 바
        st.markdown("<div class='bottom-filter-label'>⚙️ 데이터 조회 범위 세부 튜닝</div>", unsafe_allow_html=True)
        top5_ctrl_col1, top5_ctrl_col2, top5_ctrl_col3 = st.columns([33, 12, 55])
        
        with top5_ctrl_col1:
            st.radio(
                "label_hidden",
                ["📊 선택한 기간 전체 누적 데이터", "🎯 특정 년월 단독 데이터"], 
                horizontal=True,
                key="top5_view_mode",
                label_visibility="collapsed"
            )
            
        with top5_ctrl_col2:
            if st.session_state["top5_view_mode"] == "🎯 특정 년월 단독 데이터":
                st.selectbox(
                    "month_hidden", 
                    options=sorted(selected_months),
                    key="top5_single_month_select",
                    label_visibility="collapsed"
                )
            else:
                st.empty()
