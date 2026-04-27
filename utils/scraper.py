"""
News scraper utilities for Portuguese news sites.
Extracts headlines, lead paragraphs, and categories from Expresso and Jornal de Notícias.
"""

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
}

MAX_ARTICLES = 10  # per source

# Known categories to look for in URLs and CSS classes
KNOWN_CATEGORIES = {
    "economia": "Economia",
    "politica": "Política",
    "política": "Política",
    "desporto": "Desporto",
    "sport": "Desporto",
    "sociedade": "Sociedade",
    "mundo": "Mundo",
    "internacional": "Internacional",
    "tecnologia": "Tecnologia",
    "tech": "Tecnologia",
    "cultura": "Cultura",
    "opiniao": "Opinião",
    "opinião": "Opinião",
    "ciencia": "Ciência",
    "ciência": "Ciência",
    "saude": "Saúde",
    "saúde": "Saúde",
    "educacao": "Educação",
    "educação": "Educação",
    "justica": "Justiça",
    "justiça": "Justiça",
    "local": "Local",
    "pais": "País",
    "país": "País",
}


def _is_category_label(text: str) -> bool:
    """Check if a string is just a category label (possibly with punctuation)."""
    cleaned = text.strip().rstrip(" |·—-–/.,:;").lstrip(" |·—-–/.,:;").strip()
    lowered = cleaned.lower()
    all_labels = set(KNOWN_CATEGORIES.values())
    all_labels.update(k for k in KNOWN_CATEGORIES.keys())
    all_labels.update(v.lower() for v in KNOWN_CATEGORIES.values())
    return lowered in all_labels or cleaned in all_labels


def _clean_headline(headline: str) -> str:
    """
    Remove category labels that are sometimes appended to headlines.
    e.g. "Government announces new plan Economia" -> "Government announces new plan"
    """
    # Build set of all category labels (both keys and values)
    category_labels = set(KNOWN_CATEGORIES.values())
    category_labels.update(k.capitalize() for k in KNOWN_CATEGORIES.keys())

    stripped = headline.strip()
    for label in sorted(category_labels, key=len, reverse=True):
        # Check if headline ends with the category label
        if stripped.endswith(label):
            candidate = stripped[: -len(label)].rstrip(" |·—-–/")
            if candidate:  # don't strip if it would empty the headline
                stripped = candidate.strip()
                break
        # Also check if it starts with the category label (some sites prepend it)
        if stripped.startswith(label):
            candidate = stripped[len(label):].lstrip(" |·—-–/")
            if candidate:
                stripped = candidate.strip()
                break

    return stripped


def _extract_category(article_url: str, article_tag=None) -> str:
    """
    Try to extract a category from the article URL path or HTML attributes.
    Portuguese news sites typically use /categoria/slug-do-artigo patterns.
    Falls back to "Geral" if no category is found.
    """
    # Try URL path segments
    if article_url:
        parsed = urlparse(article_url)
        path_segments = [s.lower() for s in parsed.path.strip("/").split("/") if s]
        for segment in path_segments:
            # Remove accents for matching
            clean = segment.replace("-", "").replace("_", "")
            if segment in KNOWN_CATEGORIES:
                return KNOWN_CATEGORIES[segment]
            if clean in KNOWN_CATEGORIES:
                return KNOWN_CATEGORIES[clean]

    # Try section/category attributes on the article tag
    if article_tag:
        for attr in ["data-section", "data-category", "class"]:
            val = article_tag.get(attr, "")
            if isinstance(val, list):
                val = " ".join(val)
            val_lower = val.lower()
            for key, label in KNOWN_CATEGORIES.items():
                if key in val_lower:
                    return label

    return "Geral"


def scrape_expresso() -> list[dict]:
    """
    Scrape headlines and leads from Expresso homepage.
    Returns a list of dicts: {source, headline, lead, url, category}
    """
    url = "https://expresso.pt"
    articles = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for article_tag in soup.find_all("article", limit=MAX_ARTICLES):
            headline_tag = article_tag.find(["h1", "h2", "h3", "h4"])
            if not headline_tag:
                continue

            headline = _clean_headline(headline_tag.get_text(strip=True))
            if not headline:
                continue

            link_tag = headline_tag.find("a") or article_tag.find("a")
            article_url = ""
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                article_url = href if href.startswith("http") else f"{url}{href}"

            category = _extract_category(article_url, article_tag)

            articles.append({
                "source": "Expresso",
                "headline": headline,
                "url": article_url,
                "category": category,
            })

    except requests.RequestException as e:
        print(f"[news] Error scraping Expresso: {e}")

    return articles


def scrape_jn() -> list[dict]:
    """
    Scrape headlines and leads from Jornal de Notícias homepage.
    Returns a list of dicts: {source, headline, lead, url, category}
    """
    url = "https://www.jn.pt"
    articles = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for article_tag in soup.find_all("article", limit=MAX_ARTICLES):
            headline_tag = article_tag.find(["h1", "h2", "h3", "h4"])
            if not headline_tag:
                continue

            headline = _clean_headline(headline_tag.get_text(strip=True))
            if not headline:
                continue

            link_tag = headline_tag.find("a") or article_tag.find("a")
            article_url = ""
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                article_url = href if href.startswith("http") else f"{url}{href}"

            category = _extract_category(article_url, article_tag)

            articles.append({
                "source": "Jornal de Notícias",
                "headline": headline,
                "url": article_url,
                "category": category,
            })

    except requests.RequestException as e:
        print(f"[news] Error scraping JN: {e}")

    return articles
