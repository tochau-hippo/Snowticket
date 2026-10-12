import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# Tự động refresh trang mỗi 60 giây (60000 milliseconds) để kéo data mới từ Worker
st_autorefresh(interval=60000, key="ticket_auto_fetch")

st.set_page_config(page_title="Thống kê vé Ticketbox", layout="centered")
st.title("📊 Dashboard Theo Dõi Vé (Live)")

# ==========================================
# DÁN LINK CLOUDFLARE WORKER CỦA M VÀO ĐÂY:
WORKER_URL = "https://snowticket.chinmuoi.workers.dev" # Nhớ thay đúng tên link của m
# ==========================================

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
    # Nếu Worker báo chưa có data (do Cron chưa kịp chạy lần đầu)
    if "message" in data:
        st.warning("Hệ thống Cloudflare đang khởi động, vui lòng đợi 1-2 phút rồi web sẽ tự động lên data...")
    else:
        total_sold = data.get("total_sold", 0)
        total_available = data.get("total_available", 0)
        last_check = data.get("last_check", "N/A")
        history = data.get("history", [])

        st.caption(f"⏱ **Dữ liệu được hệ thống tự động kiểm tra lần cuối lúc:** {last_check}")

        # In 3 chỉ số tổng quan ở trên cùng
        col1, col2, col3 = st.columns(3)
        col1.metric("🎫 Tổng vé toàn rạp", total_sold + total_available)
        col2.metric("🔥 Tổng vé đã bán", total_sold)
        col3.metric("✅ Còn trống", total_available)

        st.divider()

        if history:
            df = pd.DataFrame(history)
            # Đổi tên cột hiển thị cho đẹp
            df = df.rename(columns={"time": "Thời gian", "sold": "Đã bán", "available": "Còn trống"})
            
            st.subheader("📈 Biểu đồ biến động vé bán")
            # Set cột Thời gian làm trục X, Đã bán làm trục Y
            chart_data = df.set_index("Thời gian")["Đã bán"]
            # Vì trong Worker mình dùng unshift (chèn dòng mới lên đầu) nên mảng đang bị ngược từ Mới -> Cũ
            # Dùng [::-1] để lật ngược lại Cũ -> Mới cho biểu đồ đường đi lên từ trái sang phải
            st.line_chart(chart_data.iloc[::-1])

            st.subheader("📋 Lịch sử chi tiết các lần thay đổi")
            # In bảng hiển thị dòng mới nhất trên cùng
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có sự thay đổi vé nào được ghi nhận kể từ lúc bắt đầu theo dõi.")
