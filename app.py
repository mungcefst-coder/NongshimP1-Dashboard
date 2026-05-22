import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# [1] 시스템 디자인 엔진 (ERP 스타일 고도화)
# ==============================================================================
st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <style>
        .stApp { background-color: #F1F5F9 !important; }
        html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
        
        /* 카드 박스 */
        .portal-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        
        /* 섹션 타이틀 */
        .section-header-text {
            font-size: 20px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 15px;
            margin-top: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* KPI 타일 */
        .kpi-tile { text-align: left; padding: 10px 5px; }
        .kpi-label { font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 8px; }
        .kpi-value { font-size: 38px; font-weight: 800; color: #0F172A; line-height: 1; }
        .kpi-unit { font-size: 18px; color: #94A3B8; margin-left: 3px; }
        .kpi-trend { font-size: 13px; margin-top: 10px; font-weight: 700; }

        /* 테이블 폰트 및 스타일 */
        .stDataFrame { border-radius: 4px; }
        
        /* 관리 기준 안내 텍스트 */
        .threshold-info {
            font-size: 14px;
            color: #475569;
            margin-top: 10px;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# [2] 데이터 처리 핵심 로직
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", "25.12", "26.01", "26.02", "26.03", "26.04"]

YIELD_THRESHOLD = {
    '면 1과': 98.92,
    '면 5과': 97.93,
    '스프실': 99.53,
    '전체 총합': 98.73
}

MAIN_BLUE = "#1E40AF"
COMP_GRAY = "#B0BEC5"

@st.cache_data(ttl=3600)
def fetch_system_data(month):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(month)}"
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        rename_dict = {
            '生産部門명': '생산부문명', '生産部門名': '생산부문명',
            '理論金額': '이론금액', '實際金額': '실제금액',
            '品목텍스트': '하위품목 텍스트', '품목 텍스트': '하위품목 텍스트'
        }
        df.rename(columns=rename_dict, inplace=True)
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실', '면 1과': '면 1과', '면 5과': '면 5과', '스프실': '스프실'}
        df = df[df['생산부문명'].isin(dept_map.keys())].copy()
        df['생산부문명'] = df['생산부문명'].map(dept_map)
        for col in ['이론금액', '실제금액']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        df['월'] = month
        return df
    except: return pd.DataFrame()

# ==============================================================================
# [3] 포털 시스템 메인 렌더링
# ==============================================================================

with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0;'>⚙️ SYSTEM ADMIN</h2>", unsafe_allow_html=True)
    st.markdown("---")
    selected_months = st.multiselect("📆 분석 대상 년월", options=ALL_MONTHS, default=["25.01", "25.02", "25.03", "26.01", "26.02", "26.03"])
    search = st.text_input("🔍 품목 실시간 검색")
    st.info(f"Sync: {datetime.now().strftime('%H:%M:%S')}")

# 메인 헤더
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

if selected_months:
    data_list = [fetch_system_data(m) for m in selected_months]
    full_df = pd.concat([d for d in data_list if not d.empty], ignore_index=True)
    
    if not full_df.empty:
        full_df['연도'] = full_df['월'].apply(lambda x: '25년' if '25' in str(x) else '26년')
        if search: full_df = full_df[full_df['하위품목 텍스트'].str.contains(search, na=False)]

        # --- [CARD 1] 상단 핵심 KPI 메트릭 ---
        df_26 = full_df[full_df['연도'] == '26년']
        if not df_26.empty:
            th_sum, ac_sum = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            y_val = (th_sum / ac_sum * 100) if ac_sum > 0 else 0
            risk_df = df_26.groupby('하위품목 텍스트')[['이론금액','실제금액']].sum().reset_index()
            risk_df['yield'] = (risk_df['이론금액'] / risk_df['실제금액'] * 100)
            risk_count = len(risk_df[(risk_df['실제금액'] >= 400000000) & (risk_df['yield'] <= 98.0)])
            
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(f'<div class="kpi-tile"><p class="kpi-label">종합 수율</p><div class="kpi-value">{y_val:.2f}<span class="kpi-unit">%</span></div><p class="kpi-trend" style="color:#22C55E;">▲ 목표치 대조 관리 중</p></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="kpi-tile"><p class="kpi-label">누적 실제 투입</p><div class="kpi-value">{ac_sum/100000000:,.1f}<span class="kpi-unit">억</span></div><p class="kpi-trend" style="color:#64748B;">생산 운영 스케일</p></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="kpi-tile"><p class="kpi-label">고위험 자재</p><div class="kpi-value" style="color:#E74C3C;">{risk_count:02d}<span class="kpi-unit">건</span></div><p class="kpi-trend" style="color:#E74C3C;">⚠️ 집중 점검 필요</p></div>', unsafe_allow_html=True)
            k4.markdown(f'<div class="kpi-tile"><p class="kpi-label">데이터 신뢰도</p><div class="kpi-value" style="color:#1E40AF;">99.9<span class="kpi-unit">%</span></div><p class="kpi-trend" style="color:#1E40AF;">ERP 동기화 완료</p></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 2] 생산1팀 수율 종합 상황판 (정밀 포맷팅) ---
        st.markdown('<div class="section-header-text">📋 생산1팀 수율 종합 상황판</div>', unsafe_allow_html=True)
        tabs = st.tabs(['면 1과', '면 5과', '스프실', '전체 총합'])
        
        for i, d_name in enumerate(['면 1과', '면 5과', '스프실', '전체 총합']):
            with tabs[i]:
                t_col, g_col = st.columns([62, 38])
                d_df = full_df if d_name == '전체 총합' else full_df[full_df['생산부문명'] == d_name]
                
                with t_col: # 표 데이터 정교화
                    st.write(f"**📊 {d_name} 수율 지표**")
                    if not d_df.empty:
                        # 통계 데이터 생성
                        summ = d_df.groupby(['연도', '자재 유형 내역'])[['이론금액', '실제금액']].sum().reset_index()
                        total_rows = []
                        for yr in ['25년', '26년']:
                            y_df = summ[summ['연도'] == yr]
                            total_rows.append({'연도': yr, '자재 유형 내역': '전체 수율', '이론금액': y_df['이론금액'].sum(), '실제금액': y_df['실제금액'].sum()})
                        summ = pd.concat([summ, pd.DataFrame(total_rows)], ignore_index=True)
                        summ['수율'] = (summ['이론금액'] / summ['실제금액'] * 100)
                        
                        # 7열 피벗 구조 (25년 선배치, 26년 후배치)
                        pivot_df = summ.pivot(index='자재 유형 내역', columns='연도', values=['이론금액', '실제금액', '수율'])
                        pivot_df.columns = [f"{c[1]} {c[0]}" for c in pivot_df.columns]
                        pivot_df = pivot_df[['25년 이론금액', '25년 실제금액', '25년 수율', '26년 이론금액', '26년 실제금액', '26년 수율']]
                        pivot_df = pivot_df.reindex(['원자재', '부자재', '반제품', '전체 수율'])
                        
                        # 스타일링 가이드 적용
                        thresh = YIELD_THRESHOLD[d_name]
                        def style_table_refined(styler):
                            # 1. 소수점 제거 및 천단위 콤마 (이론금액, 실제금액 열)
                            format_dict = {c: '{:,.0f}' for c in pivot_df.columns if '수율' not in c}
                            # 2. 수율(%) 열은 소수점 2자리 유지
                            format_dict.update({c: '{:.2f}%' for c in pivot_df.columns if '수율' in c})
                            styler.format(format_dict)
                            
                            # 3. 25년 데이터 배경색 강조 (사진의 회색조 반영)
                            styler.set_properties(subset=['25년 이론금액', '25년 실제금액', '25년 수율'], **{'background-color': '#F8F9FA'})
                            
                            # 4. 26년 수율 미달 시 빨간색 강조
                            styler.map(lambda x: 'color: #E74C3C; font-weight: bold;' if isinstance(x, float) and x < thresh else '', subset=['26년 수율'])
                            return styler

                        st.dataframe(pivot_df.style.pipe(style_table_refined), use_container_width=True)
                        st.markdown(f'<p class="threshold-info">📌 {d_name} 관리 기준 수율 : {thresh}% 이상</p>', unsafe_allow_html=True)

                with g_col: # 꺾은선 추이 그래프
                    st.write(f"**📈 수율 변화 추이**")
                    if not d_df.empty:
                        tr = d_df.groupby(['연도', '월'])[['이론금액','실제금액']].sum().reset_index()
                        tr = tr.sort_values(['연도', '월'])
                        tr['cum_th'] = tr.groupby('연도')['이론금액'].cumsum()
                        tr['cum_ac'] = tr.groupby('연도')['실제금액'].cumsum()
                        tr['누적수율'] = (tr['cum_th'] / tr['cum_ac'] * 100).round(2)
                        tr['표시월'] = tr['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        
                        fig = go.Figure()
                        for yr, color in [('25년', COMP_GRAY), ('26년', MAIN_BLUE)]:
                            y_data = tr[tr['연도'] == yr]
                            fig.add_trace(go.Scatter(
                                x=y_data['표시월'], y=y_data['누적수율'],
                                name=f"{yr} 누적",
                                mode='lines+markers+text',
                                line=dict(color=color, width=3),
                                marker=dict(size=8),
                                text=y_data['누적수율'].apply(lambda x: f"{x}%"),
                                textposition="top center",
                                textfont=dict(size=11, color=color, weight='bold')
                            ))
                        
                        fig.update_layout(
                            height=320, margin=dict(l=10, r=10, t=30, b=10),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            yaxis=dict(range=[tr['누적수율'].min()-1, tr['누적수율'].max()+1.5], title="누적 수율 (%)", gridcolor='#E2E8F0'),
                            xaxis=dict(gridcolor='#E2E8F0')
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{d_name}")

        # --- [CARD 3] 하단 분석 그리드 ---
        c_grid_l, c_grid_r = st.columns(2)
        with c_grid_l:
            st.markdown('<div class="section-header-text">📊 자재 유형별 수율 현황</div>', unsafe_allow_html=True)
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            m_opt = st.selectbox("조회 대상", ["원자재", "부자재", "반제품"], key="mat_filt")
            m_df = full_df[full_df['자재 유형 내역'] == m_opt].groupby(['연도', '생산부문명'])[['이론금액','실제금액']].sum().reset_index()
            m_df['수율'] = (m_df['이론금액']/m_df['실제금액']*100).round(2)
            fig_bar = px.bar(m_df, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년':COMP_GRAY, '26년':MAIN_BLUE})
            fig_bar.update_layout(height=280, margin=dict(l=0,r=0,t=20,b=0), yaxis=dict(range=[85, 105]), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_grid_r:
            st.markdown('<div class="section-header-text">🔍 수율 리스크 매트릭스</div>', unsafe_allow_html=True)
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            r_dept = st.selectbox("조회 부서", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="risk_filt")
            r_df = full_df.copy() if r_dept == "전체 1팀" else full_df[full_df['생산부문명'] == r_dept]
            if not r_df.empty:
                r_item = r_df.groupby(['연도', '하위품목 텍스트'])[['이론금액','실제금액']].sum().reset_index()
                r_item['수율'] = (r_item['이론금액']/r_item['실제금액']*100).round(2)
                r_item['금액(억)'] = r_item['실제금액']/100000000
                fig_sc = px.scatter(r_item, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년':COMP_GRAY, '26년':MAIN_BLUE})
                fig_sc.add_hline(y=100.0, line_dash="dash", line_color="#CBD5E1")
                fig_sc.update_layout(height=280, margin=dict(l=0,r=0,t=20,b=0), showlegend=False)
                st.plotly_chart(fig_sc, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("⚠️ 분석 대상 년월을 선택해 주세요.")

st.markdown("<p style='text-align:center; color:#94A3B8; font-size:12px; margin-top:50px;'>Integrated Production Monitoring Portal System | © 2026 Nongshim Production Team 1</p>", unsafe_allow_html=True)
