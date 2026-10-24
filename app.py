import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Tự động refresh trang mỗi 60 giây (60000 milliseconds)
st_autorefresh(interval=60000, key="ticket_auto_fetch")

st.set_page_config(page_title="Thống kê vé Ticketbox", page_icon="❄️", layout="centered")
st.title("📊 Dashboard Theo Dõi Vé S'NOW (Live)")

# --- CODE TRIỆU HỒI TUYẾT RƠI VĨNH VIỄN ---
snow_css = """
<style>
.snowflake {
  color: #fff;
  font-size: 1.5em;
  font-family: Arial, sans-serif;
  text-shadow: 0 0 5px #000;
  position: fixed;
  top: -10%;
  z-index: 9999;
  user-select: none;
  cursor: default;
  animation-name: snowflakes-fall, snowflakes-shake;
  animation-duration: 10s, 3s;
  animation-timing-function: linear, ease-in-out;
  animation-iteration-count: infinite, infinite;
  animation-play-state: running, running;
}
@keyframes snowflakes-fall { 0% { top: -10% } 100% { top: 100% } }
@keyframes snowflakes-shake { 
  0%, 100% { transform: translateX(0) } 
  50% { transform: translateX(80px) } 
}
.snowflake:nth-of-type(0) { left: 1%; animation-delay: 0s, 0s }
.snowflake:nth-of-type(1) { left: 10%; animation-delay: 1s, 1s }
.snowflake:nth-of-type(2) { left: 20%; animation-delay: 6s, .5s }
.snowflake:nth-of-type(3) { left: 30%; animation-delay: 4s, 2s }
.snowflake:nth-of-type(4) { left: 40%; animation-delay: 2s, 2s }
.snowflake:nth-of-type(5) { left: 50%; animation-delay: 8s, 3s }
.snowflake:nth-of-type(6) { left: 60%; animation-delay: 6s, 2s }
.snowflake:nth-of-type(7) { left: 70%; animation-delay: 2.5s, 1s }
.snowflake:nth-of-type(8) { left: 80%; animation-delay: 1s, 0s }
.snowflake:nth-of-type(9) { left: 90%; animation-delay: 3s, 1.5s }
</style>
<div class="snowflakes" aria-hidden="true">
  <div class="snowflake">❅</div><div class="snowflake">❆</div><div class="snowflake">❄</div>
  <div class="snowflake">❅</div><div class="snowflake">❆</div><div class="snowflake">❄</div>
  <div class="snowflake">❅</div><div class="snowflake">❆</div><div class="snowflake">❄</div>
  <div class="snowflake">❅</div>
</div>
"""
st.markdown(snow_css, unsafe_allow_html=True)
# ------------------------------------------
# API Cố định của sự kiện
API_URL = "https://api-v2.ticketbox.vn/event/api/v1/events/showings/41775904473808/seatmap"

# Ô nhập Token (Mỗi khi hết 2 phút m dán cái mới vào đây rồi Enter là web tự update data)
st.markdown("---")
token_input = st.text_input("🔑 Dán Access Token mới vào đây (Bắt buộc để lấy data):", type="password")
st.markdown("---")

# Khởi tạo Session State để lưu lịch sử biến động trong RAM (Tránh bị mất khi web F5)
if "ticket_history" not in st.session_state:
    st.session_state.ticket_history = []
if "last_total_sold" not in st.session_state:
    st.session_state.last_total_sold = -1
if "last_zones" not in st.session_state:
    st.session_state.last_zones = []

@st.cache_data(ttl=2) # Cache rất ngắn 2 giây để tránh bị spam API quá đà trong lúc test
def fetch_ticket_data(_token):
    if not _token:
        return None
    headers = {
        "accept": "application/json",
        "origin": "https://ticketbox.vn",
        "referer": "https://ticketbox.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "x-tb-access-token": _token
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if token_input:
    data = fetch_ticket_data(token_input.strip())
    
    if data and "error" in data:
        st.error(f"Nhập API mới nha")
    elif data:
        sections = data.get("data", {}).get("result", {}).get("sections", [])
        
        current_total_sold = 0
        current_total_available = 0
        current_zones = []

        # Đếm vé y hệt logic cũ
        for sec in sections:
            if sec.get("isStage"): continue
            
            all_seats = []
            if "seats" in sec:
                all_seats.extend(sec["seats"])
            elif "rows" in sec:
                for row in sec["rows"]:
                    if "seats" in row:
                        all_seats.extend(row["seats"])
            
            if all_seats:
                total = len(all_seats)
                # Đang trống = 1
                available = sum(1 for s in all_seats if str(s.get("status")) == "1")
                sold = total - available
                
                current_total_available += available
                current_total_sold += sold
                
                current_zones.append({
                    "Hạng Vé / Khu Vực": sec.get("name", "Unknown"), 
                    "Tổng vé": total, 
                    "Đã bán": sold, 
                    "Còn trống": available
                })

        # Xử lý biến động (So sánh với dữ liệu vòng lặp trước)
        now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        if st.session_state.last_total_sold != current_total_sold:
            change_details = []
            
            # Tính Zone nào vừa nhảy vé
            if st.session_state.last_zones:
                for cur_z in current_zones:
                    old_z_val = next((z["Đã bán"] for z in st.session_state.last_zones if z["Hạng Vé / Khu Vực"] == cur_z["Hạng Vé / Khu Vực"]), 0)
                    diff = cur_z["Đã bán"] - old_z_val
                    if diff != 0:
                        sign = "+" if diff > 0 else ""
                        change_details.append(f'{cur_z["Hạng Vé / Khu Vực"]}: {sign}{diff}')
            
            detail_str = " | ".join(change_details) if change_details else "Lần đầu tải dữ liệu"
            
            st.session_state.ticket_history.insert(0, {
                "Thời gian": now_str,
                "Đã bán": current_total_sold,
                "Còn trống": current_total_available,
                "Biến động chi tiết": detail_str
            })
            
            # Cập nhật state cũ thành mới
            st.session_state.last_total_sold = current_total_sold
            st.session_state.last_zones = current_zones

        # HẾT PHẦN LOGIC - BẮT ĐẦU VẼ BẢNG
        st.caption(f"⏱ Dữ liệu được cập nhật lần cuối lúc: {now_str}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🎫 Tổng vé toàn rạp", current_total_sold + current_total_available)
        col2.metric("🔥 Tổng vé đã bán", current_total_sold)
        col3.metric("✅ Còn trống", current_total_available)
        
        st.divider()
        
        if st.session_state.ticket_history:
            st.subheader("📋 Lịch sử biến động bán vé")
            df_history = pd.DataFrame(st.session_state.ticket_history)
            st.dataframe(df_history, use_container_width=True, hide_index=True)
            
        st.divider()
        
        if current_zones:
            st.subheader("🎯 Thống kê chi tiết từng hạng vé")
            df_zones = pd.DataFrame(current_zones)
            st.dataframe(df_zones, use_container_width=True, hide_index=True)

else:
    st.info("Vui lòng lấy Access Token mới nhất từ Ticketbox dán vào ô bên trên để bắt đầu theo dõi.")
