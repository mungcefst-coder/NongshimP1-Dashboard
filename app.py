import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. 페이지 세팅 및 타이틀
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템 V2.1")

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

# 사이드바 컨트롤러
with st.sidebar:
    st.header("📂 데이터 관리")
    months_list = ["전체 누적 데이터", "1월", "2월", "3월", "4월"]
    selected_month = st.selectbox("분석할 월 선택", months_list)
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="비워두면 전체 조회")

# 데이터 로드 및 정제 로직
@st.cache_data(ttl=600)
def load_and_process_gsheet(mode, sheet_id):
    try:
        # 추이 분석을 위해 모든 달 데이터를 미리 로드하는 내부 로직 포함
        all_months = ["1월", "2월", "3월", "4월"]
        loaded_dfs = []
        for m in all_months:
            encoded_sheet = urllib.parse.quote(m)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            temp = pd.read_csv(url)
            if not temp.empty:
                temp['월'] = m
                loaded_dfs.append(temp)
        
        full_df = pd.concat(loaded_dfs, ignore_index=True) if loaded_dfs else pd.DataFrame()
        
        # 전처리 공통 로직
        if full_df.empty: return pd.DataFrame(), pd.DataFrame()
        
        # 칼럼명 표준화
        full_df.columns = [c.replace('生産部門名', '생산부문명').replace('資재 유형 내역', '자재 유형 내역').replace('品目텍스트', '하위품목 텍스트').replace('理論金額', '이론금액').replace('實際金額', '실제금액') for c in full_df.columns]
        # 한글 깨짐 방지용 강제 매핑 (시트 상황에 따라 조정)
        full_df.rename(columns={'資材タイプテキスト': '자재 유형 내역', '品目テキスト': '하위품목 텍스트', 'Actual Amount': '실제금액', '实际金额': '실제금액'}, inplace=True)

        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        full_df = full_df[full_df['생산부문명'].isin(my_team)].copy()
        
        # 숫자 변환
        for col in ['이론금액', '실제금액']:
            full_df[col] = full_df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)
            
        # 선택한 모드에 따른 필터링 데이터 반환
        if mode == "전체 누적 데이터":
            filtered_df = full_df.copy()
        else:
            filtered_df = full_df[full_df['월'] == mode].copy()
            
        return filtered_df, full_df # (현재 선택 데이터, 추이용 전체 데이터)
    except:
        return pd.DataFrame(), pd.DataFrame()

team_df, trend_raw_df = load_and_process_gsheet(selected_month, SHEET_ID)

# 메인 화면 제목
st.title("🚀 생산1팀 통합 수율 관리 시스템 V2.1")
st.markdown(f"**현재 조회 데이터:** `{selected_month}`")
st.markdown("---")

if not team_df.empty:
    if search_keyword:
        team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]

    # ---------------------------------------------------------
    # 탭 구성 (V2.1 신규 구성)
    # ---------------------------------------------------------
    tab_main, tab_analysis, tab_trend = st.tabs(["📋 과별 상세 현황", "📊 상세 분석 및 매트릭스", "📈 실적 추이 분석 (New)"])

    # --- [TAB 1: 과별 상세 현황] ---
    with tab_main:
        # KPI MoM 계산 (전월 대비)
        t_theory = team_df['이론금액'].sum()
        t_actual = team_df['실제금액'].sum()
        t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
        
        # 전월 데이터 찾기 로직
        prev_yield = 0
        if "월" in selected_month:
            curr_idx = months_list.index(selected_month)
            if curr_idx > 1: # 1월보다 이후 달을 선택했을 때
                prev_m = months_list[curr_idx - 1]
                prev_df = trend_raw_df[trend_raw_df['월'] == prev_m]
                if not prev_df.empty:
                    prev_yield = (prev_df['이론금액'].sum() / prev_df['실제금액'].sum() * 100)
        
        delta_val = f"{t_yield - prev_yield:.2f}%" if prev_yield > 0 else None

        k1, k2, k3 = st.columns(3)
        k1.metric("🎯 이론 금액", f"{t_theory:,.0f} 원")
        k2.metric("💰 실제 금액", f"{t_actual:,.0f} 원")
        k3.metric("🏆 종합 수율", f"{t_yield:.2f} %", delta=delta_val, delta_color="normal")
        
        st.subheader("📋 부서별 세부 수율 지표")
        depts = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
        inner_tabs = st.tabs(depts)
        for i, d in enumerate(depts):
            with inner_tabs[i]:
                target = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                final = target.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                final.loc['원부자재 수율'] = [final.loc[final.index.isin(['원자재', '부자재']), '이론금액'].sum(), final.loc[final.index.isin(['원자재', '부자재']), '실제금액'].sum()]
                final.loc['전체 수율'] = [final.loc[final.index.isin(['원자재', '부자재', '반제품']), '이론금액'].sum(), final.loc[final.index.isin(['원자재', '부자재', '반제품']), '실제금액'].sum()]
                final['수율(%)'] = (final['이론금액'] / final['실제금액'] * 100)
                
                def make_signal_text(val, dept_name=d):
                    targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 총합': 98.73}
                    limit = 98.73 if dept_name == '전체 총합' else targets.get(dept_name, 95.0)
                    if pd.isna(val) or val == 0: return "-"
                    return f"🟢 {val:.2f}%" if val >= limit else f"🔴 {val:.2f}%"
                
                final['수율(%)'] = final['수율(%)'].apply(lambda x: make_signal_text(x))
                st.dataframe(final.reindex(['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율']).style.format({'이론금액': '{:,.0f}', '실제금액': '{:,.0f}'}), use_container_width=True)
        
        st.markdown("""<div style="background-color:#262730; padding:12px; border-radius:8px; border-left:5px solid #448AFF; margin-top:10px;">
            <span style="font-size:14px; color:#B9F6CA; font-weight:bold; margin-right:15px;">🎯 생산1팀 과별 수율 관리 기준 :</span>
            <span style="font-size:13px; color:#E0E0E0;">🔹 <b>1팀 면1과 :</b> 98.92% | 🔹 <b>1팀 면5과 :</b> 97.92% | 🔹 <b>1팀 스프 :</b> 99.53% | 🔹 <b>전체 총합 :</b> 98.73%</span>
        </div>""", unsafe_allow_html=True)

    # --- [TAB 2: 상세 분석 및 매트릭스] ---
    with tab_analysis:
        r2_c1, r2_c2 = st.columns([45, 55])
        with r2_c1:
            st.subheader("📊 부서/자재별 수율 비교")
            dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
            dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
            fig1 = px.bar(dept_sum, x='생산부문명', y='수율(%)', color='자재 유형 내역', barmode='group', text='수율(%)', color_discrete_map={'원자재': '#0c4da2', '부자재': '#5a9bd5', '반제품': '#a6c8e0'})
            fig1.update_layout(yaxis=dict(range=[80, 105]), template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
        
        with r2_c2:
            st.subheader("🔍 수율 리스크 매트릭스")
            scatter_dept = st.selectbox("부서 선택", ["전체 1팀", "1팀 면1과", "1팀 면5과", "1팀 스프"], key="matrix_filter")
            plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
            item_scatter = plot_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            item_scatter['수율(%)'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
            item_scatter['억'] = item_scatter['실제금액'] / 100000000
            
            targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 1팀': 98.73}
            limit = targets.get(scatter_dept, 98.0)
            item_scatter['상태'] = item_scatter['수율(%)'].apply(lambda x: '달성' if x >= limit else '미달')
            
            fig3 = px.scatter(item_scatter, x='억', y='수율(%)', hover_name='하위품목 텍스트', color='상태', color_discrete_map={'달성': '#448AFF', '미달': '#FF5252'})
            fig3.add_hline(y=limit, line_dash="dash", line_color="#FF5252", annotation_text=f"기준 {limit}%")
            fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(ticksuffix="억"))
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        st.subheader("🚨 집중 관리 대상 (Top 5)")
        item_sum = team_df[team_df['생산부문명'] != '1팀 스프'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_sum['수율(%)'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
        c1, c2 = st.columns(2)
        for i, d in enumerate(['1팀 면1과', '1팀 면5과']):
            with [c1, c2][i]:
                st.markdown(f"**📍 {d}**")
                m_data = item_sum[item_sum['생산부문명'] == d].sort_values('실제금액', ascending=False).head(15).sort_values('수율(%)', ascending=True).head(5)
                m_data['label'] = m_data.apply(lambda r: f"{r['수율(%)']:.2f}% | {(r['실제금액']/100000000):.2f}억", axis=1)
                fig = px.bar(m_data, x='수율(%)', y='하위품목 텍스트', orientation='h', text='label', color_discrete_sequence=['#0c4da2'])
                fig.update_layout(showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 115]))
                st.plotly_chart(fig, use_container_width=True)

    # --- [TAB 3: 실적 추이 분석 (신규)] ---
    with tab_trend:
        st.subheader("📈 월별 생산 수율 및 집행 금액 추이")
        
        # 월별 데이터 집계
        monthly_trend = trend_raw_df.groupby('월')[['이론금액', '실제금액']].sum().reset_index()
        # 월 순서 정렬
        monthly_trend['월순서'] = monthly_trend['월'].str.replace('월','').astype(int)
        monthly_trend = monthly_trend.sort_values('월순서')
        monthly_trend['수율(%)'] = (monthly_trend['이론금액'] / monthly_trend['실제금액'] * 100).round(2)
        
        # 콤보 차트 생성 (바 + 선)
        fig_trend = go.Figure()
        # 실제 금액 바 차트
        fig_trend.add_trace(go.Bar(x=monthly_trend['월'], y=monthly_trend['실제금액'], name="실제 집행 금액(원)", yaxis="y1", marker_color='rgba(12, 77, 162, 0.6)'))
        # 수율 꺾은선 차트
        fig_trend.add_trace(go.Scatter(x=monthly_trend['월'], y=monthly_trend['수율(%)'], name="종합 수율(%)", yaxis="y2", line=dict(color='#00E676', width=4), mode='lines+markers+text', text=monthly_trend['수율(%)'], textposition="top center"))
        
        fig_trend.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(title="집행 금액 (원)", side="left"),
            yaxis2=dict(title="수율 (%)", side="right", overlaying="y", range=[95, 101]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        st.info("💡 **데이터 분석 의견:** 수율 추세선이 수평을 유지하거나 우상향할 경우 공정 관리가 안정적임을 의미합니다. 급격한 하락 지점은 해당 월의 대형 리스크 품목 점검이 필요합니다.")
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 구글 시트 상태를 확인해 주세요.")
