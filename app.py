import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# 1. 페이지 메인 레이아웃 및 프리미엄 테마 주입
st.set_page_config(layout="wide", page_title="생산1팀 통합 수율 관리 시스템 V3.0", page_icon="🚀")

# 사진 속 고급 레이아웃을 구현하기 위한 하드웨어급 커스텀 CSS 주입
st.markdown("""
<style>
    /* 전체 폰트 세팅 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Noto Sans KR', sans-serif;
        background-color: #0f1319 !important;
    }
    
    /* 사이드바 숨김/디자인 매칭 */
    [data-testid="stSidebar"] {
        background-color: #131822 !important;
    }
    
    /* 왼쪽 블루 패널 스타일링 */
    .welcome-panel {
        background: linear-gradient(135deg, #0a3d82 0%, #1c5cb4 100%);
        border-radius: 16px;
        padding: 45px 35px;
        color: white;
        height: 100%;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .welcome-sub {
        font-size: 12px;
        letter-spacing: 2px;
        color: rgba(255,255,255,0.7);
        font-weight: bold;
        margin-bottom: 10px;
    }
    .welcome-title {
        font-size: 38px;
        font-weight: 700;
        line-height: 1.3;
        margin-bottom: 15px;
    }
    .welcome-desc {
        font-size: 14px;
        color: rgba(255,255,255,0.8);
        margin-bottom: 35px;
    }
    .check-item {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: 12px;
        font-size: 13px;
        display: flex;
        align-items: center;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* 서버 인디케이터 스타일 */
    .status-container {
        display: flex;
        gap: 20px;
        background: #161c28;
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #222d3f;
        margin-bottom: 25px;
    }
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #00E676;
        border-radius: 50%;
        margin-right: 6px;
        box-shadow: 0 0 8px #00E676;
    }
    
    /* 우측 메뉴 카드 그리드 디자인 */
    .menu-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
    }
    .menu-card {
        background: #1a2130;
        border: 1px solid #27354d;
        border-radius: 12px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.25s ease;
    }
    .menu-card:hover {
        border-color: #448AFF;
        background: #202b3e;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# 구글 스프레드시트 ID 고정
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"

# 사이드바 데이터 컨트롤러 유지
with st.sidebar:
    st.header("📂 데이터 필터")
    months = ["전체 누적 데이터", "1월", "2월", "3월", "4월"]
    selected_month = st.selectbox("분석할 월 선택", months)
    st.markdown("---")
    search_keyword = st.text_input("🔍 세부 품목 검색", placeholder="비워두면 전체 조회")

# 데이터 선행 로드
@st.cache_data(ttl=600)
def load_and_process_gsheet(mode, sheet_id):
    try:
        if mode == "전체 누적 데이터":
            all_dfs = []
            for m in ["1월", "2월", "3월", "4월"]:
                encoded_sheet = urllib.parse.quote(m)
                url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
                temp_df = pd.read_csv(url)
                if not temp_df.empty: temp_df['월'] = m; all_dfs.append(temp_df)
            df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        else:
            encoded_sheet = urllib.parse.quote(mode)
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            df = pd.read_csv(url)
            if not df.empty: df['월'] = mode
            
        if df.empty: return df
        if '生産部門名' in df.columns: df.rename(columns={'生産部門名': '생산부문명'}, inplace=True)
        if '資材タイプテキスト' in df.columns: df.rename(columns={'資材タイプテキスト': '자재 유형 내역'}, inplace=True)
        if '品目テキスト' in df.columns: df.rename(columns={'品目テキスト': '하위품목 텍스트'}, inplace=True)
        if '理論金額' in df.columns: df.rename(columns={'理論金額': '이론금액'}, inplace=True)
        if 'Actual Amount' in df.columns: df.rename(columns={'Actual Amount': '실제금액'}, inplace=True)
        if '实际金额' in df.columns: df.rename(columns={'实际金额': '실제금액'}, inplace=True)
        if '實際金額' in df.columns: df.rename(columns={'實際金額': '실제금액'}, inplace=True)
        if '실제금액' not in df.columns and '실적금액' in df.columns: df.rename(columns={'실적금액': '실제금액'}, inplace=True)

        my_team = ['1팀 면1과', '1팀 면5과', '1팀 스프']
        team_df = df[df['생산부문명'].isin(my_team)].copy()
        
        if '하위품목 텍스트' in team_df.columns:
            team_df['하위품목 텍스트'] = team_df['하위품목 텍스트'].astype(str).str.strip()
            for kw in ['소계', '합계', '총합', '총계', '결과', '부문명']:
                team_df = team_df[~team_df['하위품목 텍스트'].str.contains(kw, na=False)]

        team_df['자재 유형 내역'] = team_df['자재 유형 내역'].astype(str).str.strip()
        team_df = team_df[team_df['자재 유형 내역'].isin(['원자재', '부자재', '반제품'])]
        
        for col in ['이론금액', '실제금액']:
            team_df[col] = team_df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            team_df[col] = pd.to_numeric(team_df[col], errors='coerce').fillna(0)
            
        calculated_yield = (team_df['이론금액'] / team_df['실제금액']) * 100
        team_df = team_df[~((team_df['실제금액'] > 0) & (calculated_yield < 50))]
        return team_df
    except: return pd.DataFrame()

team_df = load_and_process_gsheet(selected_month, SHEET_ID)

# =========================================================================
# ⚡ [사진 반영] 메인 화면 레이아웃 대분할 (왼쪽 4.5 배너 : 오른쪽 5.5 메뉴창)
# =========================================================================
main_col1, main_col2 = st.columns([43, 57])

with main_col1:
    # 사진 속 왼쪽 파란색 판넬 시스템 소개 가이드 그대로 구현
    st.markdown("""
    <div class="welcome-panel">
        <div class="welcome-sub">BUSAN PLANT · PRODUCTION TEAM 1</div>
        <div class="welcome-title">생산계획 검토 및<br>조별 생산순서 시스템</div>
        <div class="welcome-desc">SCM 계획 업로드로부터 CAPA 검도, 조별 생산순서 편성, 최종 종합 실시간 수율 관리까지 하나의 흐름으로 통제합니다.</div>
        <div class="check-item">✓ &nbsp; SCM 엑셀 업로드 ➔ 자동 품목 매칭</div>
        <div class="check-item">✓ &nbsp; CAPA 적정성 자동 검도 및 수율 시각화</div>
        <div class="check-item">✓ &nbsp; 주간·야간 생산순서 자동 편성 관리</div>
        <div class="check-item">✓ &nbsp; 전환시간 최적화 및 리스크 매트릭스 도출</div>
        <div style="text-align: center; margin-top: 50px; opacity: 0.8;">
            <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line></svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

with main_col2:
    st.markdown("<p style='font-size:11px; color:#5a9bd5; letter-spacing:1px; margin:0;'>PPT / GOOGLE SHEET ENTRY</p>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; margin-bottom:20px; font-weight:700; color:#f8fafc;'>문서 링크 업무 시작</h3>", unsafe_allow_html=True)
    
    # ⚡ 사진 상단 실시간 인디케이터 상태창 연동
    st.markdown("""
    <div class="status-container">
        <div style="font-size:13px; color:#94a3b8;"><span class="status-dot"></span>Backend <b style="color:#FFF;">정상</b></div>
        <div style="font-size:13px; color:#94a3b8; margin-left:15px;"><span class="status-dot"></span>Database <b style="color:#FFF;">정상</b></div>
        <div style="font-size:13px; color:#94a3b8; margin-left:15px;"><span class="status-dot"></span>Storage <b style="color:#FFF;">정상</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ⚡ 사진의 9개 업무 카드 그리드를 무선 조종하는 선택 라디오 구현 (카드 클릭 대용 UI 효과)
    st.markdown("<p style='font-size:13px; color:#94a3b8; margin-bottom:5px;'>💡 조회하고 싶은 관제 시스템 업무 메뉴를 선택하세요 :</p>", unsafe_allow_html=True)
    current_work = st.radio("", ["📋 종합 상세 현황 표", "📊 부서별 수율 비교", "🚨 집중 리스크 Top 5", "🔍 수율 리스크 매트릭스"], horizontal=True, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")

# =========================================================================
# ⚡ 업무 메뉴 클릭 시 하단에 실제 데이터 관제 화면이 유기적으로 표출되는 종합 시스템
# =========================================================================
if not team_df.empty:
    if search_keyword:
        team_df = team_df[team_df['하위품목 텍스트'].str.contains(search_keyword, na=False)]
    
    # 최상단 총합 누계 KPI는 언제나 고정 관제
    t_theory, t_actual = team_df['이론금액'].sum(), team_df['실제금액'].sum()
    t_yield = (t_theory / t_actual * 100) if t_actual > 0 else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("🎯 선택월 이론 금액", f"{t_theory:,.0f} 원")
    kpi2.metric("💰 선택월 실제 금액", f"{t_actual:,.0f} 원")
    kpi3.metric("🏆 종합 실시간 수율", f"{t_yield:.2f} %")
    st.markdown("<br>", unsafe_allow_html=True)

    # 1번 업무 카드 실행 시
    if current_work == "📋 종합 상세 현황 표":
        st.subheader("📋 과별 상세 수율 현황 분석")
        depts_list = ['1팀 면1과', '1팀 면5과', '1팀 스프', '전체 총합']
        tabs = st.tabs(depts_list)
        for i, d in enumerate(depts_list):
            with tabs[i]:
                target_df = team_df if d == '전체 총합' else team_df[team_df['생산부문명'] == d]
                final_summ = target_df.groupby('자재 유형 내역')[['이론금액', '실제금액']].sum()
                final_summ.loc['원부자재 수율'] = [final_summ.loc[final_summ.index.isin(['원자재', '부자재']), '이론금액'].sum(), final_summ.loc[final_summ.index.isin(['원자재', '부자재']), '실제금액'].sum()]
                final_summ.loc['전체 수율'] = [final_summ.loc[final_summ.index.isin(['원자재', '부자재', '반제품']), '이론금액'].sum(), final_summ.loc[final_summ.index.isin(['원자재', '부자재', '반제품']), '실제금액'].sum()]
                final_summ['수율(%)'] = (final_summ['이론금액'] / final_summ['실제금액'] * 100)
                
                def get_custom_color(val, dept_name=d):
                    if pd.isna(val): return ''
                    t_limits = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53, '전체 총합': 98.73}
                    if val < t_limits.get(dept_name, 95.0): return 'color: #FF5252; font-weight: bold;'
                    return 'color: #448AFF; font-weight: bold;'
                
                st.dataframe(final_summ.reindex(['원자재', '부자재', '반제품', '원부자재 수율', '전체 수율']).style.format({'이론금액': '{:,.0f}', '실제금액': '{:,.0f}', '수율(%)': '{:.2f}%'}).map(get_custom_color, subset=['수율(%)']), use_container_width=True)
        
        st.markdown("""
        <div style="background-color: #161c28; padding: 12px 18px; border-radius: 8px; border-left: 5px solid #0c4da2; margin-top: 10px;">
            <span style="font-size: 13px; color: #B9F6CA; font-weight: bold; margin-right: 15px;">🎯 생산1팀 과별 수율 관리 기준 :</span>
            <span style="font-size: 12px; color: #E0E0E0;">🟢 <b>면1과:</b> 98.92% 이상 &nbsp;|&nbsp; 🟢 <b>면5과:</b> 97.92% 이상 &nbsp;|&nbsp; 🟢 <b>스프:</b> 99.53% 이상</span>
        </div>
        """, unsafe_allow_html=True)

    # 2번 업무 카드 실행 시
    elif current_work == "📊 부서별 수율 비교":
        st.subheader("📊 부서 및 자재별 수율 비교 통계")
        dept_sum = team_df.groupby(['생산부문명', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
        dept_sum['수율(%)'] = (dept_sum['이론금액'] / dept_sum['실제금액'] * 100).round(2)
        fig1 = px.bar(dept_sum, x='생산부문명', y='수율(%)', color='자재 유형 내역', barmode='group', text='수율(%)', 
                      category_orders={'자재 유형 내역': ['원자재', '부자재', '반제품']}, color_discrete_map={'원자재': '#0c4da2', '부자재': '#5a9bd5', '반제품': '#a6c8e0'})
        fig1.update_layout(yaxis=dict(range=[80, 105]), template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)

    # 3번 업무 카드 실행 시
    elif current_work == "🚨 집중 리스크 Top 5":
        st.subheader("🚨 과별 핵심 관리 대상 Top 5 (실제금액 상위 품목 중 수율 최저 순)")
        item_sum = team_df[team_df['생산부문명'] != '1팀 스프'].groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_sum['수율(%)'] = (item_sum['이론금액'] / item_sum['실제금액'] * 100).round(2)
        
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("**📍 면 1과 관리 품목**")
            m1 = item_sum[item_sum['생산부문명'] == '1팀 면1과'].copy()
            if not m1.empty:
                m1_top5 = m1.sort_values('실제금액', ascending=False).head(15).sort_values('수율(%)', ascending=True).head(5)
                m1_top5['txt'] = m1_top5.apply(lambda r: f"수율: {r['수율(%)']:.2f}% | 실제: {(r['실제금액']/100000000):.2f}억", axis=1)
                fig_m1 = px.bar(m1_top5, x='수율(%)', y='하위품목 텍스트', orientation='h', text='txt', color_discrete_sequence=['#0c4da2', '#2a69bd', '#4d88db', '#75a8f5', '#a3c7ff'])
                fig_m1.update_layout(showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 115]), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_m1, use_container_width=True)
        with rc2:
            st.markdown("**📍 면 5과 관리 품목**")
            m5 = item_sum[item_sum['생산부문명'] == '1팀 면5과'].copy()
            if not m5.empty:
                m5_top5 = m5.sort_values('실제금액', ascending=False).head(15).sort_values('수율(%)', ascending=True).head(5)
                m5_top5['txt'] = m5_top5.apply(lambda r: f"수율: {r['수율(%)']:.2f}% | 실제: {(r['실제금액']/100000000):.2f}억", axis=1)
                fig_m5 = px.bar(m5_top5, x='수율(%)', y='하위품목 텍스트', orientation='h', text='txt', color_discrete_sequence=['#0c4da2', '#2a69bd', '#4d88db', '#75a8f5', '#a3c7ff'])
                fig_m5.update_layout(showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 115]), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_m5, use_container_width=True)

    # 4번 업무 카드 실행 시
    elif current_work == "🔍 수율 리스크 매트릭스":
        st.subheader("🔍 수율 리스크 매트릭스 분석")
        lbl_col, select_col, _ = st.columns([15, 25, 60])
        with lbl_col: st.markdown("<p style='padding-top:35px; font-weight:bold; font-size:14px;'>🎯 매트릭스 과별 필터 :</p>", unsafe_allow_html=True)
        with select_col: scatter_dept = st.selectbox("", ["전체 1팀", "1팀 면1과", "1팀 면5과", "1팀 스프"], key="matrix_dept_filter")
        
        plot_df = team_df.copy() if scatter_dept == "전체 1팀" else team_df[team_df['생산부문명'] == scatter_dept].copy()
        item_scatter = plot_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
        item_scatter = item_scatter[item_scatter['실제금액'] > 0].copy()
        item_scatter['수율(%)'] = (item_scatter['이론금액'] / item_scatter['실제금액'] * 100).round(2)
        item_scatter['실제 투입 금액 (억 원)'] = item_scatter['실제금액'] / 100000000
        
        if not item_scatter.empty:
            def get_scatter_status(row):
                targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53}
                return '기준 달성' if row['수율(%)'] >= targets.get(row['생산부문명'], 95.0) else '기준 미달'
            item_scatter['관리 상태'] = item_scatter.apply(get_scatter_status, axis=1)
            
            fig3 = px.scatter(item_scatter, x='실제 투입 금액 (억 원)', y='수율(%)', hover_name='하위품목 텍스트', color='관리 상태', color_discrete_map={'기준 달성': '#448AFF', '기준 미달': '#FF5252'})
            fig3.update_traces(hovertemplate="<b>%{hovertext}</b><br><br>실제금액: %{x:.2f}억 원<br>수율: %{y:.2f}%<extra></extra>", marker=dict(size=11, opacity=0.9))
            
            targets = {'1팀 면1과': 98.92, '1팀 면5과': 97.92, '1팀 스프': 99.53}
            if scatter_dept in targets: fig3.add_hline(y=targets[scatter_dept], line_dash="dash", line_color="#FF5252", annotation_text=f"{targets[scatter_dept]}%")
            else: fig3.add_hline(y=98.0, line_dash="dash", line_color="#FFF", opacity=0.3)
            
            fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(ticksuffix="억"))
            st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 구글 시트 상태를 확인해 주세요.")
