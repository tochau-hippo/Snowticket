import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# Tự động refresh trang mỗi 60 giây
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

WORKER_URL = "https://snowticket.chinmuoi.workers.dev"

def fetch_worker_data():
    try:
        response = requests.get(WORKER_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Lỗi kết nối tới hệ thống ngầm: {e}")
        return None

data = fetch_worker_data()

if data:
    if "message" in data:
        st.warning("Hệ thống Cloudflare đang khởi động, vui lòng đợi 1-2 phút rồi web sẽ tự động lên data...")
    else:
        total_sold = data.get("total_sold", 0)
        total_available = data.get("total_available", 0)
        last_check = data.get("last_check", "N/A")
        history = data.get("history", [])
        zones = data.get("zones", [])

        st.caption(f"⏱ **Dữ liệu được cập nhật lần cuối lúc:** {last_check}")

        # In 3 chỉ số tổng quan ở trên cùng
        col1, col2, col3 = st.columns(3)
        col1.metric("🎫 Tổng vé toàn rạp", total_sold + total_available)
        col2.metric("🔥 Tổng vé đã bán", total_sold)
        col3.metric("✅ Còn trống", total_available)

        st.divider()

        # Hiển thị bảng LỊCH SỬ BIẾN ĐỘNG
        if history:
            df_history = pd.DataFrame(history)
            
            # Kiểm tra nếu API đã trả về cột detail thì mới đổi tên, tránh lỗi lúc mảng cũ chưa có detail
            rename_cols = {"time": "Thời gian", "sold": "Đã bán", "available": "Còn trống"}
            if "detail" in df_history.columns:
                rename_cols["detail"] = "Biến động chi tiết"
                
            df_history = df_history.rename(columns=rename_cols)
            
            st.subheader("📋 Lịch sử biến động bán vé")
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có sự thay đổi vé nào được ghi nhận kể từ lúc bắt đầu theo dõi.")
            
        st.divider()
            
        # Hiển thị bảng CHI TIẾT TỪNG KHU VỰC
        if zones:
            df_zones = pd.DataFrame(zones)
            df_zones = df_zones.rename(columns={"name": "Hạng Vé / Khu Vực", "total": "Tổng vé", "sold": "Đã bán", "available": "Còn trống"})
            
            st.subheader("🎯 Thống kê chi tiết từng hạng vé")
            st.dataframe(df_zones, use_container_width=True, hide_index=True)
        else:
            st.warning("Chưa có dữ liệu chi tiết từng khu vực. Vui lòng chờ Cron chạy lại để cập nhật.")
