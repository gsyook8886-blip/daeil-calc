import streamlit as st

# 1. 페이지 레이아웃 및 스타일 설정
st.set_page_config(page_title="(주)대일물류 화물 운임 산출 시스템", layout="wide")

# 가독성을 극대화한 커스텀 CSS 적용
st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #6B7280; margin-bottom: 25px; }
    .metric-container { background-color: #F3F4F6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #1E3A8A; }
    .metric-label { font-size: 13px; color: #4B5563; font-weight: 500; }
    .metric-value { font-size: 24px; font-weight: bold; color: #111827; }
    .highlight-value { color: #2563EB; }
    .margin-value { color: #059669; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚚 (주)대일물류 화물 운임 산출 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">정산 규칙 설정 및 실시간 마진 컨트롤러 버전</div>', unsafe_allow_html=True)

# 보안 비밀번호 확인
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    with st.form("login_form"):
        password = st.text_input("보안 비밀번호를 입력하세요:", type="password")
        submit_btn = st.form_submit_button("시스템 인증")
        if submit_btn:
            if password == "8886":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# 2. 데이터 매트릭스 정의
TON_PARAMS = {
    "1톤": {"fixed": 40000, "cost_a": 800, "cost_b": 300},
    "1.4톤": {"fixed": 47000, "cost_a": 800, "cost_b": 300},
    "2.5톤": {"fixed": 62000, "cost_a": 800, "cost_b": 300},
    "3.5톤": {"fixed": 72000, "cost_a": 800, "cost_b": 300},
    "3.5톤 광폭": {"fixed": 77000, "cost_a": 800, "cost_b": 300},
    "5톤": {"fixed": 86500, "cost_a": 1050, "cost_b": 550},
    "5톤 플러스": {"fixed": 90000, "cost_a": 1050, "cost_b": 550},
    "5톤 장축": {"fixed": 95000, "cost_a": 1050, "cost_b": 550},
    "8톤": {"fixed": 105000, "cost_a": 1200, "cost_b": 600},
    "11톤": {"fixed": 133000, "cost_a": 1200, "cost_b": 600},
    "11톤 장축": {"fixed": 145000, "cost_a": 1200, "cost_b": 600},
    "14톤": {"fixed": 140000, "cost_a": 1200, "cost_b": 600},
    "18톤": {"fixed": 150000, "cost_a": 1300, "cost_b": 650},
    "25톤": {"fixed": 164000, "cost_a": 1600, "cost_b": 700},
}

REGION_COMPENSATION = {
    "0% 지역 (서울, 인천, 부천, 안산, 시흥, 화성, 평택, 용인, 이천, 안성, 부산, 울산)": 0.00,
    "3% 지역 (수원, 대전, 대구, 남양주, 파주, 김포, 광주, 양주, 포천, 천안, 아산, 당진, 서산, 청주, 진천, 음성, 구미, 경산, 창원, 김해, 양산, 군산)": 0.03,
    "5% 지역 (춘천, 원주, 강릉, 공주, 논산, 보령, 충주, 제천, 전주, 익산, 완주, 목포, 순천, 광양, 여수, 안동, 영주, 상주, 진주, 통영, 거제)": 0.05,
    "10% 지역 (태백, 정선, 평창, 인제, 양구, 화천, 고성, 완도, 진도, 신안, 봉화, 영양, 청송, 울진)": 0.10,
}

# 3. 2단 레이아웃 분할
col_l, col_r = st.columns([1.1, 0.9], gap="large")

with col_l:
    # ⚙️ 글로벌 환경 설정 섹션 (할증률 및 마진 수동 설정)
    st.markdown("### ⚙️ 시스템 마진 및 요율 설정")
    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
    with cfg_col1:
        reg_margin = st.number_input("기본 마진율 (%)", min_value=0, max_value=100, value=20, step=1)
    with cfg_col2:
        reg_ref_rate = st.number_input("냉장/동 가산 요율 (배)", min_value=1.00, max_value=3.00, value=1.55, step=0.05)
    with cfg_col3:
        reg_weather_rate = st.number_input("기상 할증 요율 (%)", min_value=0, max_value=100, value=20, step=5)
    
    st.write("---")
    
    st.markdown("### 📋 화물 운송 조건 입력")
    
    # 연산 방식 선택 라디오 버튼 (기사 고정 방식 index=1로 기본값 세팅)
    calc_mode = st.radio(
        "⚖️ 연산 방식 선택",
        ["화주 고정 방식 (청구 총액 기준 역산)", "기사 고정 방식 (기사 원가 기준 순산)"],
        index=1,
        horizontal=True
    )
    
    # 2열 조건 입력 구조
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        tonnage = st.selectbox("차량 톤수", list(TON_PARAMS.keys()))
        distance = st.number_input("운송 거리 (km)", min_value=0.0, value=50.0, step=1.0)
    
    with sub_col2:
        region = st.selectbox("도착지 (공차 보정)", list(REGION_COMPENSATION.keys()))
        actual_cost = st.number_input("기타 실비 (톨비/대기료 등)", min_value=0, value=0, step=1000)
        
        st.write("**추가 할증 활성화**")
        is_refrigerated = st.checkbox("냉장/동 가산 적용")
        is_bad_weather = st.checkbox("기상 악화 (비/눈) 적용")

# 4. 연산 엔진 부분 (등록한 요율 연동)
params = TON_PARAMS[tonnage]
fixed_fee = params["fixed"]
cost_a = params["cost_a"]
cost_b = params["cost_b"]

# 거리별 기본 요금
if distance <= 100:
    base_fee = fixed_fee + (distance * cost_a)
else:
    base_fee = fixed_fee + (100 * cost_a) + ((distance - 100) * cost_b)
    
# 화면에서 수동 등록한 냉장/동 요율 반영
if is_refrigerated:
    base_fee *= reg_ref_rate
    
# 화면에서 수동 등록한 기상 할증 요율 및 지역 보정율 반영
comp_rate = REGION_COMPENSATION[region]
weather_rate = (reg_weather_rate / 100.0) if is_bad_weather else 0.00
extra_fee = base_fee * (comp_rate + weather_rate)

# 실비 제외 순수 총 운임
pure_total_fee = base_fee + extra_fee
margin_pct = reg_margin / 100.0

# 모드별 수식 분기
if "화주 고정" in calc_mode:
    shipper_pure = pure_total_fee
    shipper_total = shipper_pure + actual_cost
    driver_pure = shipper_pure * (1 - margin_pct)
    driver_total = driver_pure + actual_cost
    margin_amount = shipper_pure - driver_pure
else:
    driver_pure = pure_total_fee
    driver_total = driver_pure + actual_cost
    if margin_pct < 1.0:
        shipper_pure = driver_pure / (1 - margin_pct)
    else:
        shipper_pure = driver_pure
    shipper_total = shipper_pure + actual_cost
    margin_amount = shipper_pure - driver_pure

with col_r:
    st.markdown("### 💵 실시간 정산 결과")
    
    # 커스텀 카드형 메트릭 박스 출력
    st.markdown(f"""
        <div class="metric-container" style="border-left-color: #2563EB;">
            <div class="metric-label">💰 최종 화주 청구 총액 (실비 포함)</div>
            <div class="metric-value highlight-value">{int(shipper_total):,} 원</div>
        </div>
        <div class="metric-container" style="border-left-color: #4B5563;">
            <div class="metric-label">👨‍✈️ 최종 차주 지급 운임 (실비 포함)</div>
            <div class="metric-value">{int(driver_total):,} 원</div>
        </div>
        <div class="metric-container" style="border-left-color: #059669;">
            <div class="metric-label">📈 대일물류 확보 마진 ({reg_margin}%)</div>
            <div class="metric-value margin-value">{int(margin_amount):,} 원</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 상세 요율 내역 투명 노출
    with st.expander("🔍 상세 요율 구성 내역", expanded=True):
        st.write(f"• **톤수별 기본 고정료 (Fixed):** {fixed_fee:,} 원")
        st.write(f"• **거리 정산 운임 (기본):** {int(base_fee / reg_ref_rate if is_refrigerated else base_fee):,} 원")
        if is_refrigerated:
            st.write(f"• **냉장/동 가산 적용액 ({reg_ref_rate}배):** {int(base_fee):,} 원")
        st.write(f"• **공차 보정 ({int(comp_rate*100)}%) + 기상 할증 ({int(weather_rate*100)}%):** {int(extra_fee):,} 원")
        st.write(f"• **증빙 청구 실비:** {actual_cost:,} 원")
        st.info(f"💡 현재 시스템은 **기사 고정 방식**을 기본 운용 모드로 켜고 있습니다.")
