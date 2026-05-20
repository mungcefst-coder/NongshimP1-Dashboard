import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. 페이지 세팅 및 타이틀 
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# 디자인 테마 컬러 정의
MAIN_BLUE = "#4A90E2"       # 26년 누적 일반 실적 (선명하고 밝은 블루)
COMP_GRAY = "#B0BEC5"       # 25년 누적 실적 (슬레이트 그레이)
ALERT_RED = "#E74C3C"       # 핵심 관리 대상 강조 컬러 (소프트 레드)
BG_WHITE = "#FFFFFF"

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = [
    "25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
    "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
    "26.01", "26.02", "26.03", "26.04"
]

# 사이드바 컨트롤러
with st.sidebar:
    st.header("📂 데이터 관제")
    st.info("📊 연도별 누적 교차 비교 기능 가동 중")
    
    selected_months = st.multiselect(
        "분석할 년월(YY.MM) 복수 선택 가능", 
        options=ALL_MONTHS, 
        default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"]
    )
    
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="비워두면 전체 조회")

# 메인 화면 제목
st.title("⚙️ 생산1팀 통합 수율 관리 시스템")

if selected_months:
    sorted_display_months = sorted(selected_months)
    st.markdown(f"**현재 선택 기간:** `{', '.join(sorted_display_months)}` (연도별 데이터 독립 연산 조화)")
else:
    st.warning("⚠️ 사이드바에서 분석할 년월을 최소 1개 이상 선택해 주세요.")
st.markdown("---")

# 2. 데이터 처리 로직
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy(); df['월'] = month_label
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        '生産部門명': '생산부문명', '生産部門名': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資材タイプ텍스트': '자재 유형 내역',
        '品목텍스트': '하위품목 텍스트', '品목 텍스트': '하위품목 텍스트', '하위품목텍스트': '하위품목 텍스트',
        '理論金額': '이론금액', '實際金額': '실제금액', 'Actual Amount': '실제금액', 'Actual金额': '실제금액'
    }
    df.rename(columns=rename_map, inplace=True)
    
    if '생산부문명' in df.columns:
        df['생산부문명'] = df['생산부문명'].strip() if hasattr(df['생산부문명'], 'strip') else df['생산부문명']
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실'}
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

@st.cache_data(ttl=600)
def load_all_raw_data(sheet_id, month_list):
    month_data_dict = {}
    for m in month_list:
        try:
            encoded_sheet = urllib.parse.quote(m)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            raw_df = pd.read_csv(url)
            processed = preprocess_df(raw_df, m)
            if not processed.empty: month_data_dict[m] = processed
        except: pass
    return month_data_dict

data_pool = load_all_raw_data(SHEET_ID, ALL_MONTHS)

if data_pool and selected_months:
    active_dfs = [data_pool[m] for m in selected_months if m in data_pool]
    team_df = pd.concat(active_dfs, ignore_index=True)
    team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
    
    if search_keyword:
        team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

    # 1단 - 수율 종합 지표
    st.subheader("📋 생산1팀 수율 종합 지표")
    depts_list = ['면 1과', '면 5과', '스프실', '전체 총합']
    selected_dept_tab = st.tabs(depts_list)
    
    for i, d in enumerate(depts_list):
        with selected_dept_tab[i]:
            tab_col1, tab_col2 = st.columns([53, 47])
            target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
            
            with tab_col1:
                st.markdown(f"**📊 {d} 연도별 누적 지표 대조**")
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
                            flat_cols.append(f"{yr[:3]} {val.replace('(%)', '수율')}")
                    pivot_df.columns = flat_cols
                    pivot_df = pivot_df.reindex(['원자재', '부자재', '반제품', '전체 수율'])
                    format_dict = {}
                    for col in pivot_df.columns:
                        if '수율' in col:
                            pivot_df[col] = pivot_df[col].apply(lambda x: f"{x:.2f}%" if x > 0 else "-")
                        else:
                            format_dict[col] = '{:,.0f}'
                    st.dataframe(pivot_df.style.format(format_dict), use_container_width=True)
                else: st.caption("데이터가 없습니다.")
                
            with tab_col2:
                st.markdown(f"**📈 연도별 누적 수율 비교 (YoY)**")
                if not target_df.empty:
                    agg_yoy = target_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                    agg_yoy['수율'] = (agg_yoy['이론금액'] / agg_yoy['실제금액'] * 100).round(2)
                    fig_yoy = px.bar(
                        agg_yoy, x='자재 유형 내역', y='수율', color='연도', barmode='group', text='수율',
                        category_orders={'자재 유형 내역': ['원자재', '부자재', '반제품']},
                        color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE}
                    )
                    fig_yoy.update_layout(template='plotly_white', height=280, margin=dict(l=0,r=0,t=20,b=0), yaxis=dict(range=[85,103]))
                    st.plotly_chart(fig_yoy, use_container_width=True)

    # 2단 - 자재별 비교 & 리스크 매트릭스
    st.markdown("---")
    r2_col1, r2_col2 = st.columns([48, 52])
    
    with r2_col1:
        st.subheader("📊 부서별 연도 누적 수율 대조")
        mat_choice = st.selectbox("조회할 자재 유형 선택", ["원자재", "부자재", "반제품"], key="mat_opt")
        filtered_r2_1 = team_df[team_df['자재 유형 내역'] == mat_choice]
        if not filtered_r2_1.empty:
            dept_sum = filtered_r2_1.groupby(['연도', '생산부문명'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            fig1 = px.bar(
                dept_sum, x='생산부문명', y='수율', color='연도', barmode='group', text='수율',
                color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE}
            )
            fig1.update_layout(template='plotly_white', height=330, yaxis=dict(range=[80, 105]), xaxis_title=None)
            st.plotly_chart(fig1, use_container_width=True)
        else: st.caption("해당 자재 데이터가 없습니다.")

    with r2_col2:
        st.subheader("🔍 연도별 누적 수율 리스크 매트릭스")
        scatter_dept = st.selectbox("부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="m_dept")
        plot_df2 = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
        
        if not plot_df2.empty:
            item_scatter = plot_df2.groupby(['연도', '생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
            item_scatter['수율'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
            item_scatter['actual_billion'] = item_scatter['실제금액'] / 100000000
            
            # 💡 [리스크 조건] 4억 이상 & 98% 이하
            def assign_risk_status(row):
                if row['연도'] == '26년 누적' and row['actual_billion'] >= 4.0 and row['수율'] <= 98.0:
                    return '26년 핵심 관리 대상 (⚠️고위험)'
                return row['연도']
            
            item_scatter['분류'] = item_scatter.apply(assign_risk_status, axis=1)
            
            # ⚡ [1번 수정] 버블 크기 대폭 축소 (10, 11, 18 -> 6, 7, 12)
            size_map = {'25년 누적': 6, '26년 누적': 7, '26년 핵심 관리 대상 (⚠️고위험)': 12}
            item_scatter['점크기'] = item_scatter['분류'].map(size_map)
            
            fig3 = px.scatter(
                item_scatter, x='actual_billion', y='수율', color='분류',
                size='점크기', size_max=12,  # ⚡ size_max도 12로 하향 조정
                hover_name='하위품목 텍스트',
                color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE, '26년 핵심 관리 대상 (⚠️고위험)': ALERT_RED},
                category_orders={'분류': ['25년 누적', '26년 누적', '26년 핵심 관리 대상 (⚠️고위험)']}
            )
            fig3.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
            fig3.add_hline(y=100.0, line_dash="dash", line_color="#7F8C8D", opacity=0.7)
            fig3.update_layout(template='plotly_white', height=330, xaxis_title="금액(억원)", yaxis_title="수율 (%)", legend_title=None)
            st.plotly_chart(fig3, use_container_width=True)
        else: st.caption("조회할 리스크 내역이 없습니다.")

    # 3단 - 과별 관리 대상 Top 5
    st.markdown("---")
    st.subheader("🚨 과별 핵심 관리 대상 Top 5")
    tab_26, tab_25 = st.tabs(["📅 2026년 누적 관리 품목", "📅 2025년 누적 관리 품목"])
    
    for target_yr, current_tab in [("26년 누적", tab_26), ("25년 누적", tab_25)]:
        with current_tab:
            yr_df = team_df[team_df['연도'] == target_yr]
            if not yr_df.empty:
                item_sum = yr_df[yr_df['생산부문명'] != '스프실'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
                item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
                r3_c1, r3_c2 = st.columns(2)
                for idx, d in enumerate(['면 1과', '면 5과']):
                    with [r3_c1, r3_c2][idx]:
                        st.markdown(f"**📍 {d} ({target_yr})**")
                        m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                        
                        # ⚡ [2번 수정] 높이를 240에서 360으로 1.5배 상향하여 막대 두께 보강
                        if not m_data.empty:
                            m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                            fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                            fig_m.update_traces(marker_color=MAIN_BLUE if target_yr == "26년 누적" else COMP_GRAY, textposition='inside')
                            fig_m.update_layout(template='plotly_white', height=360, xaxis=dict(range=[0, 115]), yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_m, use_container_width=True)
                        else: st.caption("🔍 대상 품목이 없습니다.")
            else: st.caption(f"ℹ️ {target_yr} 데이터가 없습니다.")
else:
    st.warning("⚠️ 사이드바에서 분석할 년월을 선택해 주세요.")
