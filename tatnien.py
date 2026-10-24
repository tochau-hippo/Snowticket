import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# Tự động refresh 1 phút / lần
st_autorefresh(interval=60000, key="river_auto_fetch")

st.set_page_config(page_title="Thống kê show RIVER", page_icon="🐎", layout="wide")

st.title("📊 Dashboard Theo Dõi Vé (Live)")
st.caption("Sự kiện: Minishow MÃ ĐÁO THÀNH CÔNG - Neko Lê x S.T Sơn Thạch")

# ==========================================
# THAY ĐƯỜNG LINK WORKER MỚI CỦA SHOW RIVER VÀO ĐÂY:
WORKER_URL = "https://river-worker.chinmuoi.workers.dev" 
# ==========================================

def get_data():
    try:
        r = requests.get(WORKER_URL, timeout=10)
        return r.json()
    except:
        return None

data = get_data()

if not data:
    st.error("Không kết nối được tới máy chủ Cloudflare. Vui lòng kiểm tra lại link.")
elif "message" in data:
    st.warning("Đang khởi tạo hệ thống cho show River. Vui lòng đợi 2 phút...")
else:
    t_sold = data.get("total_sold", 0)
    t_avail = data.get("total_available", 0)
    last_check = data.get("last_check", "N/A")
    history = data.get("history", [])
    zones = data.get("zones", [])
    sold_out_times = data.get("sold_out_times", {})

    st.markdown(f"**⏱ Dữ liệu lấy từ API lúc:** `{last_check}`")

    # Nếu nguyên rạp Sold Out thì nổ thông báo to
    if "ALL_SHOW" in sold_out_times:
        st.success(f"🎉 CHÚC MỪNG! SHOW ĐÃ SOLD OUT TOÀN BỘ LÚC: **{sold_out_times['ALL_SHOW']}** 🎉")

    col1, col2, col3 = st.columns(3)
    col1.metric("🎫 Tổng quy mô rạp", t_sold + t_avail)
    col2.metric("🔥 Tổng ghế đã bán", t_sold)
    col3.metric("✅ Ghế còn trống", t_avail)
    
    st.divider()

    left_col, right_col = st.columns([1.5, 1.2])

    with left_col:
        st.subheader("📋 Lịch sử chốt đơn")
        if history:
            df_hist = pd.DataFrame(history).rename(columns={
                "time": "Thời gian", "sold": "Đã bán", "available": "Trống", "detail": "Chi tiết thay đổi"
            })
            st.dataframe(df_hist, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("Chưa có biến động vé.")

    with right_col:
        st.subheader("🎯 Tình trạng từng hạng vé")
        if zones:
            # Map dữ liệu sold out time vào mảng zone
            for z in zones:
                z_name = z["name"]
                if z_name in sold_out_times:
                    z["sold_out_at"] = f"🔥 {sold_out_times[z_name]}"
                else:
                    z["sold_out_at"] = "Đang bán"

            df_zones = pd.DataFrame(zones).rename(columns={
                "name": "Khu vực", "price": "Giá vé", "total": "Tổng", 
                "sold": "Đã bán", "available": "Trống", "sold_out_at": "Trạng thái (Sold Out Lúc)"
            })
            df_zones["Giá vé"] = df_zones["Giá vé"].apply(lambda x: f"{x:,.0f} đ")
            st.dataframe(df_zones, use_container_width=True, hide_index=True, height=400)
