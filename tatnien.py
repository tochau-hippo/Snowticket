import streamlit as st
import pandas as pd
import requests
import html
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from celebrations import new_milestones, render_celebration
​
st.set_page_config(page_title="STNK - Mã Đáo Thành Công", page_icon="🐎", layout="wide")
​
# Theme assets are resolved relative to this file, not the working directory.
from pathlib import Path
import base64
​
ASSETS = Path(__file__).resolve().parent / "assets"
​
@st.cache_data(show_spinner=False)
def asset_data_uri(filename, mime):
    path = ASSETS / filename
    if not path.is_file():
        return ""
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
​
def apply_show_theme():
    desktop = asset_data_uri("background-desktop.webp", "image/webp")
    mobile = asset_data_uri("background-mobile.webp", "image/webp") or desktop
    logo = asset_data_uri("show-logo.png", "image/png")
    st.markdown("""
    <style>
    :root {color-scheme: dark;}
    [data-testid="stAppViewContainer"] {background: #300504; isolation:isolate;}
    [data-testid="stAppViewContainer"]::before {
        content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
        background-color:#300504;
        background-image:linear-gradient(rgba(22,2,2,.16),rgba(22,2,2,.30)),url("DESKTOP_ASSET");
        background-size:cover; background-position:center center; background-repeat:no-repeat;
    }
    [data-testid="stMain"], [data-testid="stSidebar"] {background:transparent;}
    [data-testid="stHeader"] {background:rgba(35,3,3,.88);}
    .block-container {max-width:1480px; padding:3.5rem 3rem 3rem;}
    .show-brand {text-align:center; margin:0 auto 2rem;}
    .show-brand img {display:block; width:min(420px,78%); height:auto; margin:0 auto 1rem;}
    .show-brand .show-subtitle {color:#f2e2c4; font-size:16px; line-height:1.6; margin:0;}
    .show-brand .show-eyebrow {color:#d9b85e; letter-spacing:.16em; font-size:14px; margin:.5rem 0;}
    h1,h2,h3 {font-family:Georgia,"Times New Roman",serif; color:#f2e2b9;}
    h1 {font-size:clamp(1.6rem,3vw,2.2rem)!important;}
    h2,h3 {line-height:1.35!important;}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:#e0cbb2!important; opacity:1;}
    [data-testid="stMetric"] {background:rgba(38,5,5,.94); border:1px solid #866634;
        border-radius:12px; padding:20px 24px; min-height:128px;}
    [data-testid="stMetricLabel"] {color:#eedbc0;}
    [data-testid="stMetricValue"] {color:#f4db92; font-variant-numeric:tabular-nums;}
    [data-testid="stAlert"] {background:rgba(38,5,5,.95); border:1px solid #866634; border-radius:10px;}
    [data-testid="stAlertContainer"] {background:rgba(38,5,5,.96)!important;}
    [data-testid="stAlert"] p {color:#f5e8d2;}
    [data-testid="stDataFrame"] {border:1px solid #866634; border-radius:10px; overflow:hidden;}
    hr {border-color:rgba(217,184,94,.32)!important; margin:1.8rem 0!important;}
    button {min-height:44px;}
    button:focus-visible,a:focus-visible {outline:2px solid #f4db92; outline-offset:3px;}
    @media (max-width:767px) {
        [data-testid="stAppViewContainer"]::before {
            background-image:linear-gradient(rgba(22,2,2,.20),rgba(22,2,2,.35)),url("MOBILE_ASSET");
        }
        .block-container {padding:3.5rem 1.1rem 2rem;}
        .show-brand {margin-bottom:1.5rem;}
        .show-brand img {width:min(340px,94%);}
        .show-brand .show-subtitle {font-size:14px;}
        .show-brand .show-eyebrow {font-size:14px; letter-spacing:.1em;}
        [data-testid="stMetric"] {padding:16px 20px; min-height:110px;}
        [data-testid="stHorizontalBlock"] {flex-direction:column; gap:1rem;}
        [data-testid="stColumn"] {width:100%!important; flex:1 1 auto!important; min-width:0!important;}
    }
    @media (prefers-reduced-motion:reduce) {
        *,*::before,*::after {animation:none!important; transition:none!important; scroll-behavior:auto!important;}
    }
    </style>
    """.replace("DESKTOP_ASSET", desktop).replace("MOBILE_ASSET", mobile), unsafe_allow_html=True)
    if logo:
        st.markdown(f'<div class="show-brand"><img src="{logo}" alt="Mã Đáo Thành Công">'
                    '<p class="show-subtitle">NEKO LÊ · S.T SƠN THẠCH</p>'
                    '<p class="show-eyebrow">THEO DÕI VÉ · MINISHOW</p></div>', unsafe_allow_html=True)
    else:
        st.title("Mã Đáo Thành Công")
        st.caption("Neko Lê · S.T Sơn Thạch")
​
def format_history_detail(detail):
    """Escape API text, then decorate signed counts only; never change stored data."""
    text = html.escape(str(detail or ""))
    def marker(match):
        up = match.group(1) == "+"
        count = match.group(2)
        cls, arrow, label = ("up", "▲", "Tăng") if up else ("down", "▼", "Giảm")
        return (f'<span class="history-delta-{cls}" role="img" aria-label="{label} {count} vé">'
                f'<span aria-hidden="true">{arrow} {count}</span></span>')
    return re.sub(r"(?<![\w\d])([+\-−])(\d+)(?!\d)", marker, text)
​
​
def history_table_html(history):
    rows = []
    for row in history:
        time = html.escape(str(row.get("time", "")))
        sold_count = html.escape(str(row.get("sold", "")))
        available = html.escape(str(row.get("available", "")))
        detail = format_history_detail(row.get("detail", ""))
        rows.append(f'<tr><td class="history-time">{time}</td>'
                    f'<td class="history-number">{sold_count}</td>'
                    f'<td class="history-number">{available}</td><td>{detail}</td></tr>')
    return '''<style>
.history-legend {font:14px/1.5 system-ui,sans-serif;color:#e0cbb2;margin:0 0 10px;}
.history-delta-up {color:#72D99B!important;white-space:nowrap;font-weight:650;}
.history-delta-down {color:#FF8B87!important;white-space:nowrap;font-weight:650;}
.history-panel {height:400px;max-width:100%;overflow:auto;background:#270807;
    border:1px solid #866634;border-radius:10px;scrollbar-color:#866634 #270807;}
.history-panel:focus-visible {outline:2px solid #f4db92;outline-offset:3px;}
.history-panel table.history-grid {border-collapse:separate;border-spacing:0;width:100%;min-width:560px;
    font:14px/1.5 system-ui,sans-serif;color:#F5E8D2;text-align:left;}
.history-panel .history-grid th {position:sticky;top:0;background:#300B09;color:#efddc6;z-index:1;
    font-weight:500;text-align:left;white-space:nowrap;}
.history-panel .history-grid th,.history-panel .history-grid td {
    padding:12px 10px;border-right:1px solid #54302a;border-bottom:1px solid #54302a;vertical-align:top;}
.history-panel .history-grid th:last-child,.history-panel .history-grid td:last-child {border-right:0;}
.history-panel .history-grid .history-time {white-space:nowrap;}
.history-panel .history-grid .history-number {text-align:right;font-variant-numeric:tabular-nums;}
.history-panel .history-grid td:last-child {min-width:200px;overflow-wrap:anywhere;}
</style>
<div class="history-legend"><span class="history-delta-up">▲ Tăng</span> · <span class="history-delta-down">▼ Giảm</span> · Đơn vị: vé</div>
<div class="history-panel" role="region" aria-label="Bảng lịch sử chốt đơn, có thể cuộn" tabindex="0">
<table class="history-grid"><thead><tr><th scope="col">Thời gian</th><th scope="col">Đã bán</th><th scope="col">Trống</th><th scope="col">Chi tiết thay đổi</th></tr></thead>
<tbody>''' + "".join(rows) + '</tbody></table></div>'
​
​
apply_show_theme()
​
# Tự động refresh 1 phút / lần
st_autorefresh(interval=60000, key="river_auto_fetch")
​
st.subheader("Dashboard theo dõi vé")

​
# ==========================================
WORKER_URL = "https://tatnienriver.chinmuoi.workers.dev" 
# ==========================================
​
# Session-local: reloading the tab/new session can replay the welcome.
celebration_kind = None
celebration_message = ""
if not st.session_state.get("gold_welcome_seen", False):
    celebration_kind = "welcome"
    st.session_state.gold_welcome_seen = True
if "gold_seen_marks" not in st.session_state:
    st.session_state.gold_seen_marks = set()
​
# Giờ mở bán cố định
OPENING_TIME_STR = "12:00:00 26/10/2026"
opening_dt = datetime.strptime(OPENING_TIME_STR, "%H:%M:%S %d/%m/%Y")
​
def calc_soldout_minutes(so_time_str):
    try:
        so_dt = datetime.strptime(so_time_str, "%H:%M:%S %d/%m/%Y")
        diff_mins = (so_dt - opening_dt).total_seconds() / 60
        if diff_mins < 0: return "Nội bộ/Pre-sale"
        elif diff_mins < 1: return "Chưa tới 1 phút"
        else: return f"{int(diff_mins)} phút"
    except:
        return "N/A"
​
def status_label(status_code):
    labels = {1: "Chưa bán", 2: "Tạm lock", 3: "Sold", 4: "Lock", 5: "Đang TT"}
    return labels.get(status_code, f"Lỗi ({status_code})")
​
def get_data():
    try:
        response = requests.get(WORKER_URL, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    except:
        return None
​
data = get_data()
​
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
​
    # First valid snapshot is a baseline: old sold-out marks do not fire on entry.
    previous_marks = st.session_state.get("gold_previous_marks")
    fresh_marks = new_milestones(sold_out_times, previous_marks, st.session_state.gold_seen_marks)
    st.session_state.gold_previous_marks = dict(sold_out_times)
    new_zones = [name for name in fresh_marks if name != "ALL_SHOW"]
    if "ALL_SHOW" in fresh_marks:
        celebration_kind = "show"
        celebration_message = "Toàn bộ show Mã Đáo Thành Công đã sold out!"
        if new_zones:
            celebration_message += " Hạng vé: " + ", ".join(new_zones)
    elif new_zones:
        celebration_kind = "zone"
        celebration_message = "Đã sold out hạng vé: " + ", ".join(new_zones)
​
    # Persistent status is separate from the temporary 5-second notice.
    if "ALL_SHOW" in sold_out_times:
        so_str = sold_out_times["ALL_SHOW"]
        record_time = calc_soldout_minutes(so_str)
        st.success(f"✦ SHOW ĐÃ SOLD OUT lúc {so_str} · {record_time} kể từ khi mở bán")
    else:
        st.info(f"⏳ **TRẠNG THÁI:** ĐANG BÁN ... (Giờ mở cửa: {OPENING_TIME_STR})")
​
    st.markdown(f"**⏱ Lần kiểm tra Worker:** `{last_check}`")
​
    col1, col2, col3 = st.columns(3)
    # Tự động cộng tổng toàn bộ số vé của tất cả các zone (không sót 1 vé nào)
    t_total = sum([z.get("total", 0) for z in zones])
    col1.metric("🎫 Tổng quy mô rạp", t_total)
    col2.metric("🔥 Tổng ghế đã chốt", t_sold)
    col3.metric("✅ Ghế còn trống", t_avail)
    
    st.divider()
    
    # Chia tỷ lệ: Bên trái (Lịch sử) chiếm 35%, Bên phải (Tình trạng) chiếm 65%
    left_col, right_col = st.columns([3.5, 6.5])
​
    with left_col:
        st.subheader("📋 Lịch sử chốt đơn")
        if history:
            st.markdown(history_table_html(history), unsafe_allow_html=True)
        else:
            st.info("Chưa có biến động vé.")
​
    with right_col:
        st.subheader("🎯 Tình trạng từng hạng vé")
        
        # --- BẢO HIỂM CHỐNG BẢNG TRẮNG KHI CHƯA MỞ BÁN ---
        # Khi show chưa mở, API nhả mảng rỗng. Bơm data mặc định để giữ form bảng.
        if not zones:
            zones = [
                
                {"name": "RIVER (Standard)", "price": 850000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0},
                {"name": "FLOWS (Pre)", "price": 1250000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0},
                {"name": "IN (VIP)", "price": 1750000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0},
                {"name": "YOU (SVIP)", "price": 2350000, "total": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0, "sold": 0, "available": 0}
            ]
        # ------------------------------------------------
​
        for z in zones:
            z_name = z["name"]
            if z_name in sold_out_times:
                rec = calc_soldout_minutes(sold_out_times[z_name])
                z["sold_out_at"] = f"🔥 {sold_out_times[z_name]} ({rec})"
            else:
                # Nếu tổng vé = 0 thì báo "Chờ mở bán", ngược lại báo "Đang bán"
                z["sold_out_at"] = "Đang bán" if z.get("total", 0) > 0 else "Chờ mở bán"
​
        df_zones = pd.DataFrame(zones)
​
        for col in ["s1", "s2", "s3", "s4", "s5"]:
            if col not in df_zones.columns:
                df_zones[col] = 0
​
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
                "Chưa bán": st.column_config.NumberColumn(format="%d"),
                "Đang TT": st.column_config.NumberColumn(format="%d"),
                "Sold": st.column_config.NumberColumn(format="%d"),
                "Tạm lock": st.column_config.NumberColumn(format="%d"),
                "Lock": st.column_config.NumberColumn(format="%d")
            }
        )
        
    st.divider()
    st.subheader("🕵️ Lịch sử biến động trạng thái bất thường")
    st.caption("Các chuyển trạng thái ngoài luồng được Worker đánh dấu; không tự xác định nguyên nhân hoặc hành vi gian lận.")
    
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
​
# One effect per update; show milestone takes priority over simultaneous zones.
if celebration_kind:
    render_celebration(celebration_kind, celebration_message)
​
