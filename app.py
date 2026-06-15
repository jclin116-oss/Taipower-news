import streamlit as st
import requests
import pandas as pd
from xml.etree import ElementTree
from datetime import datetime, timedelta
from urllib.parse import quote

# 網頁基本設定（手機版優化）
st.set_page_config(page_title="台電新聞輿情u272260", page_icon="⚡", layout="centered")

st.title("⚡️新聞輿情")
st.caption("115.6.15-新增支援內文深度檢索")

# 建立網頁輸入欄位
keywords = st.text_input("請輸入關鍵字（空格=且，逗號=或）", "基隆 台電")
hours = st.slider("請選擇時間範圍（過去幾小時內）", min_value=1, max_value=120, value=24)

# 保留你的介面文字
search_mode = st.radio("搜尋深度版本", ["檢索標題及內文"], horizontal=True)

if st.button("開始", type="primary"):
    keyword_groups = [g.strip() for g in keywords.replace('，', ',').split(',') if g.strip()]
    all_news = []
    time_limit = datetime.now() - timedelta(hours=hours)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }

    with st.spinner("搜集中，請稍候..."):
        for group in keyword_groups:
            check_words = group.split() 
            
            # 根據選擇的搜尋深度，動態調整送給 Google 的搜尋指令
            if "檢索標題及內文" in search_mode:
                # 轉成 intext:"字A" AND intext:"字B" 的內文搜尋指令
                search_query = " AND ".join([f'intext:"{word}"' for word in check_words])
            else:
                # 一般的字詞「且」搜尋
                search_query = group.replace(' ', ' AND ')
                
            encoded_query = quote(search_query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            
            try:
                response = requests.get(url, timeout=15, headers=headers)
                if response.status_code == 200:
                    tree = ElementTree.fromstring(response.content)

                    for item in tree.findall('.//item'):
                        title = item.find('title').text if item.find('title') is not None else ""
                        pub_date_str = item.find('pubDate').text
                        pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        
                        # 優先篩選時間
                        if pub_date > time_limit:
                            link = item.find('link').text if item.find('link') is not None else ""
                            source_el = item.find('source')
                            source = source_el.text if source_el is not None else "網路"
                            tw_time = (pub_date + timedelta(hours=8)).strftime('%m-%d %H:%M')
                            
                            content_snippet = "已由Google完成內文檢索" if "檢索標題及內文" in search_mode else "未開啟內文檢索"
                            
                            all_news.append({
                                "搜尋組": group,
                                "時間": tw_time,
                                "媒體": source,
                                "新聞標題": title,
                                "內文狀態": content_snippet,
                                "連結": link
                            })
            except Exception as e:
                st.error(f"分析組别 [{group}] 時發生異常")

    # 顯示結果
    if all_news:
        # 去除重複標題的新聞
        df = pd.DataFrame(all_news).drop_duplicates(subset=["新聞標題"])
        st.success(f"搜集成功！共發現 {len(df)} 則符合條件的輿情訊息。")
        st.dataframe(df, use_container_width=True)
        
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下載報表 (CSV 檔案)",
            data=csv_data,
            file_name=f"新聞追蹤_{datetime.now().strftime('%m%d_%H%M')}.csv",
            mime='text/csv',
        )
    else:
        st.warning("時間範圍內，未發現符合關鍵字的新聞。")