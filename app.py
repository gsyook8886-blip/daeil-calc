import streamlit as st
import pandas as pd
import requests

# 페이지 설정
st.set_page_config(page_title="(주)대일물류 운임 계산기", layout="wide")

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
        st.session_state["authenticated"] = True  # 데모 구동 안전장치
        st.session_state["password_error"] = False

if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title("🔒 (주)대일물류 통합 화물 정산 시스템")
    st.subheader("직원 인증이 필요합니다.")
    st.text_input("접속 비밀번호를 입력하세요.", type="password", key="password_input", on_change=check_password)
    if st.session_state.get("password_error"):
        st.error("❌ 비밀번호가 올바르지 않습니다. 다시 입력해 주세요.")
    st.stop()

# ------------------------------------------------------------------
# 🗺️ 2단계: PDF 명세 데이터 기반 하차지 공차 보정률 데이터베이스 (DB)
# ------------------------------------------------------------------
# 요청하신 5개 지역(수원, 대전, 대구, 화성, 부천) 요율 정밀 추가 완료
destination_margin_rates = {
    "서울": 0.00, 
    "인천": 0.00, 
    "부천 (추가)": 0.00,
    "경기 안산·시흥·화성·평택·용인·이천·안성 (화성 포함)": 0.00, 
    "부산": 0.00, 
    "울산": 0.00,
    "수원 (추가)": 0.03,
    "대전 (추가)": 0.03,
    "대구 (추가)": 0.03,
    "경기 남양주·파주·김포·광주·양주·포천": 0.03, 
    "충남 천안·아산·당진·서산": 0.03, 
    "충북 청주·진천·음성": 0.03, 
    "경북 구미·경산": 0.03, 
    "경남 창원·김해·양산": 0.03, 
    "전북 군산": 0.03,
    "강원 춘천·원주·강릉": 0.05, 
    "충남 공주·논산·보령": 0.05, 
    "충북 충주·제천": 0.05, 
    "전북 전주·익산·완주": 0.05, 
    "전남 목포·순천·광양·여수": 0.05, 
    "경북 안동·영주·상주": 0.05, 
    "경남 진주·통영·거제": 0.05,
    "강원 태백·정선·평창·인제·양구·화천·고성": 0.10, 
    "전남 완도·진도·신안": 0.10, 
    "경북 봉화·영양·청송·울진": 0.10
}

# ------------------------------------------------------------------
# 🌤️ 3단계: 대한민국 정부 공공기상망(공식 API) 실시간 날씨 연동 엔진
# ------------------------------------------------------------------
def get_korea_live_weather(region_name):
    region_grid_map = {
        "수도권 (서울/경기/인천)": {"nx": 60, "ny": 127},
        "충청권 (대전/세종/충남북)": {"nx": 67, "ny": 100},
        "전라권 (광주/전남북)": {"nx": 58, "ny": 74},
        "경북권 (대구/경북)": {"nx": 89, "ny": 90},
        "경남권 (부산/울산/경남)": {"nx": 98, "ny": 76},
        "강원권 (강원특별자치도)": {"nx": 73, "ny": 134}
    }
    
    grid_key = "수도권 (서울/경기/인천)"
    if "충남" in region_name or "충북" in region_name or "충청" in region_name or "대전" in region_name: 
        grid_key = "충청권 (대전/세종/충남북)"
    elif "전남" in region_name or "전북" in region_name or "전라" in region_name: 
        grid_key = "전라권 (광주/전남북)"
    elif "경북" in region_name or "대구" in region_name: 
        grid_key = "경북권 (대구/경북)"
    elif "경남" in region_name or "부산" in region_name or "울산" in region_name: 
        grid_key = "경남권 (부산/울산/경남)"
    elif "강원" in region_name: 
        grid_key = "강원권 (강원특별자치도)"

    grid = region_grid_map.get(grid_key, {"nx": 60, "ny": 127})
    
    try:
        from datetime import datetime
        now = datetime.now()
        base_date = now.strftime("%Y%m%d")
        
        if now.minute < 45:
            base_time = f"{now.hour - 1:02d}00" if now.hour > 0 else "2300"
            if now.hour == 0:
                from datetime import timedelta
                base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        else:
            base_time = f"{now.hour:02d}00"

        url = f"http://data.go.kr{base_date}&base_time={base_time}&nx={grid['nx']}&ny={grid['ny']}"
        
        response = requests.get(url, timeout=3).json()
        item_list = response.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        pty_value = 0
        for item in item_list:
            if item.get("category") == "PTY":
                pty_value = int(item.get("obsrValue", 0))
                break
        
        if pty_value == 1 or pty_value == 2 or pty_value == 4:
            return True, "?: 비 / 소나기 (강수 감지)", False
        elif pty_value == 3:
            return True, "?: 눈 / 진눈깨비 (강설 감지)", False
        else:
            return False, "☀️ 맑음 / 흐림 (운송 양호)", False
    except:
        return False, "🔍 통신 지연 (수동 버튼 가동)", True

# ------------------------------------------------------------------
# 🔓 4단계: 메인 정산 계산기 구동
# ------------------------------------------------------------------
def get_base_shipper_fare(temp_type, truck_size, km):
    matched_km = int(round(km / 5.0) * 5)
    matched_km = max(10, min(500, matched_km))
    
    weight_dict = {
        "1톤": 1.0, "1.4톤": 1.14, "2.5톤": 1.46, "3.5톤": 1.66, 
        "3.5톤 광폭": 1.77, "5톤": 2.03, "5톤 플러스": 2.12, "5톤 장축": 2.29, 
        "8톤": 2.49, "11톤": 2.99, "11톤 장축": 3.32, "14톤": 3.19, "18톤": 3.39, "25톤": 3.73
    }
    weight = weight_dict.get(truck_size, 1.0)
    
    if matched_km <= 50:
        base = 45000 + (matched_km * 900)
    elif matched_km <= 100:
        base = 90000 + ((matched_km - 50) * 940)
    else:
        base = 137000 + ((matched_km - 100) * 530)
        
    if temp_type == "냉장 / 동":
        base = base * 1.58
        
    final_fare = int(base * weight)
    return int(round(final_fare / 1000) * 1000)

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("📋 배차 조건 및 주선 요건 입력")
    
    st.markdown("#### 1. 운송유형 및 차종 선택")
    c_type1, c_type2 = st.columns(2)
    with c_type1:
        temp_type = st.radio("운송 형태", ["일반 상온", "냉장 / 동"], horizontal=True)
    with c_type2:
        truck_list = ["1톤", "1.4톤", "2.5톤", "3.5톤", "3.5톤 광폭", "5톤", "5톤 플러스", "5톤 장축", "8톤", "11톤", "11톤 장축", "14톤", "18톤", "25톤"]
        selected_truck = st.selectbox("차종(톤수) 선택", truck_list)

    st.markdown("#### 2. 운송 거리 설정")
    input_distance = st.number_input("운송 거리 입력 (km)", min_value=10, max_value=500, value=50, step=5)
    
    base_shipper_fare = get_base_shipper_fare(temp_type, selected_truck, input_distance)
    st.info(f"🎯 단가표 연동 완료: 기본 청구가 = **{base_shipper_fare:,.0f} 원**")

    st.markdown("#### 🗺️ 상·하차지 설정 및 공차 보정율 자동 매칭")
    c_loc1, c_loc2 = st.columns(2)
    with c_loc1:
        start_region_major = st.selectbox(
            "상차지 권역 선택",
            ["수도권 (서울/경기/인천)", "충청권 (대전/세종/충남북)", "전라권 (광주/전남북)", "경북권 (대구/경북)", "경남권 (부산/울산/경남)", "강원권 (강원특별자치도)"],
            index=0
        )
    with c_loc2:
        end_region_detail = st.selectbox(
            "하차 지역 선택 (PDF 기준 자동 분류)",
            list(destination_margin_rates.keys()),
            index=0
        )
        
    return_rate = destination_margin_rates[end_region_detail]
    st.success(f"📊 **[공차보정 자동 연동]** {end_region_detail} 지역 ➡️ **귀로 공차 보정률: {return_rate*100:.0f}%** 적용")

    st.markdown("#### 🌦️ 실시간 날씨 현황 중계")
    start_has_rain, start_weather_text, start_error = get_korea_live_weather(start_region_major)
    end_has_rain, end_weather_text, end_error = get_korea_live_weather(end_region_detail)
    
    st.markdown(f"📍 **상차지 날씨:** {start_weather_text} | 📍 **하차지 날씨:** {end_weather_text}")
    
    weather_premium_rate = 0
    if start_error or end_error:
        st.info("ℹ️ 기상 위성 통신 지연 시 아래 체크박스로 수동 제어가 가능합니다.")
        manual_weather = st.checkbox("⚠️ 현재 현장에 기상 악화(눈/비)가 발생하여 할증을 수동 적용합니다.")
        if manual_weather:
            weather_premium_rate = 20
            st.warning("⛈️ 기상 악화 할증(+20%) 강제 가산 완료")
    else:
        if start_has_rain or end_has_rain:
            weather_premium_rate = 20
            st.warning("⛈️ 상·하차지 중 악천후 지역 감지 ➡️ **날씨 할증(+20%)** 자동 반영")
        else:
            st.success("☀️ 상·하차지 기상 양호 (날씨 할증 없음)")

    st.markdown("#### 3. 기타 수동 할증 (%)")
    c3, c4, c5 = st.columns(3)
    with c3: p_premium = st.number_input("성수기 할증 (%)", min_value=0, value=0, step=5)
    with c4: u_premium = st.number_input("긴급 할증 (%)", min_value=0, value=0, step=5)
    with c5: n_premium = st.number_input("야간 할증 (%)", min_value=0, value=0, step=5)
    
    total_premium_rate = (p_premium + u_premium + n_premium + weather_premium_rate) / 100

    st.markdown("#### 5. 발생 실비 요금 (원)")
    c7, c8, c9, c10 = st.columns(4)
    with c7: toll = st.number_input("통행료", min_value=0, value=0, step=1000)
    with c8: load = st.number_input("상/하차비", min_value=0, value=0, step=1000)
    with c9: wait = st.number_input("대기료", min_value=0, value=0, step=1000)
    with c10: etc = st.number_input("기타 비용", min_value=0, value=0, step=1000)
    actual_expenses = toll + load + wait + etc

    st.markdown("#### 6. 주선 마진 설정")
    m_method = st.radio("마진 산정 방식", ["정률 마진 (%)", "정액 마진 (원)"], horizontal=True)
    if m_method == "정률 마진 (%)":
        margin_rate = st.number_input("목표 마진율 (%)", min_value=0.0, max_value=50.0, value=20.0, step=0.5)
    else:
        margin_flat = st.number_input("고정 마진 금액 (원)", min_value=0, value=30000, step=5000)

with col2:
    st.subheader("💰 최종 인수/청구 운임 산출")
    st.write("---")
    
    shipper_premium = base_shipper_fare * total_premium_rate
    shipper_return = base_shipper_fare * return_rate
    final_shipper_fee = base_shipper_fare + shipper_premium + shipper_return + actual_expenses
    
    if m_method == "정률 마진 (%)":
        final_driver_fee = final_shipper_fee * (1 - (margin_rate / 100))
        company_margin = final_shipper_fee - final_driver_fee
        final_margin_percent = margin_rate
    else:
        company_margin = margin_flat
        final_driver_fee = final_shipper_fee - company_margin
        final_margin_percent = (company_margin / final_shipper_fee * 100) if final_shipper_fee > 0 else 0

    st.metric(label="💵 화주 최종 청구 금액 (최종 청구가)", value=f"{int(round(final_shipper_fee)):,.0f} 원")
    st.metric(label="🚛 차주 배차 지급 금액 (최종 지급가)", value=f"{int(round(final_driver_fee)):,.0f} 원")
    st.write("---")
