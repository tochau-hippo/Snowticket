import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# Tự động refresh trang mỗi 60 giây
st_autorefresh(interval=60000, key="ticket_auto_fetch")

st.set_page_config(page_title="Thống kê vé Ticketbox", layout="centered")
st.title("📊 Dashboard Theo Dõi Vé (Live)")

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

        # Hiển thị bảng LỊCH SỬ BIẾN ĐỘNG (Bỏ biểu đồ)
        if history:
            df_history = pd.DataFrame(history)
            df_history = df_history.rename(columns={"time": "Thời gian", "sold": "Đã bán", "available": "Còn trống"})
            
            st.subheader("📋 Lịch sử biến động bán vé")
            # In bảng hiển thị dòng mới nhất trên cùng
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
