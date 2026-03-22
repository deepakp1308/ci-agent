"""Firecrawl website crawler wrapper with Tavily fallback."""

import os
import time
import logging

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from firecrawl import FirecrawlApp
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY not set")
        _client = FirecrawlApp(api_key=api_key)
    return _client


def crawl_website(url, max_pages=5, include_patterns=None):
    """Scrape a single page via Firecrawl. Falls back to Tavily on failure."""
    retries = 2
    for attempt in range(retries):
        try:
            client = _get_client()
            logger.info(f"Firecrawl scrape: {url}")
            result = client.scrape(url, formats=["markdown"])

            pages = []
            if isinstance(result, dict):
                pages.append({
                    "url": result.get("metadata", {}).get("sourceURL", url),
                    "title": result.get("metadata", {}).get("title", ""),
                    "content": result.get("markdown", result.get("content", "")),
                })
            logger.info(f"Firecrawl returned {len(pages)} pages")
            return pages
        except Exception as e:
            logger.warning(f"Firecrawl failed (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
            else:
                logger.warning("Firecrawl failed. Falling back to Tavily.")
                return _tavily_fallback(url)


def _tavily_fallback(url):
    """Fallback: use Tavily to extract content from a URL."""
    try:
        from tools.web_search import web_search
        results = web_search(f"site:{url}", max_results=3, search_depth="advanced")
        pages = []
        for r in results:
            pages.append({
                "url": r.get("url", url),
                "title": r.get("title", ""),
                "content": r.get("content", ""),
            })
        return pages
    except Exception as e:
        logger.error(f"Tavily fallback also failed for {url}: {e}")
        return []
