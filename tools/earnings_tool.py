"""Earnings call and investor news search via Tavily."""

import logging
from tools.web_search import web_search

logger = logging.getLogger(__name__)


def search_earnings(competitor: str, quarter: str = "", year: str = "") -> list[dict]:
    """Search for earnings calls, investor relations, and press releases.
    Returns list of result dicts."""
    queries = [
        f"{competitor} earnings call {quarter} {year}".strip(),
        f"{competitor} investor relations press release {year}".strip(),
        f"site:seekingalpha.com {competitor} earnings {year}".strip(),
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        results = web_search(query, max_results=5, search_depth="advanced")
        for r in results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    logger.info(f"Earnings search for {competitor}: {len(all_results)} results")
    return all_results
