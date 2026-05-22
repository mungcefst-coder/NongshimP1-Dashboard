import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime

# ==============================================================================
# [1] 시스템 포털 엔진 설계 (Deep CSS)
# ==============================================================================
st.set_page_config(layout="wide", page_title="생산1팀 Smart 수율 모니터링 Portal")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* [전체 배경] */
        .stApp { background-color: #F1F5F9 !important; }
        html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
        
        /* [흰색 카드 제거] */
        .portal-card {
            background-color: transparent !important;
            padding: 5px 0px !important;
            border: none !important;
            box-shadow: none !important;
            margin-bottom: 5px !important;
        }
        
        /* [메인 타이틀] */
        .section-header-text {
            font-size: 21px !important;
            font-weight: 800 !important;
            color: #0F172A !important;
            margin-bottom: 20px !important;
            margin-top: 35px !important;
            letter-spacing: -0.8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* [KPI 위젯 레이아웃] */
        .kpi-tile { text-align: left; }
        .kpi-label { font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 8px; }
        .kpi-value { font-size: 42px; font-weight: 800; color: #0F172A; line-height: 1; letter-spacing: -1px; }
        .kpi-unit { font-size: 18px; color: #94A3B8; margin-left: 2px; font-weight: 600; }
        .kpi-trend { font-size: 14px; margin-top: 10px; font-weight: 700; }

        /* [기타 UI] */
        section[data-testid="stSidebar"] { background-color: #1E293B !important; }
        section[data-testid="stSidebar"] * { color: white !important; }
        .stTabs [data-baseweb="tab"] p { font-size: 15px !important; font-weight: 700 !important; }
        .stDataFrame { border: none !important; background-color: transparent !important; }
        div[data-testid="stNotification"], .stAlert { background-color: transparent !important; border: none !important; padding: 0 !important; }
        .block-container { padding-top: 2.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# [2] 데이터 처리 핵심 엔진
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", "25.12", "26.01", "26.02", "26.03", "26.04"]
YIELD_TARGET = 98.73  # 전사 관리 기준 수율

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
    st.markdown("---")
    selected_months = st.multiselect("📆 분석 기간 (YY.MM)", options=ALL_MONTHS, default=["26.01", "26.02", "26.03"])
    search = st.text_input("🔍 품목 실시간 검색")
    st.markdown("---")
    st.write(f"Sync: {datetime.now().strftime('%H:%M:%S')}")

# --- [메인 헤더] ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 30px; border-bottom: 1px solid #CBD5E1; padding-bottom: 15px;">
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
            <p style="color: #94A3B8; font-size: 11px; margin-top: 8px; font-weight: 600;">
                {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
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

        # --- [CARD 1: KPI 센터] (수율 판정 로직 및 명칭 수정) ---
        df_26 = full_df[full_df['연도'] == '26년']
        if not df_26.empty:
            th_s, ac_s = df_26['이론금액'].sum(), df_26['실제금액'].sum()
            y_v = (th_s / ac_s * 100) if ac_s > 0 else 0
            
            # 수율 목표 판정
            if y_v >= YIELD_TARGET:
                yield_status = "▲ 수율 달성"
                yield_color = "#22C55E" # 녹색
            else:
                yield_status = "▼ 수율 미달"
                yield_color = "#E74C3C" # 빨간색

            risk_df = df_26.groupby('하위품목 텍스트')[['이론금액','실제금액']].sum().reset_index()
            risk_df['yield'] = (risk_df['이론금액'] / risk_df['실제금액'] * 100)
            r_count = len(risk_df[(risk_df['실제금액'] >= 400000000) & (risk_df['yield'] <= 98.0)])
            
            st.markdown('<div class="portal-card">', unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3) # 데이터 신뢰도 삭제 후 3열 구성
            with k1: 
                st.markdown(f'''
                    <div class="kpi-tile">
                        <p class="kpi-label">종합 수율</p>
                        <div class="kpi-value">{y_v:.2f}<span class="kpi-unit">%</span></div>
                        <p class="kpi-trend" style="color:{yield_color};">{yield_status}</p>
                    </div>
                ''', unsafe_allow_html=True)
            with k2: 
                st.markdown(f'''
                    <div class="kpi-tile">
                        <p class="kpi-label">실제 투입 금액</p>
                        <div class="kpi-value">{ac_s/100000000:,.1f}<span class="kpi-unit">억</span></div>
                        <p class="kpi-trend" style="color:#64748B;">KRW 누적 실적</p>
                    </div>
                ''', unsafe_allow_html=True)
            with k3: 
                st.markdown(f'''
                    <div class="kpi-tile">
                        <p class="kpi-label">고위험 자재</p>
                        <div class="kpi-value" style="color:#E74C3C;">{r_count:02d}<span class="kpi-unit">건</span></div>
                        <p class="kpi-trend" style="color:#E74C3C;">⚠️ 정밀 점검 대상</p>
                    </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [1. 부문별 상세 수율] ---
        st.markdown('<div class="section-header-text">📋 부문별 상세 수율 및 변화 트렌드</div>', unsafe_allow_html=True)
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        tabs = st.tabs(['면 1과', '면 5과', '스프실', '전체 총합'])
        for i, d_n in enumerate(['면 1과', '면 5과', '스프실', '전체 총합']):
            with tabs[i]:
                c_l, c_r = st.columns([40, 60])
                t_df = full_df if d_n == '전체 총합' else full_df[full_df['생산부문명'] == d_n]
                with c_l:
                    if not t_df.empty:
                        pv = t_df.groupby(['연도', '자재 유형 내역'])[['이론금액','실제금액']].sum().reset_index()
                        pv['수율(%)'] = (pv['이론금액']/pv['실제금액']*100).round(2)
                        st.dataframe(pv.pivot(index='자재 유형 내역', columns='연도', values='수율(%)').style.format("{:.2f}%"), use_container_width=True)
                with c_r:
                    if not t_df.empty:
                        tr = t_df.groupby(['연도', '월'])[['이론금액','실제금액']].sum().reset_index()
                        tr['수율'] = (tr['이론금액']/tr['실제금액']*100).round(2)
                        tr['표시월'] = tr['월'].apply(lambda x: f"{int(x.split('.')[1])}월")
                        fig = px.area(tr, x='표시월', y='수율', color='연도', markers=True, color_discrete_map={'25년':'#CBD5E1', '26년':'#1E40AF'})
                        fig.update_layout(height=240, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_v6_{d_n}")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [2. 자재 유형 비교 & 3. 리스크 매트릭스] ---
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        cl, cr = st.columns(2)
        with cl:
            st.markdown('<p class="section-header-text">📊 자재 유형별 실적 비교</p>', unsafe_allow_html=True)
            m_o = st.selectbox("자재 유형 선택", ["원자재", "부자재", "반제품"], key="mat_filt_v6")
            m_d = full_df[full_df['자재 유형 내역'] == m_o].groupby(['연도', '생산부문명'])[['이론금액','실제금액']].sum().reset_index()
            m_d['수율'] = (m_d['이론금액']/m_d['실제금액']*100).round(2)
            fig_b = px.bar(m_d, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년':'#CBD5E1', '26년':'#1E40AF'})
            fig_b.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[85, 105]), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_b, use_container_width=True)
            
        with cr:
            st.markdown('<p class="section-header-text">🔍 수율 리스크 매트릭스</p>', unsafe_allow_html=True)
            r_p = st.selectbox("관제 부서 선택", ["전체 1팀", "면 1과", "면 5과", "스프실"], key="risk_filt_v6")
            r_d = full_df.copy() if r_p == "전체 1팀" else full_df[full_df['생산부문명'] == r_p]
            if not r_d.empty:
                r_i = r_d.groupby(['연도', '하위품목 텍스트'])[['이론금액','실제금액']].sum().reset_index()
                r_i['수율'] = (r_i['이론금액']/r_i['실제금액']*100).round(2)
                r_i['금액(억)'] = r_i['실제금액']/100000000
                fig_s = px.scatter(r_i, x='금액(억)', y='수율', color='연도', hover_name='하위품목 텍스트', color_discrete_map={'25년':'#CBD5E1', '26년':'#1E40AF'})
                fig_s.add_hline(y=100.0, line_dash="dash", line_color="#CBD5E1")
                fig_s.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_s, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [4. 중점 관리 리스트] ---
        st.markdown('<div class="section-header-text">🚨 중점 관리 품목 (수율 하위 Top 5)</div>', unsafe_allow_html=True)
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        t_y = st.radio("실적 기준 연도", ["26년", "25년"], horizontal=True)
        y_d = full_df[full_df['연도'] == t_y]
        if not y_d.empty:
            t_s = y_d.groupby(['생산부문명', '하위품목 텍스트'])[['이론금액', '실제금액']].sum().reset_index()
            t_s['수율'] = (t_s['이론금액'] / t_s['실제금액'] * 100).round(2)
            tc1, tc2 = st.columns(2)
            for i, d_n in enumerate(['면 1과', '면 5과']):
                with [tc1, tc2][i]:
                    st.markdown(f"<p style='font-weight:700; color:#1E40AF; margin-bottom:10px;'>📍 {d_n} 하위 수율 Top 5</p>", unsafe_allow_html=True)
                    d_t = t_s[t_s['생산부문명'] == d_n].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                    if not d_t.empty:
                        d_t['label'] = d_t.apply(lambda r: f"{r['수율']:.2f}% ({(r['실제금액']/100000000):.1f}억)", axis=1)
                        fig_t = px.bar(d_t, x='수율', y='하위품목 텍스트', orientation='h', text='label', color_discrete_sequence=['#1E40AF' if t_y == '26년' else '#CBD5E1'])
                        fig_t.update_layout(height=260, margin=dict(l=0,r=10,t=10,b=10), xaxis=dict(range=[0, 135]), yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_t, use_container_width=True, key=f"top_list_v6_{d_n}")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.write("분석 기간을 선택해주세요.")

st.markdown("<p style='text-align:center; color:#94A3B8; font-size:12px; margin-top:50px;'>Integrated Monitoring Portal | © 2026 Nongshim Production Team 1</p>", unsafe_allow_html=True)
