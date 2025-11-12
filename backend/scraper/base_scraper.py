# backend/scraper/base_scraper.py
import re, time, requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from backend.scraper.utils import clean_url, is_allowed_by_robots

# Default User-Agent string for HTTP requests
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
)

class BaseScraper:
    def __init__(self, config: dict):
        """
        Initialize the BaseScraper with configuration settings.

        Parameters:
            config (dict): Configuration dictionary containing site details, parsing mode, and storage settings.
        """
        self.site_name = config.get("site_name")  # Name of the site to scrape
        self.url = config.get("target_url")  # Target URL for scraping
        self.strip_query_params = config.get("strip_query_params", True)  # Whether to remove query parameters from the URL
        self.parse_mode = config.get("parse_mode", "generic")  # Parsing mode (e.g., generic, clubinject_units)
        self.storage = config.get("storage", {})  # Storage settings for saving data
        print(f"🕷️ Initializing scraper: {self.site_name} ({self.url})")

    def fetch_page(self):
        """
        Fetch the HTML content of the target webpage.

        Returns:
            str: The HTML content of the page.

        Raises:
            PermissionError: If the URL is blocked by robots.txt.
            requests.RequestException: If the HTTP request fails.
        """
        u = clean_url(self.url, self.strip_query_params)  # Clean the URL by removing query parameters
        if not is_allowed_by_robots(u):
            raise PermissionError(f"Blocked by robots.txt: {u}")

        headers = {"User-Agent": DEFAULT_UA}  # Set the User-Agent header
        print(f"🔍 GET {u}")
        r = requests.get(u, headers=headers, timeout=15)  # Send the HTTP GET request
        r.raise_for_status()  # Raise an exception for HTTP errors
        time.sleep(1.2)  # Polite delay to avoid overloading the server
        return r.text

    def parse_page(self, html):
        """
        Parse the HTML content and extract data based on the parsing mode.

        Parameters:
            html (str): The HTML content of the page.

        Returns:
            list: A list of extracted data entries.
        """
        if self.parse_mode == "clubinject_units":
            return self._parse_clubinject_units(html)  # Use the specific parsing method for clubinject_units
        return []

    def _parse_clubinject_units(self, html):
        """
        Parse the HTML content to extract Botox/Dysport information, membership fees, and contact details.

        Parameters:
            html (str): The HTML content of the page.

        Returns:
            list: A list of dictionaries containing extracted data.
        """
        soup = BeautifulSoup(html, "html.parser")  # Parse the HTML using BeautifulSoup
        text = soup.get_text("\n", strip=True)  # Extract all text content from the HTML

        # Extract units and prices (e.g., "20 Units $150.80")
        unit_price = []
        for m in re.finditer(r"(\d+)\s*Units?\s*\$([0-9]+(?:\.[0-9]{2})?)", text, flags=re.I):
            unit_count = int(m.group(1))
            price = float(m.group(2))
            unit_price.append({"units": unit_count, "price": price})

        # Extract membership fee (e.g., "$9.72/month")
        member_fee = None
        mm = re.search(r"\$([0-9]+(?:\.[0-9]{2})?)\s*/\s*month", text, flags=re.I)
        if mm:
            member_fee = float(mm.group(1))

        # Extract contact information (phone, email, address)
        phone = None
        ph = re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", text)
        if ph: phone = ph.group(0)

        email = None
        em = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if em: email = em.group(0)

        address = None
        for line in text.splitlines():
            if "Scottsdale" in line and ("AZ" in line or "Arizona" in line):
                address = line.strip()
                break

        # Combine extracted data into a structured list
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
        """
        Save the extracted data to a CSV file.

        Parameters:
            data (list): The data to save.

        Returns:
            tuple: The file path and the DataFrame object.
        """
        path = Path(self.storage.get("path", "output.csv"))  # Get the file path from the configuration
        df = pd.DataFrame(data)  # Convert the data to a pandas DataFrame
        path.parent.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
        df.to_csv(path, index=False, encoding="utf-8-sig")  # Save the DataFrame to a CSV file
        return path, df

    def run(self):
        """
        Execute the full scraping process: fetch, parse, and save data.

        Returns:
            tuple: The number of records, file path, and a sample of the data.
        """
        html = self.fetch_page()  # Fetch the HTML content
        data = self.parse_page(html)  # Parse the HTML content
        path, df = self.save_to_csv(data)  # Save the parsed data to a CSV file
        print(f"✅ {self.site_name} scraping completed, total {len(data)} records.")
        return len(data), str(path), df.head(4).to_dict(orient="records")