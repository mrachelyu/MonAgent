# backend/scraper/base_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

class BaseScraper:
    def __init__(self, config: dict):
        self.site_name = config.get("site_name")
        self.url = config.get("target_url")
        self.selectors = config.get("selectors", {})
        self.storage = config.get("storage", {})
        print(f"🕷️ 初始化爬蟲: {self.site_name} ({self.url})")

    def fetch_page(self):
        """抓取 HTML 頁面"""
        try:
            print(f"🔍 正在請求頁面: {self.url}")
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ 請求失敗: {e}")
            return None

    def parse_page(self, html):
        """解析 HTML 並擷取資料"""
        soup = BeautifulSoup(html, "html.parser")
        titles = [a.get_text(strip=True) for a in soup.select(self.selectors.get("title", ""))]
        prices = [p.get_text(strip=True) for p in soup.select(self.selectors.get("price", ""))]
        
        data = []
        for t, p in zip(titles, prices):
            data.append({"title": t, "price": p})
        return data

    def save_to_csv(self, data):
        """將結果儲存為 CSV"""
        path = Path(self.storage.get("path", "output.csv"))
        df = pd.DataFrame(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"💾 已儲存資料: {path}")

    def run(self):
        """完整執行流程"""
        html = self.fetch_page()
        if html:
            data = self.parse_page(html)
            self.save_to_csv(data)
            print(f"✅ {self.site_name} 抓取完成，共 {len(data)} 筆資料。")
