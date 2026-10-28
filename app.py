import streamlit as st
import pandas as pd

# 페이지 설정 (대일물류 상호 반영)
st.set_page_config(page_title="(주)대일물류 운임 계산기", layout="wide")

# ------------------------------------------------------------------
# 🔒 1단계: 보안 비밀번호 세션 관리
# ------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["password_input"] == "8886":  # 요청하신 암호 8886 지정
        st.session_state["authenticated"] = True
        st.session_state["password_error"] = False
    else:
        st.session_state["authenticated"] = False
        st.session_state["password_error"] = True

# 로그인이 안 되어 있으면 암호 입력창 표시
if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_value=True)
    st.title("🔒 (주)대일물류 통합 화물 정산 시스템")
    st.subheader("직원 인증이 필요합니다.")
    
    st.text_input("접속 비밀번호를 입력하세요.", type="password", key="password_input", on_change=check_password)
    
    if st.session_state.get("password_error"):
        st.error("❌ 비밀번호가 올바르지 않습니다. 다시 입력해 주세요.")
    st.stop()

# ------------------------------------------------------------------
# 🔓 2단계: 인증 완료 후 메인 계산기 화면 구동
# ------------------------------------------------------------------
st.title("🚛 (주)대일물류 맞춤형 완전 자동화 운임 계산기")
st.caption("대일물류 전용 시스템입니다. 외부 PC 및 스마트폰에서도 실시간 동시 정산이 가능합니다.")

# 차종별 10km ~ 500km 기본 운임 자동 계산 공식 표준화 탑재
def get_base_fare(temp_type, truck_size, km):
    matched_km = int(round(km / 5.0) * 5)
    matched_km = max(10, min(500, matched_km))
    
    # 톤수별 표준 단가 가중치
    weight_dict = {
        "1톤": 1.0, "1.4톤": 1.15, "2.5톤": 1.45, "3.5톤": 1.65, 
        "3.5톤 광폭": 1.75, "5톤": 2.0, "5톤 플러스": 2.1, "5톤 장축": 2.25, 
        "8톤": 2.4, "11톤": 2.9, "11톤 장축": 3.2, "14톤": 3.1, "18톤": 3.3, "25톤": 3.7
    }
    weight = weight_dict.get(truck_size, 1.0)
    
    if matched_km <= 50:
        base = 40000 + (matched_km * 800)
    elif matched_km <= 100:
        base = 80000 + ((matched_km - 50) * 900)
    else:
        base = 125000 + ((matched_km - 100) * 500)
        
    if temp_type == "냉장 / 동":
        base = base * 1.55
        
    final_fare = int(base * weight)
    return int(round(final_fare / 1000) * 1000)

# 화면 레이아웃 구성
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
    
    base_fare_won = get_base_fare(temp_type, selected_truck, input_distance)
    st.success(f"🎯 단가 매칭 완료: [{temp_type} - {selected_truck}] {input_distance}km 기준 기본 운임 = **{base_fare_won:,.0f} 원**")

    st.markdown("#### 3. 운송조건 할증 (%)")
    c3, c4, c5, c6 = st.columns(4)
    with c3: p_premium = st.number_input("성수기 할증 (%)", min_value=0, value=0, step=5)
    with c4: u_premium = st.number_input("긴급 할증 (%)", min_value=0, value=0, step=5)
    with c5: n_premium = st.number_input("야간 할증 (%)", min_value=0, value=0, step=5)
    with w_premium := c6: w_premium_input = st.number_input("주말/공휴일 할증 (%)", min_value=0, value=0, step=5)
    total_premium_rate = (p_premium + u_premium + n_premium + w_premium_input) / 100

    st.markdown("#### 4. 도착지 귀로 공차 보정")
    return_type = st.selectbox(
        "도착 권역의 귀로 물량 수준",
        ["귀로 물량이 많은 지역 (0% ~ +3% 보정)", "귀로 물량이 보통인 지역 (+5% 보정)", "귀로 물량이 적은 지역 (+10% 보정)"]
    )
    if "많은 지역" in return_type:
        return_rate = st.slider("세부 보정률 선택 (%)", min_value=0, max_value=3, value=0) / 100
    elif "보통인 지역" in return_type:
        return_rate = 0.05
    else:
        return_rate = 0.10

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
        # 요청하신 기본 마진율 20% 기본값으로 고정 세팅
        margin_rate = st.number_input("목표 마진율 (%)", min_value=0.0, max_value=50.0, value=20.0, step=0.5)
    else:
        margin_flat = st.number_input("고정 마진 금액 (원)", min_value=0, value=30000, step=5000)

with col2:
    st.subheader("💰 최종 인수/청구 운임 산출")
    st.write("---")
    
    premium_amt = base_fare_won * total_premium_rate
    return_amt = base_fare_won * return_rate
    driver_fee = base_fare_won + premium_amt + return_amt + actual_expenses
    
    if m_method == "정률 마진 (%)":
        if margin_rate < 100:
            shipper_fee = driver_fee / (1 - (margin_rate / 100))
        else:
            shipper_fee = driver_fee
        company_margin = shipper_fee - driver_fee
        final_margin_percent = margin_rate
    else:
        company_margin = margin_flat
        shipper_fee = driver_fee + company_margin
        final_margin_percent = (company_margin / shipper_fee * 100) if shipper_fee > 0 else 0

    st.metric(label="💵 화주 최종 청구 금액 (최종 청구가)", value=f"{int(round(shipper_fee)):,.0f} 원")
    st.metric(label="🚛 차주 배차 지급 금액 (최종 지급가)", value=f"{int(round(driver_fee)):,.0f} 원")
    st.write("---")
    st.success(f"📈 대일물류 확보 마진 (수익): **{int(round(company_margin)):,.0f} 원** (정산 마진율: {final_margin_percent:.1f}%)")
    
    st.markdown("##### 🔍 상세 운임 산정 항목")
    details_df = pd.DataFrame({
        "산정 항목": ["기본 단가(자동 연동)", "운송조건 할증액", "귀로 공차보정액", "실비 합계", "최종 차주지급가(원가)", "최종 주선마진"],
        "산출 금액": [
            f"{base_fare_won:,.0f} 원",
            f"{premium_amt:,.0f} 원",
            f"{return_amt:,.0f} 원",
            f"{actual_expenses:,.0f} 원",
            f"{driver_fee:,.0f} 원",
            f"{company_margin:,.0f} 원"
        ]
    })
    st.table(details_df)
