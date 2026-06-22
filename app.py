import requests
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _match_date(self, text, date_variants):
        """檢查文本內是否包含任何一種日期變體"""
        return any(v in text for v in date_variants)

    def get_ey_schedule(self, date_variants):
        """改用 RSS 抓取行政院行程"""
        # 行政院首長行程 RSS 服務網址
        url = "https://www.ey.gov.tw/RSS/Program/ECE410333003326E"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": "行政院(RSS)", "行程內容": f"RSS站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]

            res.encoding = 'utf-8'
            # 關鍵：使用 xml 解析器處理 RSS 結構
            soup = BeautifulSoup(res.text, 'xml')
            schedules = []
            
            # RSS 的標準標準節點為 <item>
            items = soup.find_all('item')
            
            for item in items:
                title = item.find('title').get_text().strip() if item.find('title') else ""
                description = item.find('description').get_text().strip() if item.find('description') else ""
                
                full_text = f"{title} {description}"
                
                # 行項過濾與日期比對
                if self._match_date(full_text, date_variants):
                    target = "行政院長" if "院長" in full_text and "副院長" not in full_text else ("行政副院長" if "副院長" in full_text else "行政院綜合")
                    schedules.append({
                        "官職": target,
                        "行程內容": title,
                        "時間/地點": description if description else "見內文"
                    })
            
            if not schedules:
                return [{"官職": "行政院(RSS)", "行程內容": "該日期在 RSS 饋送中無公開行程資料", "時間/地點": "-"}]
            return schedules
            
        except Exception as e:
            return [{"官職": "行政院(RSS)", "行程內容": f"RSS連線異常: {str(e)}", "時間/地點": "-"}]

    def get_president_schedule(self, date_variants):
        """抓取總統府行程並過濾日期"""
        url = "https://www.president.gov.tw/Page/37"
        target_name = "總統"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('li') or soup.select('.p-list-item')
            for item in items:
                text = " ".join(item.get_text(separator=" ").split())
                if text and len(text) > 10 and "頁面" not in text and "版權所有" not in text:
                    if self._match_date(text, date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": text,
                            "時間/地點": "詳見官網行程頁"
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網頁面無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

    def get_moea_schedule(self, date_variants):
        """抓取經濟部長行程並過濾日期"""
        url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
        target_name = "經濟部長"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('table tr')
            for item in items:
                tds = item.select('td')
                if len(tds) >= 2:
                    time_info = " ".join(tds[0].get_text(separator=" ").split())
                    content_info = " ".join(tds[1].get_text(separator=" ").split())
                    
                    full_text = f"{time_info} {content_info}"
                    if "暫無行程" in content_info or "無公開行程" in content_info:
                        continue
                        
                    if self._match_date(full_text, date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": content_info,
                            "時間/地點": time_info
                        })
                else:
                    text = " ".join(item.get_text(separator=" ").split())
                    if text and len(text) > 15 and self._match_date(text, date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": text,
                            "時間/地點": "見內文"
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網頁面無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]
