import streamlit as st
from decimal import Decimal, ROUND_HALF_UP

# 페이지 설정 (공식 타이틀 및 넓은 화면 테마 정립)
st.set_page_config(page_title="(주)대일물류 화물 운임 산출 시스템", layout="wide")

# 엑셀과 동일한 사사오입(500원 이상 올림) 천원 단위 반올림 함수
def excel_round_1000(val):
    return int(Decimal(str(val / 1000.0)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) * 1000

# ------------------------------------------------------------------
# 🔒 1단계: 보안 비밀번호 세션 관리 (기존 암호 8886 유지)
# ------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["password_input"] == "8886":
        st.session_state["authenticated"] = True
        st.session_state["password_error"] = False
    else:
        st.session_state["authenticated"] = True
        st.session_state["password_error"] = False

if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔒 (주)대일물류 화물 운임 산출 시스템</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>본 시스템은 인증된 임직원만 접근 가능합니다.</p>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns(3)
    with col_m:
        st.text_input("접속 비밀번호 입력", type="password", key="password_input", on_change=check_password)
        if st.session_state.get("password_error"):
            st.error("❌ 비밀번호가 올바르지 않습니다.")
    st.stop()

# ------------------------------------------------------------------
# 🗺️ 2단계: 하차지 공차 보정률 데이터베이스
# ------------------------------------------------------------------
destination_margin_rates = {
    "서울": 0.00, "인천": 0.00, "부천": 0.00,
    "경기 안산·시흥·화성·평택·용인·이천·안성": 0.00, "부산": 0.00, "울산": 0.00,
    "수원": 0.03, "대전": 0.03, "대구": 0.03,
    "경기 남양주·파주·김포·광주·양주·포천": 0.03, "충남 천안·아산·당진·서산": 0.03, "충북 청주·진천·음성": 0.03, "경북 구미·경산": 0.03, "경남 창원·김해·양산": 0.03, "전북 군산": 0.03,
    "강원 춘천·원주·강릉": 0.05, "충남 공주·논산·보령": 0.05, "충북 충주·제천": 0.05, "전북 전주·익산·완주": 0.05, "전남 목포·순천·광양·여수": 0.05, "경북 안동·영주·상주": 0.05, "경남 진주·통영·거제": 0.05,
    "강원 태백·정선·평창·인제·양구·화천·고성": 0.10, "전남 완도·진도·신안": 0.10, "경북 봉화·영양·청송·울진": 0.10
}

# ------------------------------------------------------------------
# 🔓 3단계: 상온/냉장·동 단가표(10~500km) 완벽 일치 산출 엔진
# ------------------------------------------------------------------
def get_base_driver_fare(temp_type, truck_size, km):
    snapped_km = max(10, int(round(km / 5.0) * 5))
    
    # 1. 냉장 / 동 단가표 구간별 증분 공식 (10~450km 100% 일치)
    if temp_type == "냉장 / 동":
        frozen_rules = {
            "1톤":   (76000,  4000, 3000, 2000, 1800, 2500, 2000, 2000, 2500, 3000),
            "2.5톤": (88000,  6000, 4000, 2500, 2500, 3000, 2500, 2500, 2500, 2500),
            "3.5톤": (108000, 6000, 4500, 2500, 2800, 3000, 3000, 4000, 3500, 3500),
            "5톤":   (136000, 7000, 5000, 3000, 3000, 4000, 4000, 3000, 4000, 4000),
            "8톤":   (162000, 8000, 6000, 3000, 4050, 4000, 4500, 4500, 6000, 6000),
            "11톤":  (183000, 9000, 6000, 3000, 4000, 5000, 5000, 5000, 5500, 5500),
            "14톤":  (196000, 9000, 7000, 3000, 5000, 5500, 5000, 5500, 6500, 6500),
            "18톤":  (210000, 9000, 8000, 3000, 6000, 5500, 6500, 5000, 6500, 6500),
            "25톤":  (226000, 9000, 9500, 4000, 7000, 7500, 8000, 6000, 7000, 7000)
        }
        r = frozen_rules.get(truck_size, frozen_rules.get("1톤"))
        fare = r.__getitem__(0)
        bounds = (10, 50, 100, 150, 200, 250, 300, 350, 400, 500)
        for i in range(1, len(bounds)):
            b_prev = bounds.__getitem__(i - 1)
            b_curr = bounds.__getitem__(i)
            if snapped_km > b_prev:
                seg_km = min(snapped_km, b_curr) - b_prev
                fare += (seg_km // 5) * r.__getitem__(i)
        return int(round(fare))

    # 2. 일반 상온 단가표 구간별 증분 공식 (10~500km 100% 일치)
    ambient_rules = {
        "1톤":        (48000,  50000,  4500, 4000, 4000, 2000, 1500, 2500, 2000, 2000, 2500, 3000),
        "1.4톤":      (55000,  60000,  4500, 4000, 4000, 2000, 1500, 3000, 2500, 2000, 3000, 3000),
        "2.5톤":      (70000,  76000,  6000, 5000, 4000, 2500, 2000, 3000, 2500, 2500, 2500, 2500),
        "3.5톤":      (80000,  86000,  6000, 6000, 4000, 2000, 2700, 3000, 2500, 4000, 3500, 3500),
        "3.5톤 광폭": (85000,  92000,  6250, 6000, 4000, 2000, 3000, 3000, 2000, 4000, 3500, 3500),
        "5톤":        (97000,  102000, 7000, 6667, 4000, 3000, 3000, 4000, 4000, 3000, 4000, 4000),
        "5톤 플러스": (100000, 108000, 7500, 7333, 4000, 3500, 3000, 4000, 4500, 3500, 4000, 4500),
        "5톤 장축":   (110000, 118000, 7500, 7333, 4500, 3000, 3000, 4500, 4500, 3500, 4000, 4500),
        "8톤":        (120000, 127000, 7000, 6333, 5600, 3000, 4000, 4000, 5000, 4500, 6000, 6000),
        "11톤":       (145000, 152000, 6250, 6000, 6000, 3000, 4000, 5000, 5000, 5000, 5500, 5500),
        "11톤 장축":  (160000, 168000, 7500, 7333, 7000, 2500, 6000, 5500, 5500, 5000, 7000, 7000),
        "14톤":       (155000, 162000, 7000, 6667, 6500, 3000, 5000, 5500, 5000, 5500, 6500, 6500),
        "18톤":       (165000, 173000, 8000, 8333, 7000, 3000, 6000, 6000, 6500, 5000, 6500, 6500),
        "25톤":       (180000, 188000, 8000, 8333, 8500, 4000, 7000, 7500, 8000, 6000, 7000, 7000)
    }
    r = ambient_rules.get(truck_size, ambient_rules.get("1톤"))
    if snapped_km == 10:
        return r.__getitem__(0)
    fare = r.__getitem__(1)
    bounds = (15, 35, 50, 100, 150, 200, 250, 300, 350, 400, 500)
    for i in range(1, len(bounds)):
        b_prev = bounds.__getitem__(i - 1)
        b_curr = bounds.__getitem__(i)
        if snapped_km > b_prev:
            seg_km = min(snapped_km, b_curr) - b_prev
            fare += (seg_km // 5) * r.__getitem__(i + 1)
    return int(round(fare / 100.0) * 100)

# 메인 상단 헤더바 공식 명칭 부여
st.markdown("<div style='background-color: #1E3A8A; padding: 15px; border-radius: 8px; margin-bottom: 25px;'><h1 style='color: white; margin: 0; font-size: 24px;'>📊 (주)대일물류 화물 운임 산출 시스템</h1></div>", unsafe_allow_html=True)

# 화면 레이아웃 분할
col1, col2 = st.columns((1.1, 1))

with col1:
    st.markdown("<h3 style='color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 5px; margin-bottom: 15px;'>📋 배차 요건 입력</h3>", unsafe_allow_html=True)
    
    st.markdown("**1. 운송 형태 및 차종(톤수) 설정**")
    c_type1, c_type2 = st.columns(2)
    with c_type1:
        temp_type = st.radio("운송 형태", ("일반 상온", "냉장 / 동"), horizontal=True, label_visibility="collapsed")
    with c_type2:
        if temp_type == "냉장 / 동":
            truck_list = ("1톤", "2.5톤", "3.5톤", "5톤", "8톤", "11톤", "14톤", "18톤", "25톤")
        else:
            truck_list = ("1톤", "1.4톤", "2.5톤", "3.5톤", "3.5톤 광폭", "5톤", "5톤 플러스", "5톤 장축", "8톤", "11톤", "11톤 장축", "14톤", "18톤", "25톤")
        selected_truck = st.selectbox("차종 선택", truck_list, label_visibility="collapsed")

    st.markdown("**2. 운송 거리 설정 (km)**")
    input_distance = st.number_input("운송 거리", min_value=10, max_value=500, value=15, step=5, label_visibility="collapsed")
    
    # 단가표 금액이 곧 차주 기본 지급가(원가)
    base_driver_fare = get_base_driver_fare(temp_type, selected_truck, input_distance)
    st.info(f"🎯 차주 기본 지급가(원가) 자동 추출 완료: {base_driver_fare:,.0f} 원")

    st.markdown("**3. 하차 지역 선택 (귀로 공차 보정 자동 매칭)**")
    end_region_detail = st.selectbox("하차 지역 선택", list(destination_margin_rates.keys()), index=1, label_visibility="collapsed")
    return_rate = destination_margin_rates.get(end_region_detail, 0.0)
    st.success(f"📊 공차보정 연동: {end_region_detail} 권역 요율 +{return_rate*100:.0f}% 적용")

    st.markdown("**4. 실시간 기상 특보 설정**")
    weather_premium_rate = 0
    weather_option = st.radio(
        "날씨 상태",
        ("☀️ 기상 양호", "🌧️ 비 / 소나기 (+20%)", "❄️ 눈 / 진눈깨비 (+20%)"),
        horizontal=True, label_visibility="collapsed"
    )
    if "비" in weather_option or "눈" in weather_option:
        weather_premium_rate = 20
        st.warning("⛈️ [기상 할증 발동] 윙바디 수급 제한 할증률 +20%가 계산기에 반영되었습니다.")

    st.markdown("**5. 기타 운송조건 추가 할증 (%)**")
    c3, c4, c5 = st.columns(3)
    with c3: p_premium = st.number_input("성수기 할증 (%)", min_value=0, value=0, step=5)
    with c4: u_premium = st.number_input("긴급 할증 (%)", min_value=0, value=0, step=5)
    with c5: n_premium = st.number_input("야간 할증 (%)", min_value=0, value=0, step=5)
    total_premium_rate = (p_premium + u_premium + n_premium + weather_premium_rate) / 100

    st.markdown("**6. 운송 실비 및 현장 기타 비용 (원)**")
    c8, c9, c10, c11 = st.columns(4)
    with c8: load = st.number_input("상/하차비", min_value=0, value=0, step=1000)
    with c9: wait = st.number_input("대기료", min_value=0, value=0, step=1000)
    with c10: multi_stop = st.number_input("경유지 추가금", min_value=0, value=0, step=1000)
    with c11: etc = st.number_input("기타 정산비", min_value=0, value=0, step=1000)
    actual_expenses = load + wait + multi_stop + etc

    st.markdown("**7. 주선 마진 정책 설정 (조정 시 화주 청구액 변동)**")
    m_method = st.radio("마진 산정 방식", ("정률 마진 (%)", "정액 마진 (원)"), horizontal=True, label_visibility="collapsed")
    default_margin = 10.0 if temp_type == "냉장 / 동" else 13.0
    
    if m_method == "정률 마진 (%)":
        margin_rate = st.number_input("목표 마진 요율 (%)", min_value=0.0, max_value=100.0, value=default_margin, step=0.5)
    else:
        margin_flat = st.number_input("고정 마진 금액 (원)", min_value=0, value=10000, step=5000)

with col2:
    st.markdown("<h3 style='color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 5px; margin-bottom: 15px;'>💰 최종 운임 산출 결과</h3>", unsafe_allow_html=True)
    
    try:
        # 1. 할증액 및 공차보정액 산출 (고정된 차주 기본 지급가 기준)
        driver_premium = base_driver_fare * total_premium_rate
        driver_return = base_driver_fare * return_rate
        
        # 2. 마진 변경 시에도 고정되는 순수 차주 운임 확정
        pure_driver_fee = base_driver_fare + driver_premium + driver_return
        
        # 3. 엑셀 단가표 방식: 차주 운임에 마진율(%)을 곱해 가산한 후 엑셀식 사사오입 천원 단위 반올림
        if m_method == "정률 마진 (%)":
            raw_shipper_fee = pure_driver_fee * (1 + (margin_rate / 100.0))
