"""Sentiment trend synthesizer — executive-grade VOC analysis."""

import json
import logging

from tools.llm import generate_json

logger = logging.getLogger(__name__)

SENTIMENT_PROMPT = """You are a senior product intelligence analyst writing a VOC (Voice of Customer) report for a C-suite audience.
Your analysis of {competitor} must be specific, evidence-based, and quantitative. Every insight must cite specific posts, quotes, or patterns.

Produce a JSON object:

{{
  "competitor": "{competitor}",
  "week_of": "{week_of}",
  "overall_sentiment": "positive" | "neutral" | "negative" | "mixed",
  "sentiment_score": float (-1.0 to 1.0),
  "sentiment_delta_vs_last_week": float,

  "top_loves": [ {{ "theme": string, "frequency": string (e.g. "12 mentions"), "example_quote": string (exact user quote), "trend": "up"|"steady"|"down", "implication_for_mailchimp": string }} ],

  "top_hates": [ {{ "theme": string, "frequency": string, "example_quote": string (exact user quote), "trend": "up"|"steady"|"down", "severity": "critical"|"major"|"minor", "implication_for_mailchimp": string }} ],

  "steady_issues": [ {{ "issue": string, "how_long_present": string, "severity": "critical"|"major"|"minor", "user_workarounds": string }} ],

  "analytics_reporting_sentiment": {{
    "summary": string (2-3 paragraphs with specific examples),
    "specific_complaints": [ string ] (exact user complaints with quotes),
    "specific_praise": [ string ] (exact user praise with quotes),
    "data_accuracy_issues": [ string ] (specific accuracy/reliability complaints),
    "data_availability_issues": [ string ] (what data users wish they had),
    "custom_reporting_feedback": [ string ] (what users say about report builder),
    "attribution_complaints": [ string ] (attribution model frustrations),
    "comparison_to_mailchimp": string (any direct comparisons users make)
  }},

  "omnichannel_sentiment": {{
    "summary": string (what users say about cross-channel capabilities),
    "sms_feedback": [ string ],
    "cross_channel_complaints": [ string ],
    "channel_gaps_users_mention": [ string ]
  }},

  "email_builder_sentiment": {{
    "summary": string (what users say about the email/content builder),
    "editor_complaints": [ string ],
    "editor_praise": [ string ],
    "template_feedback": [ string ],
    "ai_content_feedback": [ string ]
  }},

  "ai_agent_sentiment": {{
    "summary": string,
    "specific_complaints": [ string ],
    "specific_praise": [ string ],
    "adoption_signals": string (are users actually using AI features?)
  }},

  "mailchimp_mentions": [ string ] (any mentions of Mailchimp in same threads - exact quotes),

  "churn_signals": [ string ] (users saying they switched away or are considering switching - with context),

  "opportunity_signals": [ string ] (5-8 specific gaps this competitor is NOT addressing that Mailchimp could exploit - be specific and actionable)
}}

RULES:
- Use exact quotes from posts where possible (in quotation marks)
- Quantify frequency: "mentioned 8 times" not "frequently mentioned"
- Every opportunity signal must be tied to a specific user complaint or gap
- Compare to Mailchimp explicitly where users do so
- Return ONLY the JSON object"""


def synthesize_sentiment(
    competitor: str,
    week_of: str,
    reddit_data: list,
    social_data: list,
    history: list,
) -> dict:
    """Synthesize sentiment data into executive-grade analysis."""
    prompt = SENTIMENT_PROMPT.format(competitor=competitor, week_of=week_of)

    # Condense for local model
    condensed_reddit = []
    for p in reddit_data[:30]:
        entry = {
            "title": p.get("title", "")[:200],
            "text": p.get("selftext", "")[:400],
            "score": p.get("score", 0),
            "subreddit": p.get("subreddit", ""),
            "num_comments": p.get("num_comments", 0),
        }
        top_comments = p.get("top_comments", [])[:3]
        if top_comments:
            entry["top_comments"] = [c.get("body", "")[:300] for c in top_comments]
        condensed_reddit.append(entry)

    condensed_social = []
    for s in social_data[:15]:
        condensed_social.append({
            "title": s.get("title", "")[:200],
            "snippet": s.get("content", "")[:400],
        })

    context = f"""=== REDDIT DATA ({len(reddit_data)} posts, showing top 30) ===
{json.dumps(condensed_reddit, indent=2, default=str)[:10000]}

=== SOCIAL/WEB SIGNALS ({len(social_data)} sources) ===
{json.dumps(condensed_social, indent=2, default=str)[:4000]}

=== SENTIMENT HISTORY (prior weeks) ===
{json.dumps(history[:4], indent=2, default=str)[:2000]}
"""

    logger.info(f"Synthesizing executive sentiment for {competitor}...")
    result = generate_json(prompt, context)

    if "error" in result and len(result) == 1:
        logger.error(f"Sentiment synthesis failed for {competitor}: {result['error']}")
        return {
            "competitor": competitor,
            "week_of": week_of,
            "overall_sentiment": "unknown",
            "sentiment_score": 0.0,
            "error": result["error"],
        }

    logger.info(f"Executive sentiment synthesized for {competitor} (score={result.get('sentiment_score', 'N/A')})")
    return result
