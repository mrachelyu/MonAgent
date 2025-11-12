# backend/scraper/run_scraper.py
from backend.scraper.base_scraper import BaseScraper
from backend.config.config_loader import load_config
from backend.scraper.dynamic_scraper import DynamicScraper

def run_with_config(config_name="clubinject_scottsdale"):
    """
    Run the scraper with the specified configuration.

    Parameters:
        config_name (str): The name of the configuration file (without extension).

    Returns:
        tuple: The result of the scraper's run method, including data count, file path, and sample data.
    """
    config = load_config(config_name)  # Load the configuration file
    scraper = BaseScraper(config)  # Default to the static scraper
    mode = config.get("mode", "static")  # Determine the scraping mode (static or dynamic)
    if mode == "dynamic":
        scraper = DynamicScraper(config)  # Use the dynamic scraper if specified
    else:
        scraper = BaseScraper(config)  # Use the static scraper by default
    return scraper.run()  # Execute the scraper

def main():
    """
    Main entry point for running the scraper with a default configuration.
    """
    run_with_config("clubinject_scottsdale")

if __name__ == "__main__":
    main()  # Run the main function if executed as a script
