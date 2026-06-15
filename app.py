import streamlit as st
import requests
import pandas as pd
from xml.etree import ElementTree
from datetime import datetime, timedelta
from urllib.parse import quote

# 網頁基本設定（手機版優化）
st.set_page_config(page_title="台電輿情哨兵", page_icon="⚡", layout="centered")

st.title("⚡ 輿情採集控制台")
st.caption("Mentat 輿情哨兵 - 網頁行動版 v4.0")

# 建立直覺的網頁輸入欄位
keywords = st.text_input("請輸入關鍵字（空格=且，逗號=或）", "基隆 台電")
hours = st.slider("請選擇時間範圍（過去幾小時內）", min_value=1, max_value=72, value=24)

if st.button("🚀 開始採集輿情", type="primary"):
    keyword_groups = [g.strip() for g in keywords.replace('，', ',').split(',') if g.strip()]
    all_news = []
    time_limit = datetime.now() - timedelta(hours=hours)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }

    with st.spinner("網域數據採集中，請稍候..."):
        for group in keyword_groups:
            search_query = group.replace(' ', ' AND ')
            encoded_query = quote(search_query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            
            try:
                response = requests.get(url, timeout=15, headers=headers)
                if response.status_code == 200:
                    tree = ElementTree.fromstring(response.content)
                    check_words = group.split() 

                    for item in tree.findall('.//item'):
                        title = item.find('title').text if item.find('title') is not None else ""
                        
                        # 過濾機制
                        if any(word.lower() in title.lower() for word in check_words):
                            pub_date_str = item.find('pubDate').text
                            pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                            
                            if pub_date > time_limit:
                                link = item.find('link').text if item.find('link') is not None else ""
                                source_el = item.find('source')
                                source = source_el.text if source_el is not None else "網路"
                                tw_time = (pub_date + timedelta(hours=8)).strftime('%m-%d %H:%M')
                                
                                all_news.append({
                                    "搜尋組": group,
                                    "時間": tw_time,
                                    "媒體": source,
                                    "新聞標題": title,
                                    "連結": link
                                })
            except Exception as e:
                st.error(f"分析組别 [{group}] 時發生異常")

    # 顯示結果
    if all_news:
        df = pd.DataFrame(all_news)
        st.success(f"採集成功！共發現 {len(df)} 則完全符合條件的輿情訊息。")
        
        # 在手機網頁上渲染出漂亮的資料表格
        st.dataframe(df, use_container_width=True)
        
        # 轉換成 Excel 供使用者下載到手機
        # 為了簡化依賴關係，網頁版下載改為標準 CSV 格式
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 下載輿情報表 (CSV 檔案)",
            data=csv_data,
            file_name=f"輿情追蹤_{datetime.now().strftime('%m%d_%H%M')}.csv",
            mime='text/csv',
        )
    else:
        st.warning("❌ 當前時間範圍內，未發現完全符合關鍵字的新聞。")
