"""Product Intelligence Runner — Job 1: Gather and synthesize product data per competitor."""

import json
import logging
from datetime import datetime

from tools.web_search import web_search
from tools.web_crawler import crawl_website
from tools.earnings_tool import search_earnings
from storage.db import get_product_history, store_product_snapshot
from synthesizers.competitor_brief import synthesize_competitor_brief

logger = logging.getLogger(__name__)

COMPETITOR_CONFIG = {
    "klaviyo": {
        "name": "Klaviyo",
        "crawl_urls": [
            "https://www.klaviyo.com/product",
            "https://www.klaviyo.com/features",
            "https://www.klaviyo.com/pricing",
        ],
        "blog_url": "https://www.klaviyo.com/blog",
        "investor_url": "https://investors.klaviyo.com",
        "search_queries": [
            "Klaviyo new feature announcement product update 2026",
            "Klaviyo analytics reporting dashboard custom reports",
            "Klaviyo attribution model data accuracy",
            "Klaviyo predictive analytics benchmarks",
            "Klaviyo omnichannel SMS push notifications CDP",
            "Klaviyo email editor builder AI content personalization",
            "Klaviyo AI segmentation automation features",
            "Klaviyo earnings revenue ARR customer count growth",
            "Klaviyo vs Mailchimp comparison 2026",
        ],
    },
    "hubspot": {
        "name": "HubSpot",
        "crawl_urls": [
            "https://www.hubspot.com/products",
            "https://www.hubspot.com/products/analytics",
            "https://www.hubspot.com/products/ai",
        ],
        "blog_url": "https://www.hubspot.com/blog",
        "investor_url": "https://ir.hubspot.com",
        "search_queries": [
            "HubSpot new feature announcement product update 2026",
            "HubSpot reporting dashboard custom report builder analytics",
            "HubSpot attribution reporting marketing analytics",
            "HubSpot omnichannel SMS WhatsApp cross-channel",
            "HubSpot email editor content hub AI content assistant",
            "HubSpot Breeze AI agents copilot features",
            "HubSpot earnings revenue ARR customer count growth",
            "HubSpot vs Mailchimp comparison 2026",
            "HubSpot pricing tier comparison features",
        ],
    },
}


def run_product_intel(
    competitor_key: str,
    week_iso: str,
) -> dict:
    """Run the full product intelligence pipeline for one competitor."""
    config = COMPETITOR_CONFIG.get(competitor_key)
    if not config:
        raise ValueError(f"Unknown competitor: {competitor_key}")

    competitor_name = config["name"]
    now = datetime.now()
    month_year = now.strftime("%B %Y")
    year = now.strftime("%Y")
    quarter = f"Q{(now.month - 1) // 3 + 1}"

    logger.info(f"=== PRODUCT INTEL: {competitor_name} ({week_iso}) ===")

    gathered = {
        "search_results": [],
        "crawled_pages": [],
        "earnings_data": [],
    }

    # STEP 1 — DISCOVERY: web searches
    logger.info(f"Step 1: Discovery searches for {competitor_name}")
    for query in config["search_queries"]:
        results = web_search(f"{query} {month_year}", max_results=5)
        gathered["search_results"].extend(results)

    # Additional quant-focused searches
    gathered["search_results"].extend(
        web_search(f"{competitor_name} market share email marketing 2025 2026", max_results=5)
    )
    gathered["search_results"].extend(
        web_search(f"{competitor_name} revenue ARR customers growth {year}", max_results=5)
    )
    gathered["search_results"].extend(
        web_search(f"{competitor_name} vs Mailchimp analytics reporting comparison", max_results=5)
    )

    # STEP 1b — Crawl key pages
    logger.info(f"Step 1b: Crawling key pages for {competitor_name}")
    for url in config["crawl_urls"]:
        pages = crawl_website(url, max_pages=5)
        gathered["crawled_pages"].extend(pages)

    # STEP 1c — Earnings/investor data
    logger.info(f"Step 1c: Searching earnings for {competitor_name}")
    gathered["earnings_data"] = search_earnings(competitor_name, quarter, year)

    # STEP 1d — Get history
    logger.info(f"Step 1d: Loading history for {competitor_name}")
    history = get_product_history(competitor_key, n_weeks=12)

    # STEP 2 — DEEP DIVE on analytics/reporting/omnichannel/email
    logger.info(f"Step 2: Deep dive for {competitor_name}")
    deep_dive_queries = [
        f"{competitor_name} reporting dashboard capabilities {year}",
        f"{competitor_name} email builder features review {year}",
        f"{competitor_name} omnichannel SMS push notifications capabilities",
        f"{competitor_name} analytics accuracy data quality issues",
        f"{competitor_name} pricing tier comparison features {year}",
    ]
    for query in deep_dive_queries:
        results = web_search(query, max_results=3)
        gathered["search_results"].extend(results)

    # STEP 3 — SYNTHESIZE
    logger.info(f"Step 3: Synthesizing brief for {competitor_name}")
    brief = synthesize_competitor_brief(
        competitor=competitor_name,
        week_of=week_iso,
        gathered_data=gathered,
        history=history,
    )

    store_product_snapshot(competitor_key, week_iso, brief)
    logger.info(f"=== PRODUCT INTEL COMPLETE: {competitor_name} ===")

    return brief
