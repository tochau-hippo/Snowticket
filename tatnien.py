import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Auto refresh 1 phút / lần
st_autorefresh(interval=60000, key="river_auto_fetch")

st.set_page_config(page_title="STNK - Mã đáo thành công", page_icon="🐎", layout="wide")

st.title("📊 Dashboard Theo Dõi Vé (Live)")
st.caption("Sự kiện: Minishow MÃ ĐÁO THÀNH CÔNG - Neko Lê x S.T Sơn Thạch")

# ==========================================
WORKER_URL = "https://tatnienriver.chinmuoi.workers.dev" # Đảm bảo link này đúng
# ==========================================

# Khởi tạo bộ nhớ tạm để không bắn pop-up 2 lần cho cùng 1 khu vực
if "toasted_zones" not in st.session_state:
    st.session_state.toasted_zones = set()

# Giờ mở bán cố định để tính kỷ lục Sold Out
OPENING_TIME_STR = "12:00:00 26/10/2026"
opening_dt = datetime.strptime(OPENING_TIME_STR, "%H:%M:%S %d/%m/%Y")

def calc_soldout_minutes(so_time_str):
    try:
        so_dt = datetime.strptime(so_time_str, "%H:%M:%S %d/%m/%Y")
        diff_mins = (so_dt - opening_dt).total_seconds() / 60
        if diff_mins < 0:
            return "Nội bộ/Pre-sale"
        elif diff_mins < 1:
            return "Chưa tới 1 phút"
        else:
            return f"{int(diff_mins)} phút"
    except:
        return "N/A"

def get_data():
    try:
        return requests.get(WORKER_URL, timeout=10).json()
    except:
        return None

data = get_data()

if not data:
    st.error("Không kết nối được tới máy chủ Cloudflare. Vui lòng kiểm tra lại link.")
elif "message" in data:
    st.warning("Đang chờ Cron Trigger lấy dữ liệu. Hãy đợi 1-2 phút nhé...")
else:
    t_sold = data.get("total_sold", 0)
    t_avail = data.get("total_available", 0)
    last_check = data.get("last_check", "N/A")
    history = data.get("history", [])
    zones = data.get("zones", [])
    sold_out_times = data.get("sold_out_times", {})

    # ==========================
    # LOGIC HIỆU ỨNG & POP-UP
    # ==========================
    
    # 1. Bắn pop-up góc màn hình khi TỪNG ZONE Sold out
    for z in zones:
        z_name = z["name"]
        if z_name in sold_out_times and z_name not in st.session_state.toasted_zones:
            # Hiện pop-up nhỏ tự tắt
            st.toast(f"🎇 Cháy vé: Đã SOLD OUT zone {z_name}!", icon="🔥")
            st.session_state.toasted_zones.add(z_name)
            
        # Nếu rớt vé (nhả vé ra), xóa khỏi danh sách đã toast để lần sau sold out lại bắn tiếp
        elif z_name not in sold_out_times and z_name in st.session_state.toasted_zones:
            st.session_state.toasted_zones.remove(z_name)

    # 2. Bắn hiệu ứng TOÀN MÀN HÌNH khi TOTAL SHOW Sold out
    if "ALL_SHOW" in sold_out_times:
        so_str = sold_out_times["ALL_SHOW"]
        record_time = calc_soldout_minutes(so_str)
        
        if "ALL_SHOW" not in st.session_state.toasted_zones:
            st.balloons() # Bắn bong bóng/pháo bay lả tả
            st.toast(f"🏆 KỶ LỤC! SHOW ĐÃ SOLD OUT TRONG {record_time}!", icon="🎉")
            st.session_state.toasted_zones.add("ALL_SHOW")
            
        st.success(f"🎆 **TRẠNG THÁI: SOLD OUT TOÀN BỘ SHOW** LÚC {so_str} (KỶ LỤC: **{record_time}** KỂ TỪ KHI MỞ BÁN) 🎆")
    else:
        # Nếu chưa sold out, xóa cờ nếu trước đó đã gắn (chống lỗi rớt vé ALL_SHOW)
        if "ALL_SHOW" in st.session_state.toasted_zones:
            st.session_state.toasted_zones.remove("ALL_SHOW")
        st.info(f"⏳ **TRẠNG THÁI:** ĐANG BÁN ... (Giờ mở cửa: {OPENING_TIME_STR})")

    st.markdown(f"**⏱ Dữ liệu lấy từ API lúc:** `{last_check}`")

    col1, col2, col3 = st.columns(3)
    col1.metric("🎫 Tổng quy mô rạp", t_sold + t_avail)
    col2.metric("🔥 Tổng ghế đã chốt", t_sold)
    col3.metric("✅ Ghế còn trống", t_avail)
    
    st.divider()

    left_col, right_col = st.columns([1.5, 1.2])

    with left_col:
        st.subheader("📋 Lịch sử chốt đơn")
        if history:
            df_hist = pd.DataFrame(history).rename(columns={
                "time": "Thời gian", "sold": "Đã bán", "available": "Trống", "detail": "Chi tiết thay đổi"
            })
            st.dataframe(df_hist, use_container_width=True, hide_index=True, height=500)
        else:
            st.info("Chưa có biến động vé.")

    with right_col:
        st.subheader("🎯 Tình trạng từng hạng vé")
        if zones:
            for z in zones:
                z_name = z["name"]
                if z_name in sold_out_times:
                    rec = calc_soldout_minutes(sold_out_times[z_name])
                    z["sold_out_at"] = f"🔥 {sold_out_times[z_name]} ({rec})"
                else:
                    z["sold_out_at"] = "Đang bán"

            df_zones = pd.DataFrame(zones).rename(columns={
                "name": "Khu vực", "price": "Giá vé", "total": "Tổng", 
                "s1": "Trống (1)", "s2": "Hold (2)", "s3": "TT (3)", "s4": "Bán/Khoá (4)",
                "sold_out_at": "Sold Out Lúc"
            })
            
            # Gỡ bớt mấy cột thừa cho đỡ chật ngang màn hình
            df_zones = df_zones[["Khu vực", "Tổng", "Trống (1)", "Hold (2)", "TT (3)", "Bán/Khoá (4)", "Sold Out Lúc"]]
            
            st.dataframe(df_zones, use_container_width=True, hide_index=True, height=500)
