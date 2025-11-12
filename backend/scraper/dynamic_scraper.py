import time, re, logging
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

# Reserved for Edge support (can be enabled in the future)
# from selenium.webdriver.edge.service import Service as EdgeService
# from selenium.webdriver.edge.options import Options as EdgeOptions
# from webdriver_manager.microsoft import EdgeChromiumDriverManager

class DynamicScraper:
    def __init__(self, config: dict):
        """
        Initialize the dynamic scraper with configuration.

        Parameters:
            config (dict): Configuration dictionary containing site details, browser type, retry settings, etc.
        """
        self.site_name = config.get("site_name")
        self.url = config.get("target_url")
        self.browser = config.get("browser", "chrome").lower()
        self.retry = config.get("retry", 2)
        self.delay = config.get("delay", 3)
        self.storage = config.get("storage", {})
        self.log_path = Path("logs") / f"{self.site_name.replace(' ', '_').lower()}.log"
        self._setup_logger()

    def _setup_logger(self):
        """
        Set up logging to record scraper activities.
        """
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=self.log_path,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _init_browser(self):
        """
        Initialize the browser driver based on the configuration.

        Returns:
            WebDriver: Selenium WebDriver instance.
        """
        logging.info(f"Initializing {self.browser} in headless mode...")
        if self.browser == "chrome":
            options = ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--remote-debugging-port=9222")
            options.binary_location = (
                "/usr/bin/google-chrome"
                if Path("/usr/bin/google-chrome").exists()
                else "/usr/bin/chromium-browser"
            )
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        elif self.browser == "edge":
            raise NotImplementedError("Edge support reserved for future use.")
        else:
            raise ValueError(f"Unsupported browser type: {self.browser}")
        return driver

    def fetch_page(self):
        """
        Fetch the webpage content with automatic retry mechanism.

        Returns:
            str: HTML content of the fetched page.

        Raises:
            Exception: If all retry attempts fail.
        """
        for attempt in range(1, self.retry + 1):
            try:
                logging.info(f"Attempt {attempt}: Fetching {self.url}")
                driver = self._init_browser()
                driver.get(self.url)
                time.sleep(5)  # Wait for the page to render
                html = driver.page_source
                driver.quit()
                logging.info(f"Page fetched successfully on attempt {attempt}")
                return html
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {e}")
                if attempt < self.retry:
                    time.sleep(self.delay)
                else:
                    logging.error("All retry attempts failed.")
                    raise

    def parse_page(self, html):
        """
        Parse the HTML content to extract relevant data.

        Parameters:
            html (str): HTML content of the page.

        Returns:
            list: List of extracted data entries.
        """
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

        # Extract Botox / Dysport information
        units_data = []
        for match in re.finditer(r"(\d+)\s*Units?\s*\$([0-9]+(?:\.[0-9]{2})?)", text):
            units_data.append({"units": int(match.group(1)), "price": float(match.group(2))})

        # Membership fee
        member_fee = None
        m = re.search(r"\$([0-9]+(?:\.[0-9]{2})?)\s*/\s*month", text, flags=re.I)
        if m:
            member_fee = float(m.group(1))

        # Phone / Email / Address
        phone = re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", text)
        email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        address = None
        for line in text.splitlines():
            if "Scottsdale" in line and ("AZ" in line or "Arizona" in line):
                address = line.strip()
                break

        # Business hours (e.g., Mon–Fri or includes AM/PM)
        hours = None
        for line in text.splitlines():
            if re.search(r"Mon|Tue|Wed|Thu|Fri", line) and "AM" in line:
                hours = line.strip()
                break

        data = []
        for item in units_data:
            data.append({
                "location": "Scottsdale",
                "service": "Botox® / Dysport®",
                "description": "It's all we do.",
                "units": item["units"],
                "price": item["price"],
                "member_fee_month": member_fee,
                "phone": phone.group(0) if phone else None,
                "email": email.group(0) if email else None,
                "address": address,
                "hours": hours,
                "source_url": self.url,
            })
        logging.info(f"Parsed {len(data)} entries from {self.url}")
        return data

    def save_to_csv(self, data):
        """
        Save the extracted data to a CSV file.

        Parameters:
            data (list): List of data entries to save.

        Returns:
            tuple: Path to the saved file and the DataFrame object.
        """
        df = pd.DataFrame(data)
        path = Path(self.storage.get("path", "output.csv"))
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logging.info(f"Saved data to {path}")
        return path, df

    def run(self):
        """
        Execute the full scraping process.

        Returns:
            tuple: Number of records, path to the saved file, and a sample of the data.
        """
        html = self.fetch_page()
        data = self.parse_page(html)
        path, df = self.save_to_csv(data)
        logging.info(f"✅ {self.site_name} scraping completed, total {len(df)} records.")
        return len(df), str(path), df.head(1).to_dict(orient="records")
