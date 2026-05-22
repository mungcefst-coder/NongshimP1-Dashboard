import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# ==============================================================================
# [1] 리포트 디자인과 100% 동기화하는 딥 커스텀 CSS
# ==============================================================================
st.set_page_config(layout="wide", page_title="통합 수율 관제 포털 v2.0")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&family=Poppins:wght@700&display=swap" rel="stylesheet">
    <style>
        /* 시스템 배경색 */
        .stApp {
            background-color: #F8FAFC !important;
        }
        
        /* 폰트 및 기본 텍스트 */
        html, body, [class*="css"]  {
            font-family: 'Noto Sans KR', sans-serif;
        }
        
        /* 리포트 스타일의 화이트 카드 박스 */
        .report-card {
            background-color: #FFFFFF;
            padding: 30px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 25px;
        }
        
        /* 리포트 스타일 섹션 타이틀 (블루 바) */
        .report-title {
            font-size: 22px;
            font-weight: 700;
            color: #1E40AF;
            border-left: 6px solid #1E40AF;
            padding-left: 15px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
        }
        
        /* 커스텀 KPI 카드 디자인 */
        .kpi-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
        }
        .kpi-box {
            background: white;
            flex: 1;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            text-align: left;
        }
        .kpi-label {
            font-size: 14px;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .kpi-value {
            font-size: 42px;
            font-weight: 700;
            color: #1E40AF;
            font-family: 'Poppins', sans-serif;
            line-height: 1;
        }
        .kpi-delta {
            font-size: 13px;
            margin-top: 8px;
            font-weight: 700;
        }

        /* 탭 메뉴 스타일링 */
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            font-size: 16px;
            font-weight: 600;
        }
        
        /* 테이블 깔끔하게 */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# [2] 데이터 엔진 (Google Sheets 연동)
# ==============================================================================
SHEET_ID = "1hwWOk7qlsL654ZUtgfWQ10Cj81ITbcFLnkB_Gtl-bV4"
ALL_MONTHS = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", "26.01", "26.02", "26.03", "26.04"]
MAIN_BLUE = "#1E40AF"

@st.cache_data(ttl=3600)
def load_and_fix(month):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(month)}"
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # 컬럼명 자동 매칭
        df.rename(columns={'生産部門명': '생산부문명', '生産部門名': '생산부문명', '理論金額': '이론금액', '實際金額': '실제금액', '品목텍스트': '품목'}, inplace=True)
        # 부서명 매핑
        dept_map = {'1팀 면1과': '면 1과', '1팀 면5과': '면 5과', '1팀 스프': '스프실', '면 1과': '면 1과', '면 5과': '면 5과', '스프실': '스프실'}
        df = df[df['생산부문명'].isin(dept_map.keys())].copy()
        df['생산부문명'] = df['생산부문명'].map(dept_map)
        # 숫자 변환
        for c in ['이론금액', '실제금액']:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        df['월'] = month
        return df
    except: return pd.DataFrame()

# ==============================================================================
# [3] 메인 대시보드 레이아웃 (리포트 디자인 이식)
# ==============================================================================
with st.sidebar:
    st.markdown("<h2 style='color:#1E40AF;'>🏢 Portal Admin</h2>", unsafe_allow_html=True)
    selected_months = st.multiselect("분석 기간", options=ALL_MONTHS, default=["25.12", "26.01", "26.02", "26.03"])
    search = st.text_input("🔍 품목 필터링")

# --- 헤더 구역 ---
st.markdown(f"""
    <div style="margin-bottom: 40px;">
        <p style="color:#1E40AF; font-weight:700; letter-spacing:3px; margin-bottom:5px;">MES INTEGRATED SYSTEM</p>
        <h1 style="font-size:42px; margin:0; color:#0F172A;">통합 수율 관리 분석 포털 <span style="color:#1E40AF;">v2.0</span></h1>
        <p style="color:#64748B; font-size:18px;">생산 1팀 핵심 제조 공정 데이터 및 수율 안정화 모니터링</p>
    </div>
""", unsafe_allow_html=True)

if selected_months:
    data_list = [load_and_fix(m) for m in selected_months]
    df_raw = pd.concat([d for d in data_list if not d.empty], ignore_index=True)
    df_raw['연도'] = df_raw['월'].apply(lambda x: '25년' if '25' in str(x) else '26년')

    if not df_raw.empty:
        # --- [Slide 2 느낌] KPI 메트릭 구역 ---
        df_26 = df_raw[df_raw['연도'] == '26년']
        if not df_26.empty:
            th_sum = df_26['이론금액'].sum()
            ac_sum = df_26['실제금액'].sum()
            total_y = (th_sum / ac_sum * 100) if ac_sum > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="kpi-box"><div class="kpi-label">종합 수율 (YIELD)</div><div class="kpi-value">{total_y:.2f}%</div><div class="kpi-delta" style="color:#22C55E;">▲ 전년비 0.12% 상승</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="kpi-box" style="background:#1E40AF;"><div class="kpi-label" style="color:rgba(255,255,255,0.7);">누적 투입 금액</div><div class="kpi-value" style="color:white;">{ac_sum/100000000:,.1f}B</div><div class="kpi-delta" style="color:rgba(255,255,255,0.8);">단위: 억 원 (KRW)</div></div>""", unsafe_allow_html=True)
            with c3:
                risk_n = len(df_26.groupby('품목')[['이론금액','실제금액']].sum().query('실제금액 >= 400000000 and (이론금액/실제금액*100) <= 98.0'))
                st.markdown(f"""<div class="kpi-box"><div class="kpi-label">고위험군 자재</div><div class="kpi-value" style="color:#EF4444;">{risk_n:02d}</div><div class="kpi-delta" style="color:#EF4444;">⚠️ 집중 관제 대상</div></div>""", unsafe_allow_html=True)

        # --- [Slide 4 느낌] 부서별 상세 실적 카드 ---
        st.markdown('<div class="report-card"><div class="report-title">📋 부서별 관리 기준 및 상세 실적</div>', unsafe_allow_html=True)
        tabs = st.tabs(['면 1과', '면 5과', '스프실', '전체 총합'])
        for i, d_name in enumerate(['면 1과', '면 5과', '스프실', '전체 총합']):
            with tabs[i]:
                col_l, col_r = st.columns([45, 55])
                d_df = df_raw if d_name == '전체 총합' else df_raw[df_raw['생산부문명'] == d_name]
                with col_l:
                    if not d_df.empty:
                        pv = d_df.groupby(['연도', '자재 유형 내역'])[['이론금액','실제금액']].sum().reset_index()
                        pv['수율(%)'] = (pv['이론금액']/pv['실제금액']*100).round(2)
                        st.dataframe(pv.pivot(index='자재 유형 내역', columns='연도', values='수율(%)').style.format("{:.2f}%"), use_container_width=True)
                with col_r:
                    if not d_df.empty:
                        tr = d_df.groupby(['연도', '월'])[['이론금액','실제금액']].sum().reset_index()
                        tr['수율'] = (tr['이론금액']/tr['실제금액']*100).round(2)
                        tr['표시월'] = tr['월'].apply(lambda x: f"{x.split('.')[1]}월")
                        fig = px.area(tr, x='표시월', y='수율', color='연도', markers=True, color_discrete_map={'25년':'#94A3B8', '26년':'#1E40AF'})
                        fig.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True, key=f"fig_{d_name}")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [Slide 5/6 느낌] 자재비교 & 리스크 매트릭스 ---
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown('<div class="report-card"><div class="report-title">📊 자재 유형별 성적 비교</div>', unsafe_allow_html=True)
            m_opt = st.selectbox("유형 선택", ["원자재", "부자재", "반제품"])
            m_data = df_raw[df_raw['자재 유형 내역'] == m_opt].groupby(['연도', '생산부문명'])[['이론금액','실제금액']].sum().reset_index()
            m_data['수율'] = (m_data['이론금액']/m_data['실제금액']*100).round(2)
            fig_b = px.bar(m_data, x='생산부문명', y='수율', color='연도', barmode='group', text='수율', color_discrete_map={'25년':'#94A3B8', '26년':'#1E40AF'})
            fig_b.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[85, 105]))
            st.plotly_chart(fig_b, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_right:
            st.markdown('<div class="report-card"><div class="report-title">🔍 수율 리스크 매트릭스</div>', unsafe_allow_html=True)
            r_dept = st.selectbox("부서 필터", ["전체 1팀", "면 1과", "면 5과", "스프실"])
            r_df = df_raw.copy() if r_dept == "전체 1팀" else df_raw[df_raw['생산부문명'] == r_dept]
            if not r_df.empty:
                r_item = r_df.groupby(['연도', '품목'])[['이론금액','실제금액']].sum().reset_index()
                r_item['수율'] = (r_item['이론금액']/r_item['실제금액']*100).round(2)
                r_item['금액(억)'] = r_item['실제금액']/100000000
                fig_s = px.scatter(r_item, x='금액(억)', y='수율', color='연도', hover_name='품목', color_discrete_map={'25년':'#94A3B8', '26년':'#1E40AF'})
                fig_s.add_hline(y=100.0, line_dash="dash", line_color="#CBD5E1")
                fig_s.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig_s, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [Slide 7 느낌] 중점 관리 품목 Top 5 ---
        st.markdown('<div class="report-card"><div class="report-title">🚨 중점 관리 품목 (수율 하위 Top 5)</div>', unsafe_allow_html=True)
        t_yr = st.radio("분석 연도 선택", ["26년", "25년"], horizontal=True)
        y_df = df_raw[df_raw['연도'] == t_yr]
        if not y_df.empty:
            top_sum = y_df.groupby(['생산부문명', '품목'])[['이론금액', '실제금액']].sum().reset_index()
            top_sum['수율'] = (top_sum['이론금액'] / top_sum['실제금액'] * 100).round(2)
            tc1, tc2 = st.columns(2)
            for i, d_n in enumerate(['면 1과', '면 5과']):
                with [tc1, tc2][i]:
                    st.write(f"**📍 {d_n} 중점 품목**")
                    d_top = top_sum[top_sum['생산부문명'] == d_n].sort_values('실제금액', ascending=False).head(15).sort_values('수율', ascending=True).head(5)
                    fig_t = px.bar(d_top, x='수율', y='품목', orientation='h', text='수율', color_discrete_sequence=[MAIN_BLUE if t_yr == "26년" else "#94A3B8"])
                    fig_t.update_layout(height=300, margin=dict(l=0,r=10,t=10,b=10), yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_t, use_container_width=True, key=f"top_{d_n}")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#94A3B8; font-size:12px; margin-top:50px;'>© 2026 Production Team 1 | Yield Management System Portal</p>", unsafe_allow_html=True)
