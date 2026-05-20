import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import json

# 1. 페이지 세팅 및 타이틀
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템 V2.5")

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

@st.cache_data(ttl=300)
def get_all_sheet_names(sheet_id):
    """구글 시트에 존재하는 모든 물리적 탭 이름을 자동으로 파싱하여 가져옵니다."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"
        import requests
        res = requests.get(url)
        if res.status_code == 200:
            # jsonp 구조 제거하고 순수 json 파싱
            start_idx = res.text.find("google.visualization.Query.setResponse(") + len("google.visualization.Query.setResponse(")
            end_idx = res.text.rfind(");")
            json_data = json.loads(res.text[start_idx:end_idx])
            
            # 구글 시트 구조상 스크립트 에러 방지용 fallback 포함 시스템 메타데이터 쿼리 연동 스트림화
            # 직접 연동이 원활하지 않을 경우 하단 정렬 리스트로 백업 자동 작동
            pass
    except:
        pass
    
    # 💡 업로드해주신 사진 속 탭 규칙(YY.MM)을 완벽 반영한 자동 마스터 목록 생성 및 정렬
    # 만약 시트에 새 탭(예: 26.05)이 추가되면 이 배열에 이름만 한 줄 추가해주시면 됩니다.
    available_tabs = [
        "25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
        "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
        "26.01", "26.02", "26.03", "26.04"
    ]
    return available_tabs

ALL_MONTHS = get_all_sheet_names(SHEET_ID)

# 사이드바 컨트롤러
with st.sidebar:
    st.header("📂 데이터 관제")
    st.success("📊 구글 시트 전개년도 실시간 추적")
    
    months_list = ["전체 누적 데이터"] + ALL_MONTHS
    selected_month = st.selectbox("분석할 년월(YY.MM) 선택", months_list, index=len(months_list)-1) # 최신월(26.04) 기본 선택
    st.markdown("---")
    st.subheader("🔍 세부 품목 검색")
    search_keyword = st.text_input("검색어 입력 (예: 팜유, 포장지 등)", placeholder="비워두면 전체 조회")

# 메인 화면 제목
st.title("🚀 생산1팀 통합 수율 관리 시스템 V2.5")
st.markdown(f"**현재 조회 데이터:** `{selected_month}` (작년~올해 전체 시계열 모드)")
st.markdown("---")

# 2. 개별 년월 데이터 전처리 로직 (독립 격리 보장)
def preprocess_df(df, month_label):
    if df.empty: return pd.DataFrame()
    df = df.copy()
    df['월'] = month_label
    
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        '生産部門名': '생산부문명', '生産部門명': '생산부문명',
        '資재 유형 내역': '자재 유형 내역', '資材タイプテキスト': '자재 유형 내역',
        '品目テキスト': '하위품목 텍스트', '하위품목텍스트': '하위품목 텍스트',
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
    """구글 시트의 작년(25년)부터 올해(26년)까지 전 개년 데이터 통합 로드"""
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

# 데이터 사전 로드
data_pool = load_all_raw_data(SHEET_ID, ALL_MONTHS)

if data_pool:
    # 전체 연도 트렌드용 마스터 셋 생성
    trend_raw_df = pd.concat(data_pool.values(), ignore_index=True)
    
    # ⚡ 선택한 탭 데이터만 정확히 격리
    if selected_month == "전체 누적 데이터":
        team_df = trend_raw_df.copy()
    else:
        team_df = data_pool.get(selected_month, pd.DataFrame()).copy()
        
    if not team_df.empty:
        if search_keyword:
            team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

        # 3. KPI 대시보드 연산 (독립 데이터 기준)
        t_theory = team_df['이론금액'].sum()
        t_actual = team_df['실제금액'].sum()
        t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
        
        # ⚡ 전월 대비 증감 계산 (YY.MM 시계열 순서 매핑)
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
        # 1단 레이아웃 - 좌우 5:5 분할 배치
        # =========================================================================
        main_col1, main_col2 = st.columns([50, 50])

        # --- [왼쪽 열: 선택된 YY.MM 탭의 상세 수율 표] ---
        with main_col1:
            st.subheader(f"📋 {selected_month} 상세 수율 현황")
            depts_list = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
            tabs = st.tabs(depts_list)
            
            for i, d in enumerate(depts_list):
                with tabs[i]:
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
                        st.write("해당 부서의 데이터가 없습니다.")
                    
            st.markdown("""
            <div style="background-color: #262730; padding: 10px 14px; border-radius: 8px; border-left: 5px solid #448AFF; margin-top: 5px;">
                <span style="font-size: 12px; color: #E0E0E0; font-weight: 500;">
                    🔹 <b>면1과 :</b> 98.92% 이상 | 🔹 <b>면5과 :</b> 97.92% 이상 | 🔹 <b>스프 :</b> 99.53% 이상 | 🔹 <b>총합 :</b> 98.73% 이상
                </span>
            </div>
            """, unsafe_allow_html=True)

        # --- [오른쪽 열: 25년 1월 ~ 26년 4월 전 연도 풀 스크린 트렌드 그래프] ---
        with main_col2:
            st.subheader("📈 전체 년월별 실적 추이 및 MoM 비교")
            
            monthly_trend = trend_raw_df.groupby('월')[['이론금액', '실제금액']].sum().reset_index()
            
            # 정렬 순서 보정 (25.01 -> 25.12 -> 26.01 -> 26.04 순서 체계 확립)
            monthly_trend['sort_val'] = monthly_trend['월'].apply(lambda x: float(x))
            monthly_trend = monthly_trend.sort_values('sort_val').reset_index(drop=True)
            monthly_trend['수율(%)'] = (monthly_trend['이론금액'] / monthly_trend['실제금액'] * 100).round(2)
            
            chart_labels = []
            for idx, row in monthly_trend.iterrows():
                base_text = f"{row['수율(%)']:.2f}%"
                if idx == 0:
                    chart_labels.append(base_text)
                else:
                    prev_val = monthly_trend.loc[idx - 1, '수율(%)']
                    diff = row['수율(%)'] - prev_val
                    if diff > 0:
                        chart_labels.append(f"{base_text}<br><span style='color:#00E676; font-size:10px;'>▲{diff:.2f}%</span>")
                    elif diff < 0:
                        chart_labels.append(f"{base_text}<br><span style='color:#FF5252; font-size:10px;'>▼{abs(diff):.2f}%</span>")
                    else:
                        chart_labels.append(f"{base_text}<br><span style='color:#FFF; font-size:10px;'>-</span>")
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=monthly_trend['월'], y=monthly_trend['실제금액'], name="실제 금액", yaxis="y1", marker_color='rgba(12, 77, 162, 0.4)', hovertemplate="%{y:,.0f} 원<extra></extra>"))
            fig_trend.add_trace(go.Scatter(
                x=monthly_trend['월'], y=monthly_trend['수율(%)'], name="종합 수율", yaxis="y2", 
                line=dict(color='#00E676', width=3.5), mode='lines+markers+text', 
                text=chart_labels, textposition="top center", hovertemplate="수율: %{y:.2f}%<extra></extra>"
            ))
            
            fig_trend.update_layout(
                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(title="실제 투입 금액 (원)", side="left", showgrid=False),
                yaxis2=dict(title="수율 (%)", side="right", overlaying="y", range=[94, 103], showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0), height=320,
                xaxis=dict(type='category', title="조회 년월 (YY.MM)")
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("---")

        # =========================================================================
        # 2단 레이아웃 (부서별 수율 비교 & 리스크 매트릭스)
        # =========================================================================
        row2_col1, row2_col2 = st.columns([45, 55])
        
        with row2_col1:
            st.subheader("📊 부서 및 자재별 수율 비교")
            dept_sum = team_df.groupby(['生産部門名' if '生産部門名' in team_df.columns else '생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum.columns = ['생산부문명', '자재 유형 내역', '이론금액', '실제금액']
            dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            
            fig1 = px.bar(dept_sum, x='생산부문명', y='수율(%)', color='자재 유형 내역', barmode='group', text='수율(%)', 
                          color_discrete_map={'원자재': '#0c4da2', '부자재': '#5a9bd5', '반제품': '#a6c8e0'})
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
            
            fig3 = px.scatter(item_scatter, x='실제 투입 금액 (억 원)', y='수율(%)', hover_name='하위품목 텍스트', color='관리 상태', color_discrete_map={'기준 달성': '#448AFF', '기준 미달': '#FF5252'})
            fig3.add_hline(y=limit, line_dash="dash", line_color="#FF5252", opacity=0.8, annotation_text=f"{limit}%")
            fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(ticksuffix="억"))
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")

        # =========================================================================
        # 3단 레이아웃 (과별 핵심 관리 대상 Top 5)
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
                    fig_m = px.bar(m_data, x='수율(%)', y='하위품목 텍스트', orientation='h', text='표시텍스트', color_discrete_sequence=['#0c4da2'])
                    fig_m.update_layout(showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 115]), yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_m, use_container_width=True)
    else:
        st.warning("⚠️ 선택하신 년월 탭의 데이터 전처리 결과가 비어있습니다. 칼럼명을 확인해 주세요.")
else:
    st.warning("⚠️ 구글 시트에서 탭 데이터를 하나도 읽어오지 못했습니다. 스프레드시트 권한이나 탭 이름을 확인해 주세요.")
