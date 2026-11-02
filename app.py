import streamlit as st

# 1. 페이지 레이아웃 및 직전 최종 디자인 CSS 복원
st.set_page_config(page_title="(주)대일물류 화물 운임 산출 시스템", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #6B7280; margin-bottom: 25px; }
    .metric-container { background-color: #F8FAFC; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 6px solid #1E3A8A; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-label { font-size: 14px; color: #475569; font-weight: 600; margin-bottom: 8px; }
    .metric-value { font-size: 28px; font-weight: bold; color: #0F172A; }
    .highlight-value { color: #2563EB; }
    .margin-value { color: #16A34A; }
    .section-title { font-size: 18px; font-weight: bold; color: #334155; margin-top: 10px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚚 (주)대일물류 화물 운임 산출 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">최종 디자인 및 옵션 패널 통합 버전 (기사고정 순산 방식 기본)</div>', unsafe_allow_html=True)

# 보안 비밀번호 확인 (8886)
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

# 3. 좌우 분할 구조 (10월 30일 최종 스타일 배치)
col_l, col_r = st.columns([1.1, 0.9], gap="large")

with col_l:
    st.markdown('<div class="section-title">📋 기본 정보 및 특수 조건 등록</div>', unsafe_allow_html=True)
    
    # 상단 정산 모드 선택 (기사 고정이 기본값)
    calc_mode = st.radio(
        "⚖️ 정산 연산 방식 선택",
        ["기사 고정 방식 (기사료 기준 ➡️ 마진율 변경 시 화주금액 변동)", "화주 고정 방식 (화주금액 기준 ➡️ 마진율 변경 시 기사료 변동)"],
        index=0,  # 기사 고정 방식을 기본값으로 세팅
        horizontal=True
    )
    
    st.write("")
    
    # 이전 최종본의 입력창 분할 구조
    in_col1, in_col2 = st.columns(2)
    with in_col1:
        tonnage = st.selectbox("🚛 차량 톤수", list(TON_PARAMS.keys()))
        distance = st.number_input("📍 운송 거리 (km)", min_value=0.0, value=50.0, step=1.0)
        margin_rate = st.slider("📈 설정 마진율 (%)", min_value=0, max_value=100, value=20, step=1)
        
    with in_col2:
        region = st.selectbox("🗺️ 도착지 (공차 보정율 자동 매칭)", list(REGION_COMPENSATION.keys()))
        actual_cost = st.number_input("💵 기타 실비 (통행료/대기료 등 직접 입력)", min_value=0, value=0, step=1000)
        
        st.markdown("**🛠️ 할증/옵션 추가 등록**")
        is_refrigerated = st.checkbox("❄️ 냉장/동 차량 선택 (상온의 1.55배 가산)")
        is_bad_weather = st.checkbox("🌧️ 기상 악화 할증 적용 (비/눈 발생시 +20% 가산)")

# 4. 연산 엔진 (인수인계 규칙 적용)
params = TON_PARAMS[tonnage]
fixed_fee = params["fixed"]
cost_a = params["cost_a"]
cost_b = params["cost_b"]

# 거리별 운임 계산
if distance <= 100:
    base_fee = fixed_fee + (distance * cost_a)
else:
    base_fee = fixed_fee + (100 * cost_a) + ((distance - 100) * cost_b)
    
# 냉장/냉동 옵션 가산
if is_refrigerated:
    base_fee *= 1.55
    
# 공차 보정 및 기상 할증 요율 계산
comp_rate = REGION_COMPENSATION[region]
weather_rate = 0.20 if is_bad_weather else 0.00
extra_fee = base_fee * (comp_rate + weather_rate)

# 실비를 제외한 순수 요율 운임 합계
pure_total_fee = base_fee + extra_fee
margin_pct = margin_rate / 100.0

# 5. 핵심: 사장님 요청에 따른 모드별 운임 산출 흐름 분기
if "기사 고정" in calc_mode:
    # [기사 고정 방식 - 엑셀 스타일] 
    # 연산 요율 합계가 기사님의 확정 순수 운임(원가)이 됩니다.
    driver_pure = pure_total_fee
    driver_total = driver_pure + actual_cost
    
    # 마진율을 올리면 기사료는 가만히 있고 화주 청구금액이 위로 올라갑니다.
    if margin_pct < 1.0:
        shipper_pure = driver_pure / (1 - margin_pct)
    else:
        shipper_pure = driver_pure
        
    shipper_total = shipper_pure + actual_cost
    margin_amount = shipper_pure - driver_pure
else:
    # [화주 고정 방식 - 인수인계서 원본 스타일]
    # 연산 요율 합계가 화주의 확정 순수 청구액이 됩니다.
    shipper_pure = pure_total_fee
    shipper_total = shipper_pure + actual_cost
    
    # 마진율을 올리면 화주 금액은 가만히 있고 기사료가 깎여 내려갑니다.
    driver_pure = shipper_pure * (1 - margin_pct)
    driver_total = driver_pure + actual_cost
    margin_amount = shipper_pure - driver_pure

# 오른쪽 결과 대시보드 화면 출력 (최종 디자인 스타일)
with col_r:
    st.markdown('<div class="section-title">💵 실시간 정산 결과 대시보드</div>', unsafe_allow_html=True)
    
    # 가독성 높은 3단 카드 레이아웃
    st.markdown(f"""
        <div class="metric-container" style="border-left-color: #2563EB;">
            <div class="metric-label">💰 최종 화주 청구 총액 (실비 포함)</div>
            <div class="metric-value highlight-value">{int(shipper_total):,} 원</div>
        </div>
        <div class="metric-container" style="border-left-color: #475569;">
            <div class="metric-label">👨‍✈️ 최종 차주 지급 운임 (실비 포함)</div>
            <div class="metric-value">{int(driver_total):,} 원</div>
        </div>
        <div class="metric-container" style="border-left-color: #16A34A;">
            <div class="metric-label">📈 대일물류 확보 마진액 ({margin_rate}%)</div>
            <div class="metric-value margin-value">{int(margin_amount):,} 원</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 하단 명세서 노출
    with st.expander("🔍 상세 요율 구성 내역", expanded=True):
        st.write(f"• **선택 톤수 기본 요금 (Fixed):** {fixed_fee:,} 원")
        st.write(f"• **거리 정산 운임 (상온 기준):** {int(base_fee / 1.55 if is_refrigerated else base_fee):,} 원")
        if is_refrigerated:
            st.write(f"• **냉장/동 가산 적용액 (+55%):** {int(base_fee):,} 원")
        st.write(f"• **귀로 공차 보정액 ({int(comp_rate*100)}%):** {int(base_fee * comp_rate):,} 원")
        st.write(f"• **기상 악화 할증액 ({int(weather_rate*100)}%):** {int(base_fee * weather_rate):,} 원")
        st.write(f"• **직접 입력 실비 (마진 미적용):** {actual_cost:,} 원")
        
        st.write("---")
        if "기사 고정" in calc_mode:
            st.caption("💡 현재 **기사 고정 모드**입니다. 마진율 슬라이더를 움직이면 **화주 청구 총액**이 실시간으로 계산되어 변동합니다.")
        else:
            st.caption("💡 현재 **화주 고정 모드**입니다. 마진율 슬라이더를 움직이면 화주 금액은 유지되고 **차주 지급 운임**이 변동합니다.")
