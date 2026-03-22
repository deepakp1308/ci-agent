"""Reddit search via PRAW with Tavily fallback."""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_reddit = None


def _get_reddit():
    global _reddit
    if _reddit is None:
        import praw

        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        user_agent = os.environ.get("REDDIT_USER_AGENT", "ci-agent/1.0")
        if not client_id or not client_secret:
            raise RuntimeError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")
        _reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
    return _reddit


def search_reddit(
    query: str,
    subreddits: list[str],
    time_filter: str = "week",
    limit: int = 50,
) -> list[dict]:
    """Search Reddit posts and comments. Returns list of post dicts."""
    try:
        reddit = _get_reddit()
        return _search_via_praw(reddit, query, subreddits, time_filter, limit)
    except Exception as e:
        logger.warning(f"PRAW search failed: {e}. Falling back to Tavily.")
        return _tavily_reddit_fallback(query, subreddits, limit)


def _search_via_praw(reddit, query, subreddits, time_filter, limit) -> list[dict]:
    results = []
    per_sub_limit = max(limit // len(subreddits), 5)

    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.search(query, time_filter=time_filter, limit=per_sub_limit):
                post_data = {
                    "subreddit": sub_name,
                    "title": post.title,
                    "selftext": (post.selftext or "")[:2000],
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": f"https://reddit.com{post.permalink}",
                    "created_utc": post.created_utc,
                    "top_comments": [],
                }
                # Grab top comments
                try:
                    post.comment_sort = "top"
                    post.comments.replace_more(limit=0)
                    for comment in post.comments[:5]:
                        post_data["top_comments"].append({
                            "body": (comment.body or "")[:1000],
                            "score": comment.score,
                        })
                except Exception:
                    pass
                results.append(post_data)
        except Exception as e:
            logger.warning(f"Error searching r/{sub_name}: {e}")

    logger.info(f"PRAW returned {len(results)} posts for query: {query!r}")
    return results


def _tavily_reddit_fallback(query: str, subreddits: list[str], limit: int) -> list[dict]:
    """Fallback: search Reddit via Tavily web search."""
    from tools.web_search import web_search

    results = []
    sub_str = " OR ".join(f"site:reddit.com/r/{s}" for s in subreddits[:3])
    tavily_results = web_search(f"{query} {sub_str}", max_results=min(limit, 10))
    for r in tavily_results:
        results.append({
            "subreddit": "unknown",
            "title": r.get("title", ""),
            "selftext": r.get("content", "")[:2000],
            "score": 0,
            "num_comments": 0,
            "url": r.get("url", ""),
            "created_utc": 0,
            "top_comments": [],
        })
    return results
