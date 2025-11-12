# backend/scraper/run_scraper.py
from backend.scraper.base_scraper import BaseScraper
from backend.config.config_loader import load_config
from backend.scraper.dynamic_scraper import DynamicScraper

def run_with_config(config_name="clubinject_scottsdale"):
    config = load_config(config_name)
    scraper = BaseScraper(config)
    # mode = config.get("mode", "static")
    # if mode == "dynamic":
    #     scraper = DynamicScraper(config)
    # else:
    #     scraper = BaseScraper(config)
    return scraper.run()

def main():
    run_with_config("clubinject_scottsdale")

if __name__ == "__main__":
    main()
