import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Thống kê vé", layout="centered")
st.title("📊 Bảng theo dõi vé Ticketbox")

token_input = st.text_input("🔑 Dán Access Token mới vào đây (Nếu không nhập sẽ dùng token mặc định dưới code):", type="password")

# ==========================================
DEFAULT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJpZGVudGl0eS50aWNrZXRib3gudm4iLCJhdWQiOlsiYXBpLnRpY2tldGJveC52biJdLCJleHAiOjE3OTE4MTYwMjcsImlhdCI6MTc5MTgxNTkwNywiZGV2aWNlX2lkIjoiN2EyNjA3YjI3MWI5ZjU5YjliZTczYjNjOWNhMTU3ZmYiLCJ1c2VyX2lkIjozMzk4MzkzLCJlbWFpbCI6ImxlaGFwaHVvbmc1MTBAZ21haWwuY29tIiwibmFtZSI6IlBoxrDGoW5nIEzDqiIsInBob25lIjoiKzg0OTAzMTk5ODI1IiwicGxhdGZvcm0iOiJ3ZWIiLCJzZXNzaW9uX2lkIjoiNDI1NmZlYmUtYzlkYy00ZWVmLTllNDMtMzNlZGI3MmMyYmZlIiwia2luZCI6ImFjY2Vzc190b2tlbiJ9.bx5mR3jZrJwWuzoG6u50g4sM4q1AiIoGHriZupS2Mq_kDzarLD8rT5wPIOl-FhiP8P_Nc6BNCDLkH_zRX9wE8XIPr7wEzQouH4meCrU6uKQJZ2Tz0cs5skeAy6GTuszqETJp3XR_v1HOWEvXtaxHt12uYGcOLK0Jo7OwD09AWlP62xpzf8Sr5SMNZEoFDEKaXNjC_lpxCmgHI2ZkdvBwBiAm-SwdTF6BqknNJmtrrjPNF9d1JRby4m5kYtg_J21Qw6Cso-mLKJ_bH_JqL3o6a4glbya4sj-6pCSygXpNgLjMJgXe_GTH2LTXBh-SAM2ayW18NOSiJk23HIDYEtBu7g"
# ==========================================

active_token = token_input.strip() if token_input.strip() else DEFAULT_TOKEN
API_URL = "https://api-v2.ticketbox.vn/event/api/v1/events/showings/41775904473808/seatmap"
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7",
    "content-type": "application/json",
    "origin": "https://ticketbox.vn",
    "referer": "https://ticketbox.vn/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
    "x-tb-access-token": active_token  
}

@st.cache_data(ttl=30)
def fetch_ticket_data(_token):
    try:
        current_headers = HEADERS.copy()
        current_headers["x-tb-access-token"] = _token
        response = requests.get(API_URL, headers=current_headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Lỗi kết nối API (Có thể Token đã hết hạn): {e}")
        return None

data = fetch_ticket_data(active_token)

if data:
    sections = data.get("data", {}).get("result", {}).get("sections", [])
    stats = []
    
    # Biến debug dành cho m để kiểm tra có bao nhiêu mã status xuất hiện
    debug_statuses = {}
    
    for sec in sections:
        if sec.get("isStage"): 
            continue
            
        name = sec.get("name", "Unknown")
        all_seats = []
        
        if "seats" in sec:
            all_seats.extend(sec["seats"])
        elif "rows" in sec:
            for row in sec["rows"]:
                if "seats" in row:
                    all_seats.extend(row["seats"])
        
        if all_seats:
            total = len(all_seats)
            
            for s in all_seats:
                st_val = str(s.get("status", "None"))
                debug_statuses[st_val] = debug_statuses.get(st_val, 0) + 1

            # LOGIC MỚI: Định nghĩa status = 1 là ghế "Đang trống"
            available = sum(1 for s in all_seats if str(s.get("status")) == "1")
            sold = total - available
            
            stats.append({
                "Hạng Vé / Khu Vực": name, 
                "Tổng vé": total, 
                "Đã bán": sold, 
                "Còn trống": available
            })

    if stats:
        df = pd.DataFrame(stats)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🎫 Tổng vé", df["Tổng vé"].sum())
        col2.metric("🔥 Đã bán", df["Đã bán"].sum())
        col3.metric("✅ Còn trống", df["Còn trống"].sum())
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        with st.expander("🛠 Dành cho Dev: Thống kê mã status thực tế từ API"):
            st.info("Ticketbox đang phân loại ghế bằng các mã sau (Số lượng ghế tương ứng). Nếu data đếm sai, m chỉ cần đối chiếu mảng này để sửa lại logic đếm `status == '?'` ở trên code.")
            st.json(debug_statuses)
    else:
        st.warning("Không tìm thấy dữ liệu ghế.")

if st.button("🔄 Làm mới dữ liệu"):
    fetch_ticket_data.clear()
    st.rerun()
