# backend/scraper/base_scraper.py
import re, time, requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from backend.scraper.utils import clean_url, is_allowed_by_robots

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
)

class BaseScraper:
    def __init__(self, config: dict):
        self.site_name = config.get("site_name")
        self.url = config.get("target_url")
        self.strip_query_params = config.get("strip_query_params", True)
        self.parse_mode = config.get("parse_mode", "generic")
        self.storage = config.get("storage", {})
        print(f"🕷️ Initializing scraper: {self.site_name} ({self.url})")

    def fetch_page(self):
        u = clean_url(self.url, self.strip_query_params)
        if not is_allowed_by_robots(u):
            raise PermissionError(f"Blocked by robots.txt: {u}")

        headers = {"User-Agent": DEFAULT_UA}
        print(f"🔍 GET {u}")
        r = requests.get(u, headers=headers, timeout=15)
        r.raise_for_status()
        time.sleep(1.2)  # Polite delay
        return r.text

    def parse_page(self, html):
        if self.parse_mode == "clubinject_units":
            return self._parse_clubinject_units(html)
        return []

    def _parse_clubinject_units(self, html):
        """
        Robust text-based parsing: Extract n Units $x, membership fees, address/phone/email.
        Avoid relying on volatile CSS classes (Squarespace frequently updates).
        """
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

        # 1) Units & Price (e.g., "20 Units $150.80")
        unit_price = []
        for m in re.finditer(r"(\d+)\s*Units?\s*\$([0-9]+(?:\.[0-9]{2})?)", text, flags=re.I):
            unit_count = int(m.group(1))
            price = float(m.group(2))
            unit_price.append({"units": unit_count, "price": price})

        # 2) Membership fee (e.g., "just $9.72/month")
        member_fee = None
        mm = re.search(r"\$([0-9]+(?:\.[0-9]{2})?)\s*/\s*month", text, flags=re.I)
        if mm:
            member_fee = float(mm.group(1))

        # 3) Contact information
        # Phone (480) 576-2246
        phone = None
        ph = re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", text)
        if ph: phone = ph.group(0)

        # Email
        email = None
        em = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if em: email = em.group(0)

        # Address (capture Scottsdale AZ line)
        address = None
        for line in text.splitlines():
            if "Scottsdale" in line and ("AZ" in line or "Arizona" in line):
                address = line.strip()
                break

        # Combine into a tabular list (one row per plan)
        rows = []
        for up in unit_price:
            rows.append({
                "location": "Scottsdale",
                "units": up["units"],
                "price": up["price"],
                "member_fee_month": member_fee,
                "phone": phone,
                "email": email,
                "address": address,
                "source_url": clean_url(self.url, True),
            })
        return rows

    def save_to_csv(self, data):
        path = Path(self.storage.get("path", "output.csv"))
        df = pd.DataFrame(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path, df

    def run(self):
        html = self.fetch_page()
        data = self.parse_page(html)
        path, df = self.save_to_csv(data)
        print(f"✅ {self.site_name} scraping completed, total {len(data)} records.")
        return len(data), str(path), df.head(4).to_dict(orient="records")
3