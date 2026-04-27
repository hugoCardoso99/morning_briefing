"""
News node — scrapes Portuguese news sites for headlines and lead paragraphs.
"""

from utils.scraper import scrape_expresso, scrape_jn


def news_node(state: dict) -> dict:
    """Scrape news from Expresso and Jornal de Notícias."""
    articles = []

    expresso_articles = scrape_expresso()
    jn_articles = scrape_jn()

    articles.extend(expresso_articles)
    articles.extend(jn_articles)

    if not articles:
        print("[news] Warning: no articles scraped from any source")

    return {"news": articles}
