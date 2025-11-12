# backend/scraper/utils.py
from urllib.parse import urlsplit, urlunsplit
from urllib import robotparser

# Define a set of query parameter keys to be filtered out
BLOCKED_QUERY_KEYS = {
    "author","tag","month","view","format","page-context","json","json-pretty",
    "ical","reversePaginate"
}

def clean_url(url: str, strip_query_params: bool = True) -> str:
    """
    Clean the URL by optionally removing query parameters.

    Parameters:
        url (str): The URL to be cleaned.
        strip_query_params (bool): Whether to remove query parameters.

    Returns:
        str: The cleaned URL.
    """
    parts = list(urlsplit(url))
    if strip_query_params and parts[3]:
        # Remove all query parameters (e.g., tracking parameters like gclid/gad_source)
        parts[3] = ""
    return urlunsplit(parts)

def is_allowed_by_robots(url: str, ua: str = "MonAgentCrawler") -> bool:
    """
    Check if the URL is allowed to be crawled by robots.txt.

    Parameters:
        url (str): The URL to check.
        ua (str): The User-Agent to use.

    Returns:
        bool: True if crawling is allowed, False otherwise.
    """
    base = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
    rp = robotparser.RobotFileParser()
    rp.set_url(f"{base}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch(ua, url)
    except Exception:
        # If reading fails, conservatively treat as not allowed
        return False
