import streamlit as st
import requests
import pandas as pd
from xml.etree import ElementTree
from datetime import datetime, timedelta
from urllib.parse import quote

st.set_page_config(page_title="台電新聞輿情u272260", page_icon="⚡", layout="centered")
st.title("⚡️新聞輿情")
st.caption("115.6.16-u272260-優化內文檢索深度")
keywords = st.text_input("請輸入關鍵字（空格=且，逗號=或）", "基隆 台電")
hours = st.number_input("請輸入時間範圍（過去幾小時內）", min_value=1, max_value=720, value=24, step=1)
st.markdown("搜尋深度：全網域檢索")

if st.button("開始", type="primary"):
    keyword_groups = [g.strip() for g in keywords.replace('，', ',').split(',') if g.strip()]
    all_news = []
    now_tw = datetime.now()
    time_limit_tw = now_tw - timedelta(hours=int(hours))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }

    with st.spinner("搜集中，請稍候..."):
        for group in keyword_groups:
            check_words = group.split() 
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
                        pub_date_gmt = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        # 時區標準
                        pub_date_tw = pub_date_gmt + timedelta(hours=8)
                        # 時間過濾
                        if pub_date_tw > time_limit_tw:
                            link = item.find('link').text if item.find('link') is not None else ""
                            source_el = item.find('source')
                            source = source_el.text if source_el is not None else "網路"
                            display_time = pub_date_tw.strftime('%Y-%m-%d %H:%M')
                            
                            all_news.append({
                                "搜尋組": group,
                                "時間": display_time,
                                "媒體": source,
                                "新聞標題": title,
                                "內文狀態": "全網域關聯檢索",
                                "連結": link
                            })
            except Exception as e:
                st.error(f"分析組别 [{group}] 時發生異常")

    # 顯示結果
    if all_news:
        # 去除重複
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
