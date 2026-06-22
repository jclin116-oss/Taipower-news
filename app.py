import streamlit as st
import pandas as pd
from spiders import ScheduleSpider
from datetime import datetime

st.set_page_config(page_title="政府首長公開行程監測", layout="wide")

st.title("🏛️ 政府首長公開行程即時看板 (RSS 增強版)")

# --- 日期選擇器 ---
today = datetime.now().date()
selected_date = st.date_input("請選擇欲查詢的行程日期：", today)
date_str = selected_date.strftime("%Y-%m-%d")

# 建立多元日期字串格式，相容於 RSS 的文本過濾機制
roc_year = selected_date.year - 1911
date_variants = [
    date_str,                                      # 2026-06-22
    selected_date.strftime("%Y/%m/%d"),           # 2026/06/22
    f"{roc_year}年{selected_date.month}月{selected_date.day}日", # 115年6月22日
    f"{roc_year}/{selected_date.month:02d}/{selected_date.day:02d}", # 115/06/22
    f"{selected_date.month}月{selected_date.day}日" # 6月22日 (相容部分純月日格式)
]

st.caption(f"本系統已整合行政院 RSS 數據源。目前檢索日期：【{date_str}】。")

spider = ScheduleSpider()

if st.button("🔄 立即更新並篩選行程資料", type="primary"):
    with st.spinner(f"正在連線各部會數據源並篩選 {date_str} 資料..."):
        
        ey_data = spider.get_ey_schedule(date_variants)
        president_data = spider.get_president_schedule(date_variants)
        moea_data = spider.get_moea_schedule(date_variants)
        
        all_data = president_data + ey_data + moea_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            df['檢查時間'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            df = df[['官職', '時間/地點', '行程內容', '檢查時間']]
            
            st.success(f"{date_str} 資料篩選完成！")
            st.subheader(f"📅 {date_str} 行程列表")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載此日期行程報表 (CSV)",
                data=csv,
                file_name=f"gov_schedule_{date_str}.csv",
                mime="text/csv",
            )
        else:
            st.warning(f"未能成功獲取任何首長資料。")
else:
    st.info("請選擇日期並點擊上方按鈕開始查詢。")
