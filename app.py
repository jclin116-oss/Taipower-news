import streamlit as st
import requests
import pandas as pd
from xml.etree import ElementTree
from datetime import datetime, timedelta
from urllib.parse import quote
from bs4 import BeautifulSoup  # 額外引入 BeautifulSoup 來解析內文 HTML

# 網頁基本設定（手機版優化）
st.set_page_config(page_title="台電新聞輿情u272260", page_icon="⚡", layout="centered")

st.title("⚡️新聞輿情")
st.caption("115.6.15/新增支援內文檢索")

# 建立網頁輸入欄位
keywords = st.text_input("請輸入關鍵字（空格=且，逗號=或）", "基隆 台電")
hours = st.slider("請選擇時間範圍（過去幾小時內）", min_value=1, max_value=120, value=24)

# 新增一個選項：讓使用者決定要「只比對標題」還是「深度比對內文」
search_mode = st.radio("搜尋深度", ["檢索標題 (速度快)", "檢索標題及內文（測試）"], horizontal=True)

if st.button("開始", type="primary"):
    keyword_groups = [g.strip() for g in keywords.replace('，', ',').split(',') if g.strip()]
    all_news = []
    time_limit = datetime.now() - timedelta(hours=hours)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }

    with st.spinner("搜集中，請稍候..."):
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
                        link = item.find('link').text if item.find('link') is not None else ""
                        
                        pub_date_str = item.find('pubDate').text
                        pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        
                        # 優先篩選時間，符合時間的才點進去抓內文，節省時間
                        if pub_date > time_limit:
                            
                            is_match = False
                            content_snippet = "未開啟內文檢索"
                            
                            # 模式 1：僅比對標題
                            if "僅比對標題" in search_mode:
                                if any(word.lower() in title.lower() for word in check_words):
                                    is_match = True
                            
                            # 模式 2：深度比對內文
                            else:
                                # 先看標題有沒有，標題有就直接算命中
                                if any(word.lower() in title.lower() for word in check_words):
                                    is_match = True
                                else:
                                    # 標題沒有，點進去原始新聞網頁抓內文
                                    try:
                                        # 請求原始新聞頁面
                                        art_res = requests.get(link, timeout=5, headers=headers)
                                        if art_res.status_code == 200:
                                            # 使用 BeautifulSoup 撈出網頁內所有文字
                                            soup = BeautifulSoup(art_res.content, 'html.parser')
                                            # 移除不必要的 script 和 style 標籤
                                            for script in soup(["script", "style"]):
                                                script.decompose()
                                            article_text = soup.get_text()
                                            
                                            # 檢查所有關鍵字是否都在內文中
                                            if any(word.lower() in article_text.lower() for word in check_words):
                                                is_match = True
                                                # 擷取一段包含關鍵字的內文摘要（選填）
                                                content_snippet = article_text.replace('\n', ' ').strip()[:100] + "..."
                                    except:
                                        pass # 遇到部分媒體阻擋爬蟲時跳過
                            
                            # 確定命中後才寫入報表
                            if is_match:
                                source_el = item.find('source')
                                source = source_el.text if source_el is not None else "網路"
                                tw_time = (pub_date + timedelta(hours=8)).strftime('%m-%d %H:%M')
                                
                                all_news.append({
                                    "搜尋組": group,
                                    "時間": tw_time,
                                    "媒體": source,
                                    "新聞標題": title,
                                    "內文片段": content_snippet,
                                    "連結": link
                                })
            except Exception as e:
                st.error(f"分析組别 [{group}] 時發生異常")

    # 顯示結果
    if all_news:
        df = pd.DataFrame(all_news)
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
