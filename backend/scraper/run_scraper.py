# backend/scraper/run_scraper.py
from backend.scraper.base_scraper import BaseScraper
from backend.config.config_loader import load_config

def main():
    config = load_config("medical_spa")
    scraper = BaseScraper(config)
    scraper.run()

if __name__ == "__main__":
    main()
