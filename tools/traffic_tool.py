"""SimilarWeb traffic estimation (optional). Falls back gracefully if no API key."""

import os
import logging
import requests

logger = logging.getLogger(__name__)


def estimate_traffic(domain: str) -> dict:
    """Estimate website traffic via SimilarWeb API.
    Returns dict with traffic data or empty dict if unavailable."""
    api_key = os.environ.get("SIMILARWEB_API_KEY")
    if not api_key:
        logger.info("SimilarWeb API key not set — skipping traffic estimation")
        return {}

    try:
        url = f"https://api.similarweb.com/v1/website/{domain}/total-traffic-and-engagement/visits"
        params = {
            "api_key": api_key,
            "start_date": "2024-01",
            "end_date": "2025-12",
            "country": "world",
            "granularity": "monthly",
            "main_domain_only": "false",
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.info(f"SimilarWeb traffic data for {domain}: available")
        return data
    except Exception as e:
        logger.warning(f"SimilarWeb API failed for {domain}: {e}")
        return {}
