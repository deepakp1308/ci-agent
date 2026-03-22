"""Sentiment Trend Runner — Job 2: Gather and synthesize sentiment data per competitor."""

import logging
from datetime import datetime

from tools.web_search import web_search
from tools.reddit_tool import search_reddit
from storage.db import get_sentiment_history, store_sentiment_snapshot
from synthesizers.sentiment_synth import synthesize_sentiment

logger = logging.getLogger(__name__)

SENTIMENT_CONFIG = {
    "klaviyo": {
        "name": "Klaviyo",
        "subreddits": [
            "klaviyo", "emailmarketing", "hubspot", "marketing",
            "analytics", "smallbusiness", "ecommerce", "SaaS",
        ],
        "reddit_queries": [
            "Klaviyo problems",
            "Klaviyo analytics wrong",
            "Klaviyo reporting dashboard",
            "Klaviyo custom reports",
            "Klaviyo AI",
            "Klaviyo data accuracy",
            "Klaviyo attribution",
            "Klaviyo email editor",
            "Klaviyo email builder",
            "Klaviyo SMS",
            "Klaviyo omnichannel",
            "switched from Klaviyo",
            "Klaviyo review",
            "Klaviyo vs Mailchimp",
        ],
        "web_queries": [
            "{name} complaint OR problem OR broken {month_year}",
            "{name} analytics reporting issue {year}",
            "{name} AI feature review {year}",
            "{name} email editor builder review {year}",
            "{name} reporting dashboard review {year}",
            "{name} SMS omnichannel review {year}",
            "{name} vs Mailchimp comparison {year}",
        ],
    },
    "hubspot": {
        "name": "HubSpot",
        "subreddits": [
            "hubspot", "emailmarketing", "marketing", "analytics",
            "smallbusiness", "ecommerce", "digital_marketing", "SaaS",
        ],
        "reddit_queries": [
            "HubSpot reporting broken",
            "HubSpot analytics dashboard",
            "HubSpot custom reports",
            "Breeze AI review",
            "HubSpot data accuracy",
            "HubSpot attribution",
            "HubSpot email editor",
            "HubSpot content hub",
            "HubSpot SMS WhatsApp",
            "HubSpot omnichannel",
            "HubSpot problems",
            "switched from HubSpot",
            "HubSpot pricing",
            "HubSpot vs Mailchimp",
        ],
        "web_queries": [
            "{name} complaint OR problem OR broken {month_year}",
            "{name} analytics reporting issue {year}",
            "{name} AI feature review {year}",
            "{name} email editor content hub review {year}",
            "{name} reporting dashboard review {year}",
            "{name} omnichannel SMS WhatsApp review {year}",
            "{name} vs Mailchimp comparison {year}",
        ],
    },
}


def run_sentiment_trend(
    competitor_key: str,
    week_iso: str,
) -> dict:
    """Run the full sentiment trend pipeline for one competitor.
    Returns the synthesized sentiment dict."""
    config = SENTIMENT_CONFIG.get(competitor_key)
    if not config:
        raise ValueError(f"Unknown competitor: {competitor_key}")

    competitor_name = config["name"]
    now = datetime.now()
    month_year = now.strftime("%B %Y")
    year = now.strftime("%Y")

    logger.info(f"=== SENTIMENT TREND: {competitor_name} ({week_iso}) ===")

    # STEP 1 — GATHER: Reddit
    logger.info(f"Step 1a: Reddit search for {competitor_name}")
    reddit_data = []
    for query in config["reddit_queries"]:
        posts = search_reddit(
            query=query,
            subreddits=config["subreddits"],
            time_filter="week",
            limit=50,
        )
        reddit_data.extend(posts)

    # Deduplicate by URL
    seen = set()
    unique_reddit = []
    for post in reddit_data:
        url = post.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique_reddit.append(post)
    reddit_data = unique_reddit
    logger.info(f"Reddit: {len(reddit_data)} unique posts for {competitor_name}")

    # STEP 1b — GATHER: Web social signals
    logger.info(f"Step 1b: Web social signals for {competitor_name}")
    social_data = []
    for query_template in config["web_queries"]:
        query = query_template.format(
            name=competitor_name,
            month_year=month_year,
            year=year,
        )
        results = web_search(query, max_results=5)
        social_data.extend(results)

    # Twitter/LinkedIn signal search
    social_data.extend(
        web_search(
            f"site:twitter.com OR site:linkedin.com {competitor_name} analytics",
            max_results=5,
        )
    )

    # STEP 1c — Get history
    logger.info(f"Step 1c: Loading sentiment history for {competitor_name}")
    history = get_sentiment_history(competitor_key, n_weeks=12)

    # STEP 2 — SYNTHESIZE
    logger.info(f"Step 2: Synthesizing sentiment for {competitor_name}")
    sentiment = synthesize_sentiment(
        competitor=competitor_name,
        week_of=week_iso,
        reddit_data=reddit_data,
        social_data=social_data,
        history=history,
    )

    # Store snapshot
    store_sentiment_snapshot(competitor_key, week_iso, sentiment)
    logger.info(f"=== SENTIMENT TREND COMPLETE: {competitor_name} ===")

    return sentiment
