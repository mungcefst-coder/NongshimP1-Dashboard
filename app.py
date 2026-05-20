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

# 2. 데이터 처리 로직
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy(); df['월'] = month_label
    df.columns = [str(c).strip() for c in df.columns]
    
    rename_map = {
        '生産部門명': '생산부문명', '生産部門名': '생산부문명', '생산부문명': '생산부문명', '생산부num명': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資材タイプ텍스트': '자재 유형 내역', '자재 유형 내역': '자재 유형 내역',
        '品목텍스트': '하위품목 텍스트', '品목 텍스트': '하위품목 텍스트', '하위품목텍스트': '하위품목 텍스트', '하위품목 텍스트': '하위품목 텍스트',
        '理論金額': '이론금액', '實際金額': '실제금액', 'Actual Amount': '실제금액', 'Actual金额': '실제금액', '이론금액': '이론금액', '실제금액': '실제금액'
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

# ⚡ [진단패치 1] 구글 시트 연결 실패 시 원인을 디버깅 노출하도록 원복 및 수정
@st.cache_data(ttl=60) # 원인 진단을 위해 임시로 캐시 타임을 1분으로 단축
def load_all_raw_data(sheet_id, month_list):
    month_data_dict = {}
    error_logs = []
    for m in month_list:
        try:
            encoded_sheet = urllib.parse.quote(m)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            raw_df = pd.read_csv(url)
            processed = preprocess_df(raw_df, m)
            if not processed.empty: 
                month_data_dict[m] = processed
            else:
                error_logs.append(f"'{m}' 시트: 불러왔으나 조건에 맞는 데이터(면1과/면5과/스프실)가 없음")
        except Exception as e:
            error_logs.append(f"'{m}' 시트 연결 실패 원인: {str(e)}")
            pass
    return month_data_dict, error_logs

data_pool, system_errors = load_all_raw_data(SHEET_ID, ALL_MONTHS)

# ⚡ [진단패치 2] 데이터가 안 준비되었을 때 시스템 에러 로그를 메인 화면에 뿌려줌
is_data_ready = False
if data_pool and selected_months:
    active_dfs = [data_pool[m] for m in selected_months if m in data_pool]
    if active_dfs:
        team_df = pd.concat(active_dfs, ignore_index=True)
        if not team_df.empty:
            is_data_ready = True

if is_data_ready:
    team_df['연도'] = team_df['월'].apply(lambda x: '25년 누적' if str(x).startswith('25.') else '26년 누적')
    if search_keyword:
        team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

    sorted_display_months = sorted(selected_months)
    st.markdown(f"**현재 선택 기간:** `{', '.join(sorted_display_months)}` (연도별 데이터 독립 연산 조화)")
    st.markdown("---")

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
                            display_val = "수율" if val == "수율(%)" else val
                            flat_cols.append(f"{yr[:3]} {display_val}")
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
                st.markdown(f"**📈 연도별 월간 누적 수율 추이 흐름 (시계열 Trend)**")
                if not target_df.empty:
                    trend_raw = target_df.groupby(['연도', '월'])[['이론금액', '실제금액']].sum().reset_index()
                    trend_raw = trend_raw.sort_values(['연도', '월']).reset_index(drop=True)
                    trend_raw['누적이론'] = trend_raw.groupby('연도')['이론금액'].cumsum()
                    trend_raw['누적실제'] = trend_raw.groupby('연도')['실제금액'].cumsum()
                    trend_raw['누적수율'] = (trend_raw['누적이론'] / trend_raw['누적실제'] * 100).round(2)
                    trend_raw['표시월'] = trend_raw['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                    
                    fig_line = px.line(
                        trend_raw, x='표시월', y='누적수율', color='연도', text='누적수율',
                        color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE}, markers=True
                    )
                    fig_line.update_traces(textposition='top center', textfont=dict(color='#2C3E50', size=10), line=dict(width=3), marker=dict(size=8))
                    min_y = max(50, trend_raw['누적수율'].min() - 0.8)
                    max_y = min(110, trend_raw['누적수율'].max() + 0.8)
                    fig_line.update_layout(template='plotly_white', height=280, margin=dict(l=10, r=10, t=20, b=10), yaxis=dict(range=[min_y, max_y]), xaxis_title=None, yaxis_title="누적 수율 (%)", legend_title=None)
                    st.plotly_chart(fig_line, use_container_width=True)
                else: st.caption("추이 분석 데이터가 부족합니다.")

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
            fig1 = px.bar(dept_sum, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년 누적': COMP_GRAY, '26년 누적': MAIN_BLUE})
            fig1.update_traces(textposition='outside', textfont=dict(color='#2C3E50', size=11, family='sans-serif'))
            fig1.update_layout(template='plotly_white', height=330, yaxis=dict(range=[80, 108]), xaxis_title=None)
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
                        
                        if not m_data.empty:
                            m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                            fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                            fig_m.update_traces(marker_color=MAIN_BLUE if target_yr == "26년 누적" else COMP_GRAY, textposition='outside', textfont=dict(color='#2C3E50', size=11, family='sans-serif'))
                            fig_m.update_layout(template='plotly_white', height=360, xaxis=dict(range=[0, 130]), yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_m, use_container_width=True)
                        else: st.caption("🔍 대상 품목이 없습니다.")
            else: st.caption(f"ℹ️ {target_yr} 데이터가 없습니다.")
else:
    # ⚡ [진단 장치 활성화] 데이터가 로드되지 않은 정교한 시스템적 이유를 화면에 리스트업해줌
    st.error("❌ [시스템 데이터 추적 로그] 구글 시트 통신에 실패했거나 조건 필터 오류가 발생했습니다. 아래 내용을 확인해 주세요.")
    for log in system_errors:
        st.write(f"- {log}")
    st.info("💡 해결 팁: 구글 스프레드시트 하단의 탭 이름이 정확히 '26.01', '26.02' 처럼 공백 없이 입력되어 있는지 점검해 보세요!")
