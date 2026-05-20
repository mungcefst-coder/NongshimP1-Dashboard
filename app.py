import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. 페이지 세팅 및 타이틀 (전체 레이아웃 밝게 유지)
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템")

# 디자인 테마 컬러 정의
MAIN_BLUE = "#4A90E2"       # 올해 실적 (밝고 선명한 블루)
COMP_GRAY = "#B0BEC5"       # 작년 실적 (확실한 구분이 가는 슬레이트)
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
    st.info("📊 밝고 선명한 블루 테마 적용 중")
    
    months_list = ["전체 누적 데이터"] + ALL_MONTHS
    selected_month = st.selectbox("분석할 년월(YY.MM) 선택", months_list, index=len(months_list)-1)
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="비워두면 전체 조회")

# 메인 화면 제목
st.title("💎 생산1팀 통합 수율 관리 시스템")
st.markdown(f"**현재 조회 데이터:** `{selected_month}`")
st.markdown("---")

# 2. 데이터 처리 로직
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy(); df['월'] = month_label
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        '生産部門名': '생산부문명', '生産部門명': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資材タイプテキスト': '자재 유형 내역',
        '品목텍스트': '하위품목 텍스트', '品목 텍스트': '하위품목 텍스트', '品目テキスト': '하위품목 텍스트', '하위품목텍스트': '하위품목 텍스트',
        '理論金額': '이론금액', '實際金額': '실제금액', 'Actual Amount': '실제금액', '实际金額': '실제금액', '实际金额': '실제금액'
    }
    df.rename(columns=rename_map, inplace=True)
    my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
    if '생산부문명' in df.columns:
        df = df[df['생산부문명'].isin(my_team)]
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

if data_pool:
    trend_raw_df = pd.concat(data_pool.values(), ignore_index=True)
    team_df = trend_raw_df.copy() if selected_month == "전체 누적 데이터" else data_pool.get(selected_month, pd.DataFrame()).copy()
    
    if not team_df.empty:
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # 3. KPI 대시보드
        t_theory, t_actual = team_df['이론금액'].sum(), team_df['실제금액'].sum()
        t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🎯 이론 금액", f"{t_theory:,.0f} 원")
        col2.metric("💰 실제 금액", f"{t_actual:,.0f} 원")
        col3.metric("🏆 종합 수율", f"{t_yield:.2f} %")
        st.markdown("---")

        # ⚡ 1단 - 생산1팀 수율 종합 지표
        st.subheader("📋 생산1팀 수율 종합 지표")
        depts_list = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
        selected_dept_tab = st.tabs(depts_list)
        
        for i, d in enumerate(depts_list):
            with selected_dept_tab[i]:
                tab_col1, tab_col2 = st.columns([50, 50])
                
                with tab_col1:
                    st.markdown(f"**📊 {d} 지표 ({selected_month})**")
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    if not target_df.empty:
                        final_summ = target_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                        final_summ.loc['전체 수율'] = [final_summ['이론금액'].sum(), final_summ['실제금액'].sum()]
                        final_summ['수율(%)'] = (final_summ['이론금액'] / final_summ['실제금액'] * 100)
                        
                        def sig(v, dn=d):
                            trg = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 총합': 98.73}
                            limit = trg.get(dn, 98.73)
                            return f"🟢 {v:.2f}%" if v >= limit else f"🔴 {v:.2f}%"
                        
                        final_summ['수율(%)'] = final_summ['수율(%)'].apply(sig)
                        st.dataframe(final_summ.style.format({'이론금액': '{:,.0f}', '실제금액': '{:,.0f}'}), use_container_width=True)
                    
                    st.markdown(f"""<div style="background-color:#F0F7FF; padding:10px; border-radius:8px; border-left:5px solid {MAIN_BLUE}; font-size:12px; color:#34495E;">
                        🎯 <b>{d} 기준 :</b> { '98.92%' if d=='1팀 면1과' else '97.92%' if d=='1팀 면5과' else '99.53%' if d=='1팀 스프' else '98.73%' } 이상</div>""", unsafe_allow_html=True)

                with tab_col2:
                    st.markdown(f"**📈 전년 동기대비 수율 비교**")
                    compare_data = []
                    if selected_month != "전체 누적 데이터":
                        curr_dept_df = data_pool.get(selected_month, pd.DataFrame())
                        if d != '전체 총합': curr_dept_df = curr_dept_df[curr_dept_df['생산부문명'] == d]
                        
                        if not curr_dept_df.empty:
                            curr_g = curr_dept_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                            for cat in ['원자재', '부자재', '반제품']:
                                val = (curr_g.loc[cat, '이론금액'] / curr_g.loc[cat, '실제금액'] * 100) if cat in curr_g.index else 0
                                compare_data.append({"구분": selected_month, "자재": cat, "수율": round(val, 2)})
                        
                        try:
                            yy, mm = selected_month.split('.')
                            prev_label = f"{int(yy)-1:02d}.{mm}"
                            if prev_label in data_pool:
                                p_df = data_pool[prev_label]
                                if d != '전체 총합': p_df = p_df[p_df['생산부문명'] == d]
                                p_g = p_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                                for cat in ['원자재', '부자재', '반제품']:
                                    val = (p_g.loc[cat, '이론금액'] / p_g.loc[cat, '실제금액'] * 100) if cat in p_g.index else 0
                                    compare_data.insert(0, {"구분": prev_label, "자재": cat, "수율": round(val, 2)})
                        except: pass
                    
                    comp_df = pd.DataFrame(compare_data)
                    if not comp_df.empty:
                        fig_yoy = px.bar(comp_df, x='자재', y='수율', color='구분', barmode='group', text='수율',
                                         color_discrete_map={selected_month: MAIN_BLUE, comp_df['구분'].unique()[0]: COMP_GRAY})
                        fig_yoy.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              yaxis=dict(range=[85, 103]), margin=dict(l=0, r=0, t=30, b=0), height=280, legend=dict(title=None, orientation="h", y=1.1))
                        st.plotly_chart(fig_yoy, use_container_width=True)

        st.markdown("---")
        # ⚡ 2단 - 자재별 비교 & 리스크 매트릭스 변수명 통합 수정 선행 처리 완료
        r2_col1, r2_col2 = st.columns([45, 55])
        with r2_col1:
            st.subheader("📊 부서/자재별 수율 비교")
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            fig1 = px.bar(dept_sum, x='생산부문명', y='수율', color='자재 유형 내역', barmode='group', text='수율',
                          color_discrete_map={'원자재': '#34495E', '부자재': '#85C1E9', '반제품': '#D6EAF8'})
            fig1.update_layout(template='plotly_white', yaxis=dict(range=[80, 105]), height=350)
            st.plotly_chart(fig1, use_container_width=True)

        # ⚡ [오류 해결] 변수명을 명확하게 r2_col2로 통일하여 NameError 완전 차단
        with r2_col2:
            st.subheader("🔍 수율 리스크 매트릭스")
            
            # 부서 선택 셀렉트 박스 슬림화 패치
            select_box_col, _, _ = st.columns([30, 35, 35])
            with select_box_col:
                scatter_dept = st.selectbox("부서 선택", ["전체 1팀", "1팀 면1과", "1팀 면5과", "1팀 스프"], key="matrix_filter")
                
            plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
            
            item_scatter = plot_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
            item_scatter['수율'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
            item_scatter['actual_billion'] = item_scatter['실제금액'] / 100000000
            
            def classify_risk(row):
                if row['수율'] < 100.0 and row['actual_billion'] >= 2.0:
                    return '고위험 관리품목 (수율 미달 & 대형 자재)'
                return '일반 품목'
                
            item_scatter['관리 등급'] = item_scatter.apply(classify_risk, axis=1)
            
            fig3 = px.scatter(
                item_scatter, x='actual_billion', y='수율', 
                hover_name='하위품목 텍스트', color='관리 등급',
                color_discrete_map={
                    '일반 품목': MAIN_BLUE,
                    '고위험 관리품목 (수율 미달 & 대형 자재)': '#FF4D4D'
                }
            )
            
            fig3.add_hline(y=100.0, line_dash="dash", line_color="#7F8C8D", opacity=0.8, annotation_text="수율 100.0% 기준선")
            
            fig3.update_layout(
                template='plotly_white', 
                xaxis=dict(title="실제 투입 금액 (억원)", ticksuffix="억"), 
                yaxis=dict(title="수율 (%)"),
                legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=350
            )
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        # ⚡ 3단 - Top 5 (채도 감쇄 그라데이션)
        st.subheader("🚨 과별 핵심 관리 대상 Top 5")
        item_sum = team_df[team_df['생산부문명'] != '1팀 스프'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_sum['수율'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
        r3_c1, r3_c2 = st.columns(2)
        
        blue_grad = ['#D6EAF8', '#AED6F1', '#85C1E9', '#5DADE2', '#2E86C1'] 
        
        for i, d in enumerate(['1팀 면1과', '1팀 면5과']):
            with [r3_c1, r3_c2][i]:
                st.markdown(f"**📍 {d}**")
                m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                if not m_data.empty:
                    m_data['label'] = m_data.apply(lambda r: f"{r['수율']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                    fig_m = px.bar(m_data, x='수율', y='하위품목 텍스트', orientation='h', text='label')
                    fig_m.update_traces(marker_color=blue_grad, textposition='inside')
                    fig_m.update_layout(template='plotly_white', showlegend=False, xaxis=dict(range=[0, 115]), height=300, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_m, use_container_width=True)
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 구글 시트 상태를 확인해 주세요.")
