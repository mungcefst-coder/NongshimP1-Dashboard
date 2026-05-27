# ... (앞부분 전역 설정 및 로그인 로직은 동일) ...

else:
    with st.sidebar:
        if st.session_state['is_admin']:
            st.markdown("<span style='background-color:#EF4444; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;'>MASTER ADMIN</span>", unsafe_allow_html=True)
            
            # ------------------------------------------------------------------
            # 🔥 [이 부분이 추가되는 관리자 전용 가구입니다!]
            # ------------------------------------------------------------------
            st.markdown("### 🎯 관리자 전용: 목표 수율 설정")
            st.caption("여기서 바꾼 기준치가 대시보드 상황판에 실시간 반영됩니다.")
            
            # 기존 고정값(98.92 등) 대신 관리자가 화면에서 조절할 수 있는 입력창 배치
            adm_m1 = st.number_input("면 1과 목표 (%)", value=98.92, step=0.01)
            adm_m5 = st.number_input("면 5과 목표 (%)", value=97.93, step=0.01)
            adm_sp = st.number_input("스프실 목표 (%)", value=99.53, step=0.01)
            adm_tot = st.number_input("전체 총합 목표 (%)", value=98.73, step=0.01)
            
            # 관리자가 입력한 값으로 변수 덮어쓰기
            YIELD_THRESHOLD = {
                '면 1과': adm_m1, 
                '면 5과': adm_m5, 
                '스프실': adm_sp, 
                '전체 총합': adm_tot
            }
            st.markdown("---")
        else:
            st.markdown("<span style='background-color:#3B82F6; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;'>TEAM MEMBER</span>", unsafe_allow_html=True)
            # 일반 팀원은 소스코드에 박힌 고정 기준치 사용
            YIELD_THRESHOLD = {'면 1과': 98.92, '면 5과': 97.93, '스프실': 99.53, '전체 총합': 98.73}

        st.header("⚙️ SYSTEM ADMIN")
        # ... (이하 동일) ...
