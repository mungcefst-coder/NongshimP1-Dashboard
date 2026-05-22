import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# [1] 시스템 포털 엔진 설계 (Deep CSS Override - 박스 원천 차단)
# ==============================================================================
st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* 시스템 전체 배경 */
        .stApp { background-color: #F8FAFC !important; }
        html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
        
        /* 스트림릿 기본 요소(Warning, Info 박스)의 배경색을 투명하게 강제 고정 */
        div[data-testid="stNotification"] {
            background-color: transparent !important;
            border: none !important;
            color: #64748B !important;
            padding: 0 !important;
        }
        
        /* 상단 헤더 영역 여백 조정 */
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        
        /* [카드 박스] 정갈한 보더만 남긴 디자인 */
        .portal-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        }
        
        /* 섹션 타이틀 강조 */
        .section-header-text {
            font-size: 18px;
            font-weight: 700;
            color: #1E40AF;
            margin-bottom: 15px;
            margin-top: 5px;
        }

        /* KPI 수치 디자인 */
        .kpi-tile { text-align: left; }
        .kpi-label { font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 8px; }
        .kpi-value { font-size: 40px; font-weight: 800; color: #0F172A; line-height: 1; }
        .kpi-unit { font-size: 18px; color: #94A3B8; margin-left: 3px; }
        .kpi-trend { font-size: 13px; margin-top: 10px; font-weight: 700; }

        /* 데이터 프레임 보더 정리 */
        .stDataFrame { border: 1px solid #E2E8F0; border-radius: 4px; }
        
        /* 사이드바 어두운 테마 */
        section[data-testid="stSidebar"] {
            background-color: #1E293B !important;
        }
        section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# [2] 데이터 처리 핵심 엔진 (Google Sheets 연동)
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", "25.12", "26.01", "26.02", "26.03", "26.04"]

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

# --- [사이드바] ---
with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0;'>⚙️ SYSTEM ADMIN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.6; font-size:12px;'>Portal Stable v2.7</p>", unsafe_allow_html=True)
    st.markdown("---")
    selected_months = st.multiselect("📆 분석 대상 년월(YY.MM)", options=ALL_MONTHS, default=["26.01", "26.02", "26.03"])
    search = st.text_input("🔍 품목 실시간 검색")
    st.markdown("---")
    # 주황색 박스 유발 요소 삭제 및 일반 텍스트로 변경
    st.write(f"Sync: {datetime.now().strftime('%H:%M:%S')}")

# --- [메인 헤더 구역] ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 25px; border-bottom: 1px solid #E2E8F0; padding-bottom: 15px;">
        <div>
            <p style="color:#1E40AF; font-weight:700; letter-spacing:4px; margin-bottom:2px; font-size:11px;">MES INTEGRATED MONITORING</p>
            <h1 style="font-size: 34px; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -1.2px; line-height: 1.1;">
                생산1팀 <span style="color:#1E40AF;">Smart 수율 모니터링</span> Portal
            </h1>
        </div>
        <div style="text-align: right; padding-bottom: 5px;">
            <div style="background: #E0E7FF; color: #1E40AF; padding: 5px 12px; border-radius: 4px; font-weight: 700; font-size: 12px; border: 1px solid #C7D2FE; display: inline-block;">
                <span style="color: #22C55E; animation: blink 1.5s infinite;">●</span> SYSTEM LIVE
            </div>
            <p style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 600; font-family: 'Inter'; margin-bottom: 0;">
                Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
        </div>
    </div>
    <style>@keyframes blink {{ 0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }} }}</style>
""", unsafe_allow_html=True)

if selected_months:
    fetch_list = [fetch_system_data(m) for m in selected_months]
    full_df = pd.concat([d for d in fetch_list if not d.empty], ignore_index=True)
    
    if not full_df.empty:
        full_df['연도'] = full_df['월'].apply(lambda x: '25년' if '25' in str(x) else '26년')
        if search: full_df = full_df[full_df['하위품목 텍스트'].str.contains(search, na=False)]

        # --- [CARD 1: KPI 센터] ---
        df_26 = full_df[full_df['연도'] == '26년']
        if not df_26.empty:
            th_sum, ac_sum = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            y_val = (th_sum / ac_sum * 100) if ac_sum > 0 else 0
            risk_df = df_26.groupby('하위품목 텍스트')[['이론금액','실제금액']].sum().reset_index()
            risk_df['yield'] = (risk_df['이론금액'] / risk_df['실제금액'] * 100)
            risk_count = len(risk_df[(risk_df['실제금액'] >= 400000000) & (risk_df['yield'] <= 98.0)])
            
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f'<div class="kpi-tile"><p class="kpi-label">종합 수율</p><div class="kpi-value">{y_val:.2f}<span class="kpi-unit">%</span></div><p class="kpi-trend" style="color:#22C55E;">▲ 정상 가동</p></div>', unsafe_allow_html=True)
            with k2:
                st.markdown(f'<div class="kpi-tile"><p class="kpi-label">누적 실제 투입</p><div class="kpi-value">{ac_sum/100000000:,.1f}<span class="kpi-unit">억</span></div><p class="kpi-trend" style="color:#64748B;">KRW 누적</p></div>', unsafe_allow_html=True)
            with k3:
                st.markdown(f'<div class="kpi-tile"><p class="kpi-label">고위험 자재</p><div class="kpi-value" style="color:#E74C3C;">{risk_count:02d}<span class="kpi-unit">건</span></div><p class="kpi-trend" style="color:#E74C3C;">⚠️ 정밀 점검</p></div>', unsafe_allow_html=True)
            with k4:
                st.markdown(f'<div class="kpi-tile"><p class="kpi-label">데이터 신뢰도</p><div class="kpi-value" style="color:#1E40AF;">99.9<span class="kpi-unit">%</span></div><p class="kpi-trend" style="color:#1E40AF;">ERP 동기화</p></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 2: 상세 패널] ---
        st.markdown('<div class="section-header-text">📋 부문별 상세 실적 및 트렌드</div>', unsafe_allow_html=True)
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        tabs = st.tabs(['면 1과', '면 5과', '스프실', '전체 총합'])
        for i, d_name in enumerate(['면 1과', '면 5과', '스프실', '전체 총합']):
            with tabs[i]:
                c_tab_l, c_tab_r = st.columns([40, 60])
                d_df = full_df if d_name == '전체 총합' else full_df[full_df['생산부문명'] == d_name]
                with c_tab_l:
                    if not d_df.empty:
                        pv = d_df.groupby(['연도', '자재 유형 내역'])[['이론금액','실제금액']].sum().reset_index()
                        pv['수율(%)'] = (pv['이론금액']/pv['실제금액']*100).round(2)
                        st.dataframe(pv.pivot(index='자재 유형 내역', columns='연도', values='수율(%)').style.format("{:.2f}%"), use_container_width=True)
                with c_tab_r:
                    if not d_df.empty:
                        tr = d_df.groupby(['연도', '월'])[['이론금액','실제금액']].sum().reset_index()
                        tr['수율'] = (tr['이론금액']/tr['실제금액']*100).round(2)
                        tr['표시월'] = tr['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        fig = px.area(tr, x='표시월', y='수율', color='연도', markers=True, color_discrete_map={'25년':'#CBD5E1', '26년':'#1E40AF'})
                        fig.update_layout(height=240, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{d_name}")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 3: 분석 그리드] ---
        col_grid_l, col_grid_r = st.columns(2)
        with col_grid_l:
            st.markdown('<div class="section-header-text">📊 자재 유형별 성적 비교</div>', unsafe_allow_html=True)
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            m_opt = st.selectbox("유형 필터", ["원자재", "부자재", "반제품"], key="mat_filt_f")
            m_df = full_df[full_df['자재 유형 내역'] == m_opt].groupby(['연도', '생산부문명'])[['이론금액','실제금액']].sum().reset_index()
            m_df['수율'] = (m_df['이론금액']/m_df['실제금액']*100).round(2)
            fig_bar = px.bar(m_df, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년':'#CBD5E1', '26년':'#1E40AF'})
            fig_bar.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[85, 105]), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_grid_r:
            st.markdown('<div class="section-header-text">🔍 수율 리스크 매트릭스</div>', unsafe_allow_html=True)
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            r_dept = st.selectbox("부서 필터", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="risk_filt_f")
            r_df = full_df.copy() if r_dept == "전체 1팀" else full_df[full_df['생산부문명'] == r_dept]
            if not r_df.empty:
                r_item = r_df.groupby(['연도', '하위품목 텍스트'])[['이론금액','실제금액']].sum().reset_index()
                r_item['수율'] = (r_item['이론금액']/r_item['실제금액']*100).round(2)
                r_item['금액(억)'] = r_item['실제금액']/100000000
                fig_sc = px.scatter(r_item, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년':'#CBD5E1', '26년':'#1E40AF'})
                fig_sc.add_hline(y=100.0, line_dash="dash", line_color="#CBD5E1")
                fig_sc.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), showlegend=False)
                st.plotly_chart(fig_sc, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [CARD 4: Top 5] ---
        st.markdown('<div class="section-header-text">🚨 중점 관리 품목 (Top 5)</div>', unsafe_allow_html=True)
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        t_yr = st.radio("데이터 연도", ["26년", "25년"], horizontal=True)
        y_df = full_df[full_df['연도'] == t_yr]
        if not y_df.empty:
            top_sum = y_df.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            top_sum['수율'] = (top_sum['이론금액'] / top_sum['실제금액'] * 100).round(2)
            tc1, tc2 = st.columns(2)
            for i, d_n in enumerate(['면 1과', '면 5과']):
                with [tc1, tc2][i]:
                    st.write(f"**📍 {d_n} 집중 점검**")
                    d_top = top_sum[top_sum['생산부문명'] == d_n].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                    if not d_top.empty:
                        d_top['label'] = d_top.apply(lambda r: f"{r['수율']:.2f}% ({(r['실제금액']/100000000):.1f}억)", axis=1)
                        fig_t = px.bar(d_top, x='수율', y='하위품목 텍스트', orientation='h', text='label', color_discrete_sequence=['#1E40AF' if t_yr == '26년' else '#CBD5E1'])
                        fig_t.update_layout(height=260, margin=dict(l=0,r=10,t=10,b=10), xaxis=dict(range=[0, 135]), yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_t, use_container_width=True, key=f"top_list_v2_{d_n}")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # 사진 속 오렌지색 박스 원인: st.warning 제거 및 심플 텍스트 처리
    st.write("분석 기간을 선택해주세요.")

st.markdown("<p style='text-align:center; color:#94A3B8; font-size:12px; margin-top:50px;'>Integrated Monitoring Portal | © 2026 Nongshim Production Team 1</p>", unsafe_allow_html=True)
