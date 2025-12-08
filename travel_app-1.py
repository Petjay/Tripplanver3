import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
from geopy.geocoders import Nominatim
import plotly.express as px
import uuid

# 페이지 설정
st.set_page_config(page_title="여행 일정 매니저 Ver 11.1", layout="wide")

# --- 스타일 정의 ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    
    /* 버튼 스타일 커스텀 */
    .stButton button {
        width: 100%;
        border: 1px solid #f0f0f0;
        background-color: white;
        text-align: left; /* 텍스트 왼쪽 정렬 */
        padding: 10px;
        transition: 0.2s;
        height: auto;
        min-height: 50px;
        color: #444;
    }
    .stButton button:hover {
        border-color: #4e8cff;
        background-color: #f8faff;
        color: #4e8cff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 카드 헤더 */
    .card-header {
        text-align: center; font-weight: bold; font-size: 1.1em; padding: 8px;
        margin-bottom: 10px; border-radius: 8px;
    }
    
    /* 타임라인 */
    .timeline-row { display: flex; margin-bottom: 0px; }
    .timeline-time { width: 75px; text-align: right; padding-right: 15px; font-weight: bold; color: #555; font-size: 0.85em; padding-top: 15px; }
    .timeline-line-col { width: 30px; position: relative; display: flex; justify-content: center; }
    .timeline-line { position: absolute; top: 0; bottom: 0; width: 2px; background-color: #e0e0e0; left: 50%; transform: translateX(-50%); z-index: 0; }
    .timeline-dot { width: 12px; height: 12px; border-radius: 50%; background-color: white; border: 3px solid #2E86C1; z-index: 1; margin-top: 18px; }
    .timeline-content { flex: 1; background: white; border: 1px solid #eee; border-radius: 8px; padding: 10px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("✈️ 여행 일정 매니저 Ver 11.1")

# --- 1. 데이터 및 설정 ---
if 'schedule' not in st.session_state:
    st.session_state.schedule = pd.DataFrame(columns=["id", "start_date", "end_date", "시간", "구분", "카테고리", "내용", "장소", "비용", "메모", "색상", "lat", "lon"])
if 'custom_categories' not in st.session_state:
    st.session_state.custom_categories = ["항공", "숙박", "교통", "식비", "쇼핑", "관광", "준비물", "기타"]
if 'total_budget' not in st.session_state:
    st.session_state.total_budget = 3000000
if 'trip_start' not in st.session_state:
    st.session_state.trip_start = datetime.date.today()
if 'trip_end' not in st.session_state:
    st.session_state.trip_end = datetime.date.today() + timedelta(days=7)
if 'view_offset' not in st.session_state:
    st.session_state.view_offset = 0

ICON_MAP = {"준비물":"✅", "식비": "🍽️", "숙박": "🏨", "교통": "🚆", "항공": "✈️", "쇼핑": "🛍️", "관광": "📷", "기타": "📝"}
COLOR_PALETTE = ["#FF6B6B", "#FF9F43", "#FECA57", "#1DD1A1", "#54A0FF", "#5F27CD", "#FF9FF3", "#34495E"]

@st.cache_data
def get_coordinates(place_name):
    try:
        geolocator = Nominatim(user_agent="travel_app_v11_1")
        location = geolocator.geocode(place_name)
        if location: return location.latitude, location.longitude
        return None, None
    except: return None, None

# --- 2. 팝업창 (Dialog) ---
@st.dialog("✨ 일정 상세 관리")
def entry_modal(mode="일정", default_date=None, edit_id=None):
    edit_data = None
    if edit_id:
        rows = st.session_state.schedule[st.session_state.schedule['id'] == edit_id]
        if not rows.empty: edit_data = rows.iloc[0]

    if edit_id: st.caption("일정을 수정하거나 삭제합니다.")
    elif mode == "준비": st.info("📌 사전 예약/준비물 입력")
    else: st.caption(f"{default_date} 일정 입력")
    
    with st.form("modal_form"):
        def_start = edit_data['start_date'] if edit_id else (st.session_state.trip_start if mode=="준비" else default_date)
        def_end = edit_data['end_date'] if edit_id else (st.session_state.trip_start if mode=="준비" else default_date)
        def_cat = edit_data['카테고리'] if edit_id else st.session_state.custom_categories[0]
        def_cost = int(edit_data['비용']) if edit_id else 0
        def_content = edit_data['내용'] if edit_id else ""
        def_memo = edit_data['메모'] if edit_id else ""
        def_place = edit_data['장소'] if edit_id else ""
        def_color = edit_data['색상'] if edit_id else ("#FF6B6B" if mode=="준비" else "#54A0FF")
        def_time = edit_data['시간'] if edit_id else datetime.time(9,0)

        if mode == "준비" or (edit_data is not None and edit_data['구분'] == '준비'):
            start, end, type_, time_ = def_start, def_start, "준비", datetime.time(0,0)
            c1, c2 = st.columns(2)
            cat = c1.selectbox("카테고리", st.session_state.custom_categories, index=st.session_state.custom_categories.index(def_cat) if def_cat in st.session_state.custom_categories else 0)
            cost = c2.number_input("비용 (원)", min_value=0, step=1000, value=def_cost)
            content = st.text_input("내용", value=def_content, placeholder="예: 항공권 결제")
            memo = st.text_area("메모", value=def_memo)
            place = ""
        else:
            c1, c2 = st.columns(2)
            start = c1.date_input("시작일", value=def_start)
            end = c2.date_input("종료일", value=def_end)
            
            cat_opts = [c for c in st.session_state.custom_categories if c != "준비물"]
            cat_idx = cat_opts.index(def_cat) if def_cat in cat_opts else 0
            cat = st.selectbox("카테고리", cat_opts, index=cat_idx)
            
            if cat == "숙박": def_type, def_t = "숙박", datetime.time(15, 0)
            elif cat == "항공": def_type, def_t = "이동", datetime.time(10,0)
            else: def_type, def_t = "일정", datetime.time(9, 0)
            
            final_t = def_time if edit_id else def_t
            type_ = edit_data['구분'] if edit_id else def_type
            
            if type_ != "숙박": time_ = st.time_input("시간", value=final_t)
            else: time_ = datetime.time(15,0)

            content = st.text_input("내용", value=def_content)
            place = st.text_input("장소", value=def_place)
            cost = st.number_input("비용", min_value=0, step=1000, value=def_cost)
            memo = st.text_input("메모", value=def_memo)

        st.markdown("**🎨 라벨 색상**")
        selected_color = st.color_picker("색상", value=def_color)
        cols = st.columns(8)
        for i, color in enumerate(COLOR_PALETTE): cols[i].markdown(f"<div style='background-color:{color};height:15px;border-radius:50%;'></div>", unsafe_allow_html=True)

        c_sub, c_del = st.columns([1, 0.3])
        with c_sub:
            if st.form_submit_button("💾 저장/수정", type="primary"):
                lat, lon = None, None
                if place and place != def_place:
                    with st.spinner(".."): lat, lon = get_coordinates(place)
                elif edit_id: lat, lon = edit_data['lat'], edit_data['lon']
                
                new_row = {
                    "id": edit_id if edit_id else str(uuid.uuid4()),
                    "start_date": start, "end_date": end, "시간": time_, "구분": type_, "카테고리": cat,
                    "내용": content, "장소": place, "비용": cost, "메모": memo, "색상": selected_color, "lat": lat, "lon": lon
                }
                if edit_id: st.session_state.schedule = st.session_state.schedule[st.session_state.schedule['id'] != edit_id]
                st.session_state.schedule = pd.concat([st.session_state.schedule, pd.DataFrame([new_row])], ignore_index=True)
                st.rerun()
        with c_del:
            if edit_id and st.form_submit_button("🗑️"):
                st.session_state.schedule = st.session_state.schedule[st.session_state.schedule['id'] != edit_id]
                st.rerun()

# --- 3. 사이드바 ---
with st.sidebar:
    st.header("⚙️ 설정")
    with st.expander("📅 기간 설정", expanded=True):
        st.session_state.trip_start = st.date_input("시작일", st.session_state.trip_start)
        st.session_state.trip_end = st.date_input("종료일", st.session_state.trip_end)
    st.session_state.total_budget = st.number_input("총 예산", value=st.session_state.total_budget, step=100000)
    if st.button("🗑️ 초기화"):
        st.session_state.schedule = st.session_state.schedule.iloc[0:0]; st.rerun()

# --- 4. 메인 화면 ---
tab1, tab2, tab3, tab4 = st.tabs(["✈️ 플래너", "📱 타임라인", "🗺️ 지도", "💰 예산"])

with tab1:
    DAYS_SHOW = 5
    c_prev, c_title, c_next = st.columns([1, 8, 1])
    current_off = st.session_state.view_offset
    view_s = st.session_state.trip_start + timedelta(days=current_off)
    view_e = min(view_s + timedelta(days=DAYS_SHOW-1), st.session_state.trip_end)
    
    with c_title: st.markdown(f"<h4 style='text-align:center;'>📅 {view_s.strftime('%Y.%m.%d')} ~ {view_e.strftime('%m.%d')}</h4>", unsafe_allow_html=True)
    with c_prev:
        if current_off > 0 and st.button("◀"): st.session_state.view_offset = max(0, current_off - DAYS_SHOW); st.rerun()
    with c_next:
        if st.session_state.trip_start + timedelta(days=current_off + DAYS_SHOW) <= st.session_state.trip_end and st.button("▶"): 
            st.session_state.view_offset += DAYS_SHOW; st.rerun()

    cols = st.columns([1.1] + [1] * DAYS_SHOW)
    week_days = ["(월)", "(화)", "(수)", "(목)", "(금)", "(토)", "(일)"]

    # 1. 사전 준비
    with cols[0]:
        with st.container(border=True, height=600):
            st.markdown("<div class='card-header' style='background:#fff9db; color:#d48806;'>🧳 준비/예약</div>", unsafe_allow_html=True)
            if st.button("➕ 추가", key="btn_prep"): entry_modal(mode="준비")
            st.divider()
            
            if not st.session_state.schedule.empty:
                prep_df = st.session_state.schedule[st.session_state.schedule['구분']=='준비']
                for _, r in prep_df.iterrows():
                    # [핵심] 버튼만으로 구성 (좌측 컬러바는 st.columns로 구현)
                    c_col, c_btn = st.columns([0.15, 9.85]) # 좌측 좁은 공간에 색상표시
                    with c_col:
                        st.markdown(f"<div style='background:{r['색상']}; height:50px; border-radius:4px; margin-top:2px;'></div>", unsafe_allow_html=True)
                    with c_btn:
                        icon = ICON_MAP.get(r['카테고리'], "✅")
                        cost_s = f" (₩{r['비용']//1000}k)" if r['비용']>0 else ""
                        # 버튼 텍스트 구성
                        btn_label = f"{icon} {r['내용']}{cost_s}"
                        if st.button(btn_label, key=f"p_{r['id']}", use_container_width=True):
                            entry_modal(mode="준비", edit_id=r['id'])

    # 2. 날짜별 일정
    for i in range(DAYS_SHOW):
        d_idx = current_off + i
        t_date = st.session_state.trip_start + timedelta(days=d_idx)
        
        with cols[i+1]:
            with st.container(border=True, height=600):
                if t_date <= st.session_state.trip_end:
                    is_today = t_date == datetime.date.today()
                    bg = "#eef4ff" if is_today else "#f8f9fa"
                    fg = "#4e8cff" if is_today else "#333"
                    wd = week_days[t_date.weekday()]
                    st.markdown(f"<div class='card-header' style='background:{bg}; color:{fg};'>{t_date.month}/{t_date.day} {wd}</div>", unsafe_allow_html=True)
                    
                    if st.button("➕", key=f"add_{t_date}"): entry_modal(mode="일정", default_date=t_date)
                    st.divider()
                    
                    if not st.session_state.schedule.empty:
                        mask = (st.session_state.schedule['start_date'] <= t_date) & (st.session_state.schedule['end_date'] >= t_date) & (st.session_state.schedule['구분'] != '준비')
                        d_data = st.session_state.schedule.loc[mask].sort_values("시간")
                        
                        for _, r in d_data.iterrows():
                            # [핵심] 버튼 + 좌측 컬러바
                            c_col, c_btn = st.columns([0.15, 9.85])
                            with c_col:
                                st.markdown(f"<div style='background:{r['색상']}; height:50px; border-radius:4px; margin-top:2px;'></div>", unsafe_allow_html=True)
                            with c_btn:
                                icon = ICON_MAP.get(r['카테고리'], "📍")
                                time_s = r['시간'].strftime('%H:%M')
                                cost_s = f" (₩{r['비용']//1000}k)" if r['비용']>0 else ""
                                dur = ""
                                if r['start_date'] != r['end_date']:
                                    if t_date == r['start_date']: dur = " (S)"
                                    elif t_date == r['end_date']: dur = " (E)"
                                    else: dur = " (~ing)"
                                
                                # 버튼 라벨: 시간 | 아이콘 내용 비용
                                label = f"[{time_s}] {icon} {r['내용']}{dur}{cost_s}"
                                if st.button(label, key=f"s_{r['id']}", use_container_width=True):
                                    entry_modal(mode="일정", default_date=t_date, edit_id=r['id'])
                else:
                    st.markdown("<div style='text-align:center; color:#ddd; padding-top:200px;'>-</div>", unsafe_allow_html=True)

# [TAB 2~4] 기존 로직
with tab2: # 타임라인
    if st.session_state.schedule.empty: st.info("일정이 없습니다.")
    else:
        mask = (st.session_state.schedule['start_date'] >= st.session_state.trip_start) & (st.session_state.schedule['start_date'] <= st.session_state.trip_end) & (st.session_state.schedule['구분'] != '준비')
        t_data = st.session_state.schedule.loc[mask].sort_values(by=["start_date", "시간"])
        st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
        curr_d = None
        for _, r in t_data.iterrows():
            if curr_d != r['start_date']:
                st.markdown(f"<div style='font-size:1.1em; font-weight:bold; margin-top:20px; border-bottom:1px solid #333;'>{r['start_date'].month}/{r['start_date'].day}</div>", unsafe_allow_html=True)
                curr_d = r['start_date']
            icon = ICON_MAP.get(r['카테고리'], "📍")
            st.markdown(f"""<div class='timeline-row'><div class='timeline-time'>{r['시간'].strftime('%H:%M')}</div><div class='timeline-line-col'><div class='timeline-line'></div><div class='timeline-dot' style='border-color:{r['색상']}'></div></div><div class='timeline-content'><b>{icon} {r['내용']}</b><br><span style='color:#777; font-size:0.85em;'>{r['카테고리']}</span></div></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tab3: # 지도
    map_df = st.session_state.schedule.dropna(subset=['lat', 'lon'])
    if not map_df.empty: st.map(map_df, color="색상")
    else: st.info("지도에 표시할 장소가 없습니다.")

with tab4: # 비용
    total = st.session_state.schedule["비용"].sum()
    remain = st.session_state.total_budget - total
    c1, c2, c3 = st.columns(3)
    c1.metric("총 예산", f"{st.session_state.total_budget:,}")
    c2.metric("지출", f"{total:,}", delta=f"-{total:,}", delta_color="inverse")
    c3.metric("잔액", f"{remain:,}", delta=f"{remain:,}")
    if total > 0:
        df_g = st.session_state.schedule.groupby("카테고리")["비용"].sum().reset_index()
        fig = px.pie(df_g, values='비용', names='카테고리', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)