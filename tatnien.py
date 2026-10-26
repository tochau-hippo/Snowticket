import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Tự động refresh 1 phút / lần
st_autorefresh(interval=60000, key="river_auto_fetch")

st.set_page_config(page_title="STNK - Mã Đáo Thành Công", page_icon="🐎", layout="wide")

st.title("📊 Dashboard Theo Dõi Vé (Live)")
st.caption("Sự kiện: Minishow MÃ ĐÁO THÀNH CÔNG - Neko Lê x S.T Sơn Thạch")

# ==========================================
WORKER_URL = "https://tatnienriver.chinmuoi.workers.dev" 
# ==========================================

if "toasted_zones" not in st.session_state:
    st.session_state.toasted_zones = set()

# Giờ mở bán cố định
OPENING_TIME_STR = "12:00:00 26/10/2026"
opening_dt = datetime.strptime(OPENING_TIME_STR, "%H:%M:%S %d/%m/%Y")

def calc_soldout_minutes(so_time_str):
    try:
        so_dt = datetime.strptime(so_time_str, "%H:%M:%S %d/%m/%Y")
        diff_mins = (so_dt - opening_dt).total_seconds() / 60
        if diff_mins < 0: return "Nội bộ/Pre-sale"
        elif diff_mins < 1: return "Chưa tới 1 phút"
        else: return f"{int(diff_mins)} phút"
    except:
        return "N/A"

def status_label(status_code):
    labels = {1: "Chưa bán", 2: "Tạm lock", 3: "Sold", 4: "Lock", 5: "Đang TT"}
    return labels.get(status_code, f"Lỗi ({status_code})")

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
    sold_out_times = data.get("official_sold_out", {})
    anomaly_log = data.get("anomaly_log", [])

    # Bắn pop-up góc màn hình
    for z in zones:
        z_name = z["name"]
        if z_name in sold_out_times and z_name not in st.session_state.toasted_zones:
            st.toast(f"🎇 Cháy vé: Đã SOLD OUT zone {z_name}!", icon="🔥")
            st.session_state.toasted_zones.add(z_name)
        elif z_name not in sold_out_times and z_name in st.session_state.toasted_zones:
            st.session_state.toasted_zones.remove(z_name)

    # Hiệu ứng bong bóng toàn màn hình
    if "ALL_SHOW" in sold_out_times:
        so_str = sold_out_times["ALL_SHOW"]
        record_time = calc_soldout_minutes(so_str)
        if "ALL_SHOW" not in st.session_state.toasted_zones:
            st.balloons() 
            st.toast(f"🏆 KỶ LỤC! SHOW ĐÃ SOLD OUT TRONG {record_time}!", icon="🎉")
            st.session_state.toasted_zones.add("ALL_SHOW")
        st.success(f"🎆 **TRẠNG THÁI: SOLD OUT TOÀN BỘ SHOW** LÚC {so_str} (KỶ LỤC: **{record_time}** KỂ TỪ KHI MỞ BÁN) 🎆")
    else:
        if "ALL_SHOW" in st.session_state.toasted_zones:
            st.session_state.toasted_zones.remove("ALL_SHOW")
        st.info(f"⏳ **TRẠNG THÁI:** ĐANG BÁN ... (Giờ mở cửa: {OPENING_TIME_STR})")

    st.markdown(f"**⏱ Dữ liệu cập nhật lúc:** `{last_check}`")

    col1, col2, col3 = st.columns(3)
    # Tự động cộng tổng toàn bộ số vé của tất cả các zone (không sót 1 vé nào)
    t_total = sum([z.get("total", 0) for z in zones])
    col1.metric("🎫 Tổng quy mô rạp", t_total)
    col2.metric("🔥 Tổng ghế đã chốt", t_sold)
    col3.metric("✅ Ghế còn trống", t_avail)
    
    st.divider()
    left_col, _col = st.columns([3.5, 6.5])

    st.divider()
    
    # Chia tỷ lệ: Bên trái (Lịch sử) chiếm 35%, Bên phải (Tình trạng) chiếm 65%
    left_col, right_col = st.columns([3.5, 6.5])

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
        
        # --- BẢO HIỂM CHỐNG BẢNG TRẮNG KHI CHƯA MỞ BÁN ---
        # Khi show chưa mở, API nhả mảng rỗng. Bơm data mặc định để giữ form bảng.
        if not zones:
            zones = [
                
                {"name": "RIVER (Standard)", "price": 850000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0},
                {"name": "FLOW (Pre)", "price": 1250000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0},
                {"name": "IN (VIP)", "price": 1750000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0},
                {"name": "YOU (SVIP)", "price": 2350000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0}
            ]
        # ------------------------------------------------

        for z in zones:
            z_name = z["name"]
            if z_name in sold_out_times:
                rec = calc_soldout_minutes(sold_out_times[z_name])
                z["sold_out_at"] = f"🔥 {sold_out_times[z_name]} ({rec})"
            else:
                # Nếu tổng vé = 0 thì báo "Chờ mở bán", ngược lại báo "Đang bán"
                z["sold_out_at"] = "Đang bán" if z.get("total", 0) > 0 else "Chờ mở bán"

        df_zones = pd.DataFrame(zones)

        for col in ["s1", "s2", "s3", "s4", "s5"]:
            if col not in df_zones.columns:
                df_zones[col] = 0

        df_zones = df_zones.rename(columns={
            "name": "Khu", "price": "Giá", "total": "Tổng", 
            "s1": "Chưa bán", 
            "s2": "Tạm lock", 
            "s3": "Sold", 
            "s4": "Lock", 
            "s5": "Đang TT",
            "sold_out_at": "Trạng thái"
        })
        
        # Đã sắp xếp lại thứ tự cột m yêu cầu
        df_zones = df_zones[["Khu", "Chưa bán", "Đang TT", "Sold", "Tạm lock", "Lock", "Trạng thái"]]
        
        # Code căn giữa (center) các cột số
        st.dataframe(
            df_zones, 
            use_container_width=True, 
            hide_index=True, 
            height=400,
            column_config={
                "Chưa bán": st.column_config.NumberColumn(alignment="center"),
                "Đang TT": st.column_config.NumberColumn(alignment="center"),
                "Sold": st.column_config.NumberColumn(alignment="center"),
                "Tạm lock": st.column_config.NumberColumn(alignment="center"),
                "Lock": st.column_config.NumberColumn(alignment="center")
            }
        )
        
    st.divider()
    st.subheader("🕵️ Lịch sử biến động trạng thái bất thường")
    st.caption("Ghi nhận các ghế bị Admin hold, BTC khoá, huỷ vé lậu, v.v. (Ngoài lộ trình 1 -> 5 -> 3)")
    
    if anomaly_log:
        for anomaly in anomaly_log:
            anomaly["from_label"] = status_label(anomaly["from"])
            anomaly["to_label"] = status_label(anomaly["to"])
            
        df_anomaly = pd.DataFrame(anomaly_log).rename(columns={
            "time": "Thời gian",
            "zone": "Khu vực",
            "seat": "Mã ghế",
            "from_label": "Từ trạng thái",
            "to_label": "Sang trạng thái"
        })
        df_anomaly = df_anomaly[["Thời gian", "Khu vực", "Mã ghế", "Từ trạng thái", "Sang trạng thái"]]
        st.dataframe(df_anomaly, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có hành vi nhảy trạng thái lạ nào bị phát hiện.")
