# backend/scraper/run_scraper.py

from backend.config.config_loader import load_config
from backend.scraper.base_scraper import BaseScraper
from backend.scraper.dynamic_scraper import DynamicScraper

def run_with_config(config_name="clubinject_scottsdale"):
    """
    Run scraper using the given config name.
    """

    # Load the config file
    config = load_config(config_name)

    # Detect mode
    mode = config.get("mode", "static").lower()

    if mode == "dynamic":
        print("🔄 Using DynamicScraper...")
        scraper = DynamicScraper(config)
    else:
        print("🧱 Using BaseScraper (static)...")
        scraper = BaseScraper(config)

    # Execute scraper
    return scraper.run()


def main():
    rows, out_path, sample = run_with_config("clubinject_scottsdale")
    print("Rows:", rows)
    print("Output:", out_path)
    print("Sample:", sample)


if __name__ == "__main__":
    main()
