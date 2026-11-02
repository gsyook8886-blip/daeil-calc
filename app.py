import streamlit as st

# 1. 기본 정보 설정
st.set_page_config(page_title="(주)대일물류 화물 운임 산출 시스템", layout="wide")
st.title("🚚 (주)대일물류 화물 운임 산출 시스템")

# 보안 비밀번호 확인 (간이 인증)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    password = st.text_input("보안 비밀번호를 입력하세요:", type="password")
    if st.button("인증하기"):
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
    "0% 지역 (서울/인천/경기 주요/부산/울산 등)": 0.00,
    "3% 지역 (수원/대전/대구/경기·충청·경북·전북 일부 등)": 0.03,
    "5% 지역 (강원/전주/목포/순천/여수/안동/진주 등)": 0.05,
    "10% 지역 (강원 산간/전남 도서/경북 오지 등)": 0.10,
}

# 3. 레이아웃 분할 (입력과 결과 반반 구성)
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("📋 화물 정보 및 조건 입력")
    
    # 정산 방식 선택 라디오 버튼 (핵심 요청 기능)
    calc_mode = st.radio(
        "⚖️ 정산 기준 방식 선택",
        ["화주 고정 방식 (최종 청구액 기준 역산)", "기사 고정 방식 (기사 원가 기준 순산)"],
        help="화주 고정은 청구액에서 마진을 빼서 기사료를 구하고, 기사 고정은 기사료에 마진을 더해 청구액을 구합니다."
    )
    
    tonnage = st.selectbox("차량 톤수 선택", list(TON_PARAMS.keys()))
    is_refrigerated = st.checkbox("냉장/동 선택 (상온 운임의 1.55배)")
    distance = st.number_input("운송 거리 (km)", min_value=0.0, value=50.0, step=1.0)
    region = st.selectbox("도착지 귀로 공차 보정율 지역 선택", list(REGION_COMPENSATION.keys()))
    is_bad_weather = st.checkbox("기상 악화 (비/눈 선택 시 요율 기반 +20% 할증)")
    actual_cost = st.number_input("기타 실비 (톨비, 대기료 등 경비 직접 입력)", min_value=0, value=0, step=1000)
    margin_rate = st.slider("설정 마진율 (%)", min_value=0, max_value=100, value=20, step=1)

with col_r:
    st.subheader("💵 운임 산출 결과")
    
    # 4. 단계별 계산 처리
    params = TON_PARAMS[tonnage]
    fixed_fee = params["fixed"]
    cost_a = params["cost_a"]
    cost_b = params["cost_b"]
    
    # [1단계] 기본 거리 운임 계산
    if distance <= 100:
        base_fee = fixed_fee + (distance * cost_a)
    else:
        base_fee = fixed_fee + (100 * cost_a) + ((distance - 100) * cost_b)
        
    # [2단계] 냉장/동 가산
    if is_refrigerated:
        base_fee *= 1.55
        
    # [3단계] 귀로 공차 보정 및 기상 할증 비율 합산
    comp_rate = REGION_COMPENSATION[region]
    weather_rate = 0.20 if is_bad_weather else 0.00
    
    # 할증 및 보정액 산출 (기본 거리 운임 기반)
    extra_fee = base_fee * (comp_rate + weather_rate)
    
    # 실비를 제외한 순수 운임 합계 (마진 적용의 대상이 되는 금액)
    pure_total_fee = base_fee + extra_fee
    
    # [4단계] 정산 모드별 최종 마진 처리
    margin_pct = margin_rate / 100.0
    
    if "화주 고정 방식" in calc_mode:
        # 화주 청구 총액을 먼저 확정하고 마진을 제외하여 기사 지급액 산출
        shipper_pure = pure_total_fee
        shipper_total = shipper_pure + actual_cost
        
        driver_pure = shipper_pure * (1 - margin_pct)
        driver_total = driver_pure + actual_cost
        margin_amount = shipper_pure - driver_pure
    else:
        # 기사 지급액(원가)을 고정하고 마진을 붙여서 화주 청구 총액 산출
        driver_pure = pure_total_fee
        driver_total = driver_pure + actual_cost
        
        # 엑셀 방식 마진 가산 (원가 / (1 - 마진율) 방식 적용)
        if margin_pct < 1.0:
            shipper_pure = driver_pure / (1 - margin_pct)
        else:
            shipper_pure = driver_pure
            
        shipper_total = shipper_pure + actual_cost
        margin_amount = shipper_pure - driver_pure

    # 결과 화면 출력
    st.info(f"선택된 모드: **{calc_mode}**")
    
    # 주요 금액 대형 대시보드
    st.metric(label="💰 최종 화주 청구 총액 (실비 포함)", value=f"{int(shipper_total):,} 원")
    st.metric(label="👨‍✈️ 최종 차주 지급 운임 (실비 포함)", value=f"{int(driver_total):,} 원")
    st.metric(label="📈 대일물류 확보 마진액", value=f"{int(margin_amount):,} 원")
    
    with st.expander("🔍 상세 산출 내역 보기"):
        st.write(f"- **선택 톤수 기본료 (Fixed):** {fixed_fee:,} 원")
        st.write(f"- **거리별 운송 요금 (상온 기준):** {int(base_fee / 1.55 if is_refrigerated else base_fee):,} 원")
        if is_refrigerated:
            st.write(f"- **냉장/동 가산 후 운임 (+55%):** {int(base_fee):,} 원")
        st.write(f"- **지역 공차 보정액 ({comp_rate*100}%):** {int(base_fee * comp_rate):,} 원")
        st.write(f"- **기상 할증액 ({weather_rate*100}%):** {int(base_fee * weather_rate):,} 원")
        st.write(f"- **기타 입력 실비 (경비):** {actual_cost:,} 원")
        st.write(f"- **순수 운임 합계 (실비 제외):** {int(pure_total_fee):,} 원")
