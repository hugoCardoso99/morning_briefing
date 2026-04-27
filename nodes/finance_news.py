"""
Finance news node — fetches general finance/market news from Yahoo Finance.
Chained after the stocks node: stocks → finance_news → router.
Skipped on weekends.
"""

import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_ARTICLES = 8


def _scrape_yahoo_finance_news() -> list[dict]:
    """Scrape general finance headlines from Yahoo Finance."""
    url = "https://finance.yahoo.com/news/"
    articles = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Yahoo Finance news pages use <h3> tags inside stream items
        seen_titles = set()

        for link_tag in soup.find_all("a", href=True, limit=50):
            h3 = link_tag.find("h3")
            if not h3:
                continue

            title = h3.get_text(strip=True)
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            href = link_tag["href"]
            article_url = href if href.startswith("http") else f"https://finance.yahoo.com{href}"

            articles.append({
                "title": title,
                "url": article_url,
                "publisher": "Yahoo Finance",
            })

            if len(articles) >= MAX_ARTICLES:
                break

    except requests.RequestException as e:
        print(f"[finance_news] Error scraping Yahoo Finance: {e}")

    # Fallback: try the RSS feed if scraping got nothing
    if not articles:
        articles = _fetch_yahoo_rss()

    return articles


def _fetch_yahoo_rss() -> list[dict]:
    """Fallback: fetch from Yahoo Finance RSS feed."""
    rss_url = "https://finance.yahoo.com/news/rssindex"
    articles = []

    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for item in soup.find_all("item", limit=MAX_ARTICLES):
            title_tag = item.find("title")
            link_tag = item.find("link")

            if title_tag and title_tag.string:
                articles.append({
                    "title": title_tag.string.strip(),
                    "url": link_tag.string.strip() if link_tag and link_tag.string else "",
                    "publisher": "Yahoo Finance",
                })

    except requests.RequestException as e:
        print(f"[finance_news] Error fetching Yahoo RSS: {e}")

    return articles


def finance_news_node(state) -> dict:
    """Fetch general finance news. Skipped on weekends."""
    is_weekend = state.is_weekend

    if is_weekend:
        return {"finance_news": []}

    articles = _scrape_yahoo_finance_news()
    return {"finance_news": articles}
