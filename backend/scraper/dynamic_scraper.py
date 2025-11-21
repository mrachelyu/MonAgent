import time
import re
import logging
from pathlib import Path
from urllib import robotparser
from urllib.parse import urlsplit

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class DynamicScraper:
    """
    Dynamic scraper:
    - Currently designed primarily for ClubInject Scottsdale (Elfsight + Squarespace structure)
    - But the output fields follow a general schema, reusable for chatbots or other industries
    """

    def __init__(self, config: dict):
        self.config = config
        self.site_name = config.get("site_name", "Unknown Site")
        self.url = config.get("target_url")
        self.browser = config.get("browser", "chrome").lower()
        self.check_robots = config.get("check_robots", True)
        self.retry = config.get("retry", 2)
        self.delay = config.get("delay", 3)
        self.storage = config.get("storage", {})

        log_name = self.site_name.replace(" ", "_").lower()
        self.log_path = Path("logs") / f"{log_name}.log"
        self._setup_logger()
        logging.info(f"Initialized DynamicScraper for {self.site_name} ({self.url})")

    # ------------------ logger & robots ------------------ #

    def _setup_logger(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=self.log_path,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _is_allowed_by_robots(self) -> bool:
        """Check if robots.txt allows crawling the target_url"""
        if not self.url:
            logging.error("No target URL provided")
            return False

        parts = urlsplit(self.url)
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"

        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            allowed = rp.can_fetch("MonAgentCrawler", self.url)
            logging.info(f"robots.txt check: {robots_url}, allowed={allowed}")
            return allowed
        except Exception as e:
            logging.error(f"Failed to read robots.txt: {e}")
            # Conservative approach: treat as disallowed if unreadable (change to True for testing purposes)
            return False

    # ------------------ browser / fetch ------------------ #

    def _init_chrome(self):
        options = ChromeOptions()
        # If WSL has no GUI, enable headless mode by uncommenting the line below:
        # options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

        # In WSL, it might be google-chrome or chromium-browser
        if Path("/usr/bin/google-chrome").exists():
            options.binary_location = "/usr/bin/google-chrome"
        elif Path("/usr/bin/chromium-browser").exists():
            options.binary_location = "/usr/bin/chromium-browser"

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _init_browser(self):
        if self.browser == "chrome":
            return self._init_chrome()
        elif self.browser == "edge":
            # Placeholder for future implementation if Edge support is needed
            raise NotImplementedError("Edge browser support is reserved for future use.")
        else:
            raise ValueError(f"Unsupported browser type: {self.browser}")

    def fetch_page(self) -> str:
        """With retry + wait for rendering completion + multiple scrolls to trigger lazy-load"""
        if not self.url:
            raise ValueError("No target URL provided")

        if self.check_robots:
            if not self._is_allowed_by_robots():
                raise PermissionError(f"Robots.txt disallows crawling: {self.url}")

        last_error = None
        for attempt in range(1, self.retry + 1):
            try:
                logging.info(f"[Attempt {attempt}] Starting to load page: {self.url}")
                driver = self._init_browser()
                driver.get(self.url)

                # Wait for footer to appear, indicating most content is loaded
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "footer"))
                )

                # Scroll down multiple times to load Elfsight / lazy blocks
                for _ in range(4):
                    driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
                    time.sleep(1.8)

                html = driver.page_source
                # For debugging: save full HTML for analysis if needed
                with open("debug_scottsdale.html", "w", encoding="utf-8") as f:
                    f.write(html)

                driver.quit()
                logging.info(f"[Attempt {attempt}] Page loaded successfully")
                return html
            except Exception as e:
                logging.error(f"[Attempt {attempt}] Failed to load: {e}")
                last_error = e
                time.sleep(self.delay)

        raise RuntimeError(f"Failed to load page: {last_error}")

    # ------------------ General row schema ------------------ #

    def _empty_row(self):
        """Create an empty row with a general schema"""
        return {
            "type": None,
            "section_label": None,
            "title": None,
            "content": None,
            "units": None,
            "price": None,
            "member_fee_month": None,
            "phone": None,
            "email": None,
            "address": None,
            "hours": None,
            "link_text": None,
            "link_url": None,
            "source_url": self.url,
        }

    # ------------------ Services & Contact Info ------------------ #

    def _parse_services_and_contact(self, soup: BeautifulSoup):
        """Parse Botox / Dysport prices, membership fees, phone, email, address, hours"""
        full_text = soup.get_text("\n", strip=True)
        rows = []

        # Units + price, e.g., 20 Units $150.80
        unit_price = []
        for m in re.finditer(r"(\d+)\s*Units?\s*\$([0-9]+(?:\.[0-9]{2})?)", full_text, re.I):
            unit_price.append((int(m.group(1)), float(m.group(2))))

        # Membership monthly fee, e.g., $9.72/month
        member_fee = None
        mm = re.search(r"\$([0-9]+(?:\.[0-9]{2})?)\s*/\s*month", full_text, re.I)
        if mm:
            member_fee = float(mm.group(1))

        # Phone
        phone = None
        ph = re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", full_text)
        if ph:
            phone = ph.group(0)

        # Email
        email = None
        em = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", full_text)
        if em:
            email = em.group(0)

        # Address: avoid capturing titles like "Botox® / Dysport® Scottsdale Arizona — ClubInject®"
        address = None
        candidate_lines = []
        for line in full_text.splitlines():
            if "Scottsdale" in line and ("AZ" in line or "Arizona" in line):
                candidate_lines.append(line.strip())

        # Prefer lines containing street numbers
        for line in candidate_lines:
            if re.search(r"\d{3,}", line):
                address = line.strip()
                break
        if not address and candidate_lines:
            address = candidate_lines[-1].strip()

        # Hours (e.g., Mon–Fri 10AM–6PM)
        hours = None
        for line in full_text.splitlines():
            l = line.strip()
            if not l:
                continue
            if re.search(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)", l) and re.search(r"(AM|PM|am|pm)", l):
                hours = l
                break

        for units, price in unit_price:
            row = self._empty_row()
            row["type"] = "service"
            row["section_label"] = "Botox / Dysport"
            row["title"] = "Botox® / Dysport®"
            row["content"] = "It's all we do."
            row["units"] = units
            row["price"] = price
            row["member_fee_month"] = member_fee
            row["phone"] = phone
            row["email"] = email
            row["address"] = address
            row["hours"] = hours
            rows.append(row)

        return rows

    # ------------------ Elfsight Block Parsing (About / Pricing / Membership / Reviews) ------------------ #

    def _parse_elfsight_blocks(self, soup: BeautifulSoup):
        """
        Specifically handle the Elfsight widget structure:
        - Titles are in font-size:40px TextBlock__TextHTML
        - Content is in font-size:22px TextBlock__TextHTML
        """
        rows = []

        # All text blocks (titles + content)
        text_blocks = soup.select("div[class*='TextBlock__TextHTML']")
        current_section = None  # Remember "About Us" titles

        for tb in text_blocks:
            raw = tb.get_text("\n", strip=True)
            if not raw:
                continue

            style = tb.get("style", "")
            lower = raw.lower()

            # 40px: treat as title
            if "font-size: 40px" in style:
                # Set context only, do not directly generate rows
                if "about us" in lower:
                    current_section = "about"
                elif "joining is simple" in lower or "join" in lower:
                    current_section = "join"
                else:
                    current_section = None
                continue  # Skip title itself, content stored in next 22px block

            # 22px: content block corresponding to title
            if "font-size: 22px" in style:
                row = self._empty_row()

                # 1) Membership / Join
                if "memberships are just" in lower or "membership" in lower:
                    row["type"] = "join_info"
                    row["section_label"] = "Join"
                    row["title"] = "Membership"
                    row["content"] = raw

                # 2) Pricing summary (non-member / member unit prices)
                elif "we charge" in lower and ("botox" in lower or "dysport" in lower):
                    row["type"] = "pricing_summary"
                    row["section_label"] = "Pricing"
                    row["title"] = "Pricing Summary"
                    row["content"] = raw

                # 3) About content (first 22px block after About Us title)
                elif current_section == "about" and (
                    "clubinject" in lower and "group of" in lower
                ):
                    row["type"] = "about"
                    row["section_label"] = "About"
                    row["title"] = "About Us"
                    row["content"] = raw

                # 4) Reviews / Testimonials (e.g., Google reviews widget text)
                elif "review" in lower or ("google" in lower and "stars" in lower):
                    row["type"] = "testimonial"
                    row["section_label"] = "Testimonials"
                    row["title"] = "Reviews"
                    row["content"] = raw

                # 5) Others: treat as general text
                else:
                    row["type"] = "generic"
                    row["section_label"] = "Text"
                    first_line = raw.splitlines()[0]
                    row["title"] = first_line[:80]
                    row["content"] = raw

                rows.append(row)

        return rows

    # ------------------ General sections (currently conservative, no duplicate Elfsight parsing) ------------------ #

    def _parse_sections(self, soup: BeautifulSoup):
        """
        If future non-Elfsight <section> content appears, rules can be added here.
        Currently returns an empty list or performs very weak generic extraction to avoid duplication.
        """
        rows = []
        # Add specific rules here if needed in the future
        return rows

    # ------------------ Links ------------------ #

    def _parse_links(self, soup: BeautifulSoup):
        """Parse all a[href] links (excluding #anchor)"""
        rows = []
        seen = set()

        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href or not isinstance(href, str) or href.startswith("#"):
                continue
            if href in seen:
                continue
            seen.add(href)

            text = a.get_text(strip=True) or None
            row = self._empty_row()
            row["type"] = "link"
            row["section_label"] = "Link"
            row["title"] = text
            row["link_text"] = text
            row["link_url"] = href
            rows.append(row)

        return rows

    # ------------------ master parse ------------------ #

    def parse_page(self, html: str):
        soup = BeautifulSoup(html, "html.parser")

        rows = []
        # Services & Contact
        rows += self._parse_services_and_contact(soup)
        # Elfsight content (About / Pricing / Membership / Reviews)
        rows += self._parse_elfsight_blocks(soup)
        # Other sections (currently conservative, not used)
        rows += self._parse_sections(soup)
        # Site-wide links
        rows += self._parse_links(soup)

        logging.info(f"parse_page: Generated {len(rows)} rows in total")
        return rows


    
    # ------------------ save & run ------------------ #

    def save_to_csv(self, rows):
        df = pd.DataFrame(rows)
        path = Path(self.storage.get("path", "output.csv"))
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logging.info(f"Saved CSV to {path}")
        return path, df

    def run(self):
        html = self.fetch_page()
        rows = self.parse_page(html)
        path, df = self.save_to_csv(rows)
        logging.info(f"✅ {self.site_name} scraping completed, {len(df)} rows in total")
        # Return: total rows, file path, first three samples (for API /scrape use)
        return len(df), str(path), df.head(3).to_dict(orient="records")
