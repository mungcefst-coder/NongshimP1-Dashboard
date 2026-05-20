import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. 페이지 세팅 및 타이틀
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템 V3.0")

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
    st.success("📊 구글 시트 실시간 연동 중")
    
    months_list = ["전체 누적 데이터"] + ALL_MONTHS
    selected_month = st.selectbox("분석할 년월(YY.MM) 선택", months_list, index=len(months_list)-1)
    st.markdown("---")
    st.subheader("🔍 세부 품목 검색")
    search_keyword = st.text_input("검색어 입력 (예: 팜유, 포장지 등)", placeholder="비워두면 전체 조회")

# 메인 화면 제목
st.title("🚀 생산1팀 통합 수율 관리 시스템 V3.0")
st.markdown(f"**현재 조회 데이터:** `{selected_month}` (핀테크 뮤트 테마 적용 모드)")
st.markdown("---")

# 2. 개별 년월 데이터 전처리 로직 (독립 격리)
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy()
    df['월'] = month_label
    
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        '生産部門名': '생산부문명', '生産部門명': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資材タイプテキスト': '자재 유형 내역',
        '品목텍스트': '하위품목 텍스트', '品目テキスト': '하위품목 텍스트',
        '理論金額': '이론금액', '實際金額': '실제금액', 'Actual Amount': '실제금액', '实际金额': '실제금액'
    }
    df.rename(columns=rename_map, inplace=True)

    # 생산1팀 소속 부서만 필터링
    my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
    if '생산부문명' in df.columns:
        df = df[df['생산부문명'].isin(my_team)]
    else:
        return pd.DataFrame()
    
    if '하위품목 텍스트' in df.columns:
        df['하위품목 텍스트'] = df['하위품목 텍스트'].astype(str).str.strip()
        for kw in ['소계', '합계', '총합', '총계', '결과', '부문명']:
            df = df[~df['하위품목 텍스트'].str.contains(kw, na=False)]

    if '자재 유형 내역' in df.columns:
        df['자재 유형 내역'] = df['자재 유형 내역'].astype(str).str.strip()
        df = df[df['자재 유형 내역'].isin(['원자재', '부자재', '반제품'])]
    
    for col in ['이론금액', '실제금액']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0.0
            
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
            if not processed.empty:
                month_data_dict[m] = processed
        except:
            pass
    return month_data_dict

# 데이터 마스터 풀 로드
data_pool = load_all_raw_data(SHEET_ID, ALL_MONTHS)

if data_pool:
    trend_raw_df = pd.concat(data_pool.values(), ignore_index=True)
    
    if selected_month == "전체 누적 데이터":
        team_df = trend_raw_df.copy()
    else:
        team_df = data_pool.get(selected_month, pd.DataFrame()).copy()
        
    if not team_df.empty:
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # 3. KPI 대시보드 연산
        t_theory = team_df['이론금액'].sum()
        t_actual = team_df['실제금액'].sum()
        t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
        
        prev_yield_kpi = 0
        if selected_month in ALL_MONTHS:
            curr_idx = ALL_MONTHS.index(selected_month)
            if curr_idx > 0:
                prev_m = ALL_MONTHS[curr_idx - 1]
                prev_df = data_pool.get(prev_m, pd.DataFrame())
                if not prev_df.empty:
                    prev_yield_kpi = (prev_df['이론금액'].sum() / prev_df['실제금액'].sum() * 100)
        
        delta_val = f"{t_yield - prev_yield_kpi:.2f}% (전월비)" if prev_yield_kpi > 0 else None

        col1, col2, col3 = st.columns(3)
        col1.metric("🎯 이론 금액", f"{t_theory:,.0f} 원")
        col2.metric("💰 실제 금액", f"{t_actual:,.0f} 원")
        col3.metric("🏆 종합 수율", f"{t_yield:.2f} %", delta=delta_val)
        st.markdown("---")

        # =========================================================================
        # 1단 레이아웃 - 좌우 5:5 분할 배치 (과별 탭 구조 연동)
        # =========================================================================
        st.subheader("📋 과별 상세 수율 통제 및 전년비 비교 분석")
        
        depts_list = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
        selected_dept_tab = st.tabs(depts_list)
        
        for i, d in enumerate(depts_list):
            with selected_dept_tab[i]:
                tab_col1, tab_col2 = st.columns([50, 50])
                
                # --- [왼쪽 스크린: 상세 현황 표] ---
                with tab_col1:
                    st.markdown(f"**📊 {d} 상세 지표 ({selected_month})**")
                    target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                    
                    if not target_df.empty:
                        final_summ = target_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                        
                        raw_sub_theory = final_summ.loc[final_summ.index.isin(['원자재', '부자재']), '이론금액'].sum()
                        raw_sub_actual = final_summ.loc[final_summ.index.isin(['원자재', '부자재']), '실제금액'].sum()
                        all_theory = final_summ.loc[final_summ.index.isin(['원자재', '부자재', '반제품']), '이론금액'].sum()
                        all_actual = final_summ.loc[final_summ.index.isin(['원자재', '부자재', '반제품']), '실제금액'].sum()
                        
                        final_summ.loc['원부자재 수율'] = [raw_sub_theory, raw_sub_actual]
                        final_summ.loc['전체 수율'] = [all_theory, all_actual]
                        final_summ['수율(%)'] = (final_summ['이론금액'] / final_summ['실제금액'] * 100)
                        
                        desired_order = ['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율']
                        existing_order = [idx for idx in desired_order if idx in final_summ.index]
                        final_summ = final_summ.reindex(existing_order)
                        
                        display_df = final_summ.copy()
                        
                        def make_signal_text(val, dept_name=d):
                            if pd.isna(val) or val == 0: return "-"
                            targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 총합': 98.73}
                            limit = 98.73 if dept_name == '전체 총합' else targets.get(dept_name, 95.0)
                            return f"🟢 {val:.2f}%" if val >= limit else f"🔴 {val:.2f}%"
                        
                        display_df['수율(%)'] = [make_signal_text(display_df.loc[idx, '수율(%)']) for idx in display_df.index]
                        
                        styled_df = display_df.style.format({
                            '이론금액': '{:,.0f}', '실제금액': '{:,.0f}'
                        }).map(lambda v: 'color: #FF5252; font-weight: bold;' if "🔴" in str(v) else ('color: #448AFF; font-weight: bold;' if "🟢" in str(v) else ''), subset=['수율(%)'])
                        
                        st.dataframe(styled_df, use_container_width=True)
                    else:
                        st.write("💡 해당 년월에 해당 과의 유효 데이터가 존재하지 않습니다.")
                        
                    st.markdown(f"""
                    <div style="background-color: #262730; padding: 10px 14px; border-radius: 8px; border-left: 5px solid #448AFF; margin-top: 5px;">
                        <span style="font-size: 11px; color: #E0E0E0; font-weight: 500;">
                            🎯 <b>{d} 관리 기준 수율 :</b> { '98.92%' if d=='1팀 면1과' else '97.92%' if d=='1팀 면5과' else '99.53%' if d=='1팀 스프' else '98.73%' } 이상 통제 필요
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                # --- [오른쪽 스크린: 자재별 1:1 전년비 바 차트] ---
                with tab_col2:
                    st.markdown(f"**📊 {d} 전년 동기대비 수율 비교**")
                    
                    compare_data = []
                    
                    if selected_month != "전체 누적 데이터":
                        curr_dept_df = data_pool.get(selected_month, pd.DataFrame())
                        if d != '전체 총합' and not curr_dept_df.empty:
                            curr_dept_df = curr_dept_df[curr_dept_df['생산부문명'] == d]
                            
                        if not curr_dept_df.empty:
                            curr_g = curr_dept_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                            for cat in ['원자재', '부자재', '반제품']:
                                if cat in curr_g.index and curr_g.loc[cat, '실제금액'] > 0:
                                    c_yld = (curr_g.loc[cat, '이론금액'] / curr_g.loc[cat, '실제금액'] * 100)
                                    compare_data.append({"구분": selected_month, "자재 유형": cat, "수율(%)": round(c_yld, 2)})
                                else:
                                    compare_data.append({"구분": selected_month, "자재 유형": cat, "수율(%)": 0.0})
                        else:
                            for cat in ['원자재', '부자재', '반제품']:
                                compare_data.append({"구분": selected_month, "자재 유형": cat, "수율(%)": 0.0})
                        
                        try:
                            yy, mm = selected_month.split('.')
                            prev_year_label = f"{int(yy)-1:02d}.{mm}"
                            
                            if prev_year_label in data_pool:
                                p_dept_df = data_pool[prev_year_label]
                                if d != '전체 총합' and not p_dept_df.empty:
                                    p_dept_df = p_dept_df[p_dept_df['생산부문명'] == d]
                                    
                                if not p_dept_df.empty:
                                    p_g = p_dept_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                                    for cat in ['원자재', '부자재', '반제품']:
                                        if cat in p_g.index and p_g.loc[cat, '실제금액'] > 0:
                                            p_yld = (p_g.loc[cat, '이론금액'] / p_g.loc[cat, '실제금액'] * 100)
                                            compare_data.insert(0, {"구분": prev_year_label, "자재 유형": cat, "수율(%)": round(p_yld, 2)})
                                        else:
                                            compare_data.insert(0, {"구분": prev_year_label, "자재 유형": cat, "수율(%)": 0.0})
                                else:
                                    for cat in ['원자재', '부자재', '반제품']:
                                        compare_data.insert(0, {"구분": prev_year_label, "자재 유형": cat, "수율(%)": 0.0})
                        except:
                            pass
                    else:
                        t_dept_df = trend_raw_df if d == '전체 총합' else trend_raw_df[trend_raw_df['생산부문명'] == d]
                        if not t_dept_df.empty:
                            t_g = t_dept_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                            for cat in ['원자재', '부자재', '반제품']:
                                if cat in t_g.index and t_g.loc[cat, '실제금액'] > 0:
                                    t_yld = (t_g.loc[cat, '이론금액'] / t_g.loc[cat, '실제금액'] * 100)
                                    compare_data.append({"구분": "전체 누적", "자재 유형": cat, "수율(%)": round(t_yld, 2)})
                                else:
                                    compare_data.append({"구분": "전체 누적", "자재 유형": cat, "수율(%)": 0.0})
                    
                    comp_df = pd.DataFrame(compare_data)
                    
                    if not comp_df.empty and comp_df['수율(%)'].sum() > 0:
                        color_map = {}
                        for p in comp_df['구분'].unique():
                            if str(p).startswith('26'): color_map[p] = '#2A5994'  # 뮤트 네이비 블루
                            elif str(p).startswith('25'): color_map[p] = '#94A3B8'  # 차분한 블루그레이
                            else: color_map[p] = '#4A5568'
                                
                        fig_yoy = px.bar(
                            comp_df, x='자재 유형', y='수율(%)', color='구분', barmode='group',
                            text='수율(%)', category_orders={'자재 유형': ['원자재', '부자재', '반제품']},
                            color_discrete_map=color_map
                        )
                        fig_yoy.update_traces(texttemplate='%{text:.2f}%', textposition='inside')
                        fig_yoy.update_layout(
                            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            yaxis=dict(range=[85, 103], title="수율 (%)", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                            xaxis=dict(title=None),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=None),
                            margin=dict(l=0, r=0, t=30, b=0), height=290,
                            bargap=0.25, bargroupgap=0.1
                        )
                        st.plotly_chart(fig_yoy, use_container_width=True)
                    else:
                        st.info("💡 비교 분석할 작년 데이터가 시트에 존재하지 않습니다.")

    st.markdown("---")

    # =========================================================================
    # 2단 레이아웃 (부서별 수율 비교 & 리스크 매트릭스)
    # =========================================================================
    row2_col1, row2_col2 = st.columns([45, 55])
    
    with row2_col1:
        st.subheader("📊 부서 및 자재별 수율 비교")
        dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
        dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
        
        fig1 = px.bar(dept_sum, x='생산부문명', y='수율(%)', color='자재 유형 내역', barmode='group', text='수율(%)', 
                      color_discrete_map={
                          '원자재': '#7A9A82',  # 세이지 그린
                          '부자재': '#5C6199',  # 인디고 퍼플
                          '반제품': '#8A9BA8'   # 라이트 스틸 그레이
                      })
        fig1.update_layout(yaxis=dict(range=[80, 105]), template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)

    with row2_col2:
        st.subheader("🔍 수율 리스크 매트릭스")
        scatter_dept = st.selectbox("🎯 분석할 부서 선택", ["전체 1팀", "1팀 면1과", "1팀 면5과", "1팀 스프"], key="matrix_dept_filter")
        
        plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
        item_scatter = plot_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
        item_scatter['수율(%)'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
        item_scatter['실제 투입 금액 (억 원)'] = item_scatter['실제금액'] / 100000000
        
        targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 1팀': 98.73}
        limit = targets.get(scatter_dept, 95.0)
        item_scatter['관리 상태'] = item_scatter['수율(%)'].apply(lambda x: '기준 달성' if x >= limit else '기준 미달')
        
        fig3 = px.scatter(item_scatter, x='실제 투입 금액 (억 원)', y='수율(%)', hover_name='하위품목 텍스트', color='관리 상태', 
                           color_discrete_map={'기준 달성': '#475569', '기준 미달': '#D1A3A3'})
        fig3.add_hline(y=limit, line_dash="dash", line_color="#D1A3A3", opacity=0.8, annotation_text=f"{limit}%")
        fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(ticksuffix="억"))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # 🚨 [3단] 과별 핵심 관리 대상 Top 5 (채도 감쇄 그라데이션 완벽 구현)
    # =========================================================================
    st.subheader("🚨 과별 핵심 관리 대상 Top 5 (실제금액 상위 품목 중 수율 최저 순)")
    item_sum = team_df[team_df['생산부문명'] != '1팀 스프'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
    item_sum['수율(%)'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
    
    row3_col1, row3_col2 = st.columns(2)
    for i, d in enumerate(['1팀 면1과', '1팀 면5과']):
        with [row3_col1, row3_col2][i]:
            st.markdown(f"**📍 {d} 관리 품목**")
            m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율(%)', ascending=True).head(5)
            
            if not m_data.empty:
                m_data['표시텍스트'] = m_data.apply(lambda r: f"수율: {r['수율(%)']:.2f}% | 실제: {(r['실제금액']/100000000):.2f}억", axis=1)
                
                # ⚡ [핵심 수정] 위에서 아래로 내려갈수록 채도와 명도를 점진적으로 감쇄시키는 뮤트 톤 배열 주입
                # Plotly Express 구조상 0번 인덱스가 최하단 막대, 4번 인덱스가 최상단 막대에 매핑됩니다.
                muted_gradient_palette = [
                    '#8288BD',  # 5등 (최하단): 가장 옅은 라이트 뮤트 라벤더
                    '#6B71A3',  # 4등
                    '#555B89',  # 3등 (중간)
                    '#41466E',  # 2등
                    '#2E3253'   # 1등 (최상단): 가장 진하고 선명한 딥 퍼플 차콜
                ]
                
                fig_m = px.bar(m_data, x='수율(%)', y='하위품목 텍스트', orientation='h', text='표시텍스트')
                
                # marker_color에 배열을 직접 바인딩하여 각 막대에 독립적 그라데이션 투사
                fig_m.update_traces(
                    showlegend=False,
                    marker_color=muted_gradient_palette,
                    texttemplate='%{text}',
                    textposition='inside'
                )
                
                fig_m.update_layout(
                    showlegend=False, template='plotly_dark', 
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    xaxis=dict(range=[0, 115]), 
                    yaxis={'categoryorder':'total ascending'}
                )
                st.plotly_chart(fig_m, use_container_width=True)
            else:
                st.info("데이터 없음")
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 구글 시트 상태를 확인해 주세요.")
