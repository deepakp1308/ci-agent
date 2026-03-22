"""Tavily web search wrapper with rate limiting and retry logic."""

import os
import time
import logging
import threading

from tavily import TavilyClient

logger = logging.getLogger(__name__)

_client = None
_last_call_time = 0
_lock = threading.Lock()
MIN_INTERVAL = 0.5  # 500ms between calls to avoid rate limiting


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY not set")
        _client = TavilyClient(api_key=api_key)
    return _client


def _rate_limit():
    """Enforce minimum interval between Tavily calls."""
    global _last_call_time
    with _lock:
        now = time.time()
        elapsed = now - _last_call_time
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        _last_call_time = time.time()


def web_search(query, max_results=10, search_depth="advanced"):
    """Search the web via Tavily with rate limiting."""
    client = _get_client()
    retries = 3
    for attempt in range(retries):
        try:
            _rate_limit()
            logger.info(f"Tavily search: {query!r} (max={max_results})")
            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
            )
            results = response.get("results", [])
            logger.info(f"Tavily returned {len(results)} results")
            return results
        except Exception as e:
            err_str = str(e)
            if "excessive requests" in err_str.lower() or "blocked" in err_str.lower():
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s backoff for rate limits
                logger.warning(f"Tavily rate limited (attempt {attempt + 1}). Waiting {wait}s...")
                time.sleep(wait)
            else:
                wait = 2 ** attempt
                logger.warning(f"Tavily failed (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
                if attempt < retries - 1:
                    time.sleep(wait)
                else:
                    logger.error(f"Tavily failed after {retries} attempts: {e}")
                    return []
    return []
