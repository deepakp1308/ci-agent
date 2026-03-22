"""Competitor brief synthesizer — executive-grade structured intelligence."""

import json
import logging

from tools.llm import generate_json

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """You are a senior competitive intelligence analyst at McKinsey writing for a C-suite audience.
Your output must be executive-ready: specific, quantitative, and actionable. Every claim must cite a specific source, page, data point, or quote. No vague language. No filler.

Based on the gathered intelligence data below, produce a JSON object with these exact fields:

{
  "competitor": string,
  "week_of": string,

  "exec_summary": string (4-6 sentences. Lead with the single most important competitive signal this week. Include at least 2 specific numbers — revenue, customer count, pricing, feature metrics, market share estimates. End with the strategic implication for Mailchimp R&A.),

  "key_metrics": {
    "estimated_arr": string (latest ARR or revenue figure with source),
    "customer_count": string (latest customer count with source),
    "market_position": string (market share or ranking if available),
    "pricing_range": string (key pricing tiers with specifics),
    "yoy_growth": string (revenue or customer growth rate if available)
  },

  "analytics_reporting": {
    "current_capabilities": [ string ] (specific analytics/reporting features they offer — name each one precisely),
    "recent_changes": [ string ] (any updates to analytics/reporting this quarter),
    "known_gaps": [ string ] (weaknesses or missing capabilities based on user feedback and competitive analysis),
    "data_accuracy_reputation": string (what users say about their data accuracy, with specific examples),
    "attribution_model": string (how they handle attribution — first touch, last touch, multi-touch, etc.),
    "custom_reporting": string (capabilities for custom report building — drag-drop, SQL, templates, etc.),
    "real_time_vs_batch": string (how fresh is their data — real-time, hourly, daily refresh?),
    "competitive_advantage_vs_mailchimp": string (where they are ahead of Mailchimp in analytics)
  },

  "omnichannel": {
    "channels_supported": [ string ] (every channel: email, SMS, push, WhatsApp, social, ads, etc.),
    "cross_channel_capabilities": string (how well channels work together — unified profiles, cross-channel flows, etc.),
    "recent_channel_additions": [ string ] (any new channels added recently),
    "cdp_capabilities": string (customer data platform features — unified profiles, identity resolution, etc.),
    "competitive_advantage_vs_mailchimp": string (where they beat Mailchimp in omnichannel)
  },

  "email_content_builder": {
    "editor_type": string (drag-drop, code, hybrid, AI-assisted),
    "ai_content_features": [ string ] (AI writing, subject line generation, send time optimization, etc.),
    "template_ecosystem": string (number of templates, marketplace, custom templates),
    "personalization_capabilities": [ string ] (dynamic content, conditional blocks, merge tags, product recs),
    "recent_updates": [ string ] (changes to email/content builder this quarter),
    "competitive_advantage_vs_mailchimp": string (where they beat Mailchimp in email/content)
  },

  "new_launches": [ { "name": string, "description": string (2-3 sentences with specifics), "target_icp": string, "value_prop": string, "threat_level_to_mailchimp": "high" | "medium" | "low" } ],

  "feature_updates": [ { "feature": string, "change": string, "significance": "major" | "moderate" | "minor", "impact_on_mailchimp": string } ],

  "icp_targeting": {
    "primary_segments": [ string ] (who they are targeting most aggressively),
    "doubling_down": [ string ] (segments getting more investment),
    "loosening": [ string ] (segments getting less focus),
    "pricing_strategy_signal": string (going upmarket, downmarket, or holding?)
  },

  "trajectory_6mo": string (2-3 paragraph analysis. Include specific product bets they are making, investment areas based on earnings/hiring signals, and what this means for their competitive position. Reference specific features and timelines where possible.),

  "earnings_investor_notes": string (key financial metrics, guidance, management quotes on product strategy. Include specific numbers.),

  "start_stop_continue": {
    "start_doing": [ string ] (3-5 specific actions Mailchimp R&A should START — each one tied to a specific competitive signal discovered this week),
    "stop_doing": [ string ] (2-3 things to STOP or deprioritize based on competitor evidence),
    "continue_doing": [ string ] (2-3 things to CONTINUE — validated by competitor gaps)
  },

  "risk_assessment": string (1-2 paragraphs: what is the biggest competitive risk from this player in the next 6 months, specifically in analytics/reporting and AI?)
}

RULES:
- Every claim must reference a specific source, page, or data point from the gathered data
- Use actual numbers: revenue figures, customer counts, pricing tiers, feature counts, growth rates
- Name specific features — not "improved analytics" but "launched Custom Report Builder with drag-drop SQL query interface"
- Compare explicitly to Mailchimp where possible
- Be direct and opinionated — this is for a PM who needs to make product decisions
- Return ONLY the JSON object"""


def synthesize_competitor_brief(
    competitor: str,
    week_of: str,
    gathered_data: dict,
    history: list,
) -> dict:
    """Synthesize product intelligence into an executive-grade brief."""
    condensed = _condense_gathered_data(gathered_data)

    context = f"""COMPETITOR: {competitor}
WEEK OF: {week_of}

=== GATHERED INTELLIGENCE (condensed from {len(gathered_data.get('search_results', []))} search results, {len(gathered_data.get('crawled_pages', []))} crawled pages, {len(gathered_data.get('earnings_data', []))} earnings sources) ===
{json.dumps(condensed, indent=2, default=str)[:15000]}

=== HISTORICAL SNAPSHOTS (prior weeks) ===
{json.dumps(history[:4], indent=2, default=str)[:4000]}
"""

    logger.info(f"Synthesizing executive brief for {competitor}...")
    result = generate_json(SYNTHESIS_PROMPT, context)

    if "error" in result and len(result) == 1:
        logger.error(f"Synthesis failed for {competitor}: {result['error']}")
        return {
            "competitor": competitor,
            "week_of": week_of,
            "exec_summary": f"Synthesis failed: {result['error']}",
            "error": result["error"],
        }

    logger.info(f"Executive brief synthesized for {competitor}")
    return result


def _condense_gathered_data(gathered_data: dict) -> dict:
    """Condense raw gathered data — keep more detail for executive quality."""
    condensed = {"search_highlights": [], "page_summaries": [], "earnings": []}

    for r in gathered_data.get("search_results", [])[:30]:
        condensed["search_highlights"].append({
            "title": r.get("title", "")[:150],
            "snippet": r.get("content", "")[:400],
            "url": r.get("url", ""),
        })

    for p in gathered_data.get("crawled_pages", [])[:15]:
        condensed["page_summaries"].append({
            "title": p.get("title", "")[:150],
            "url": p.get("url", ""),
            "content_preview": p.get("content", "")[:600],
        })

    for e in gathered_data.get("earnings_data", [])[:8]:
        condensed["earnings"].append({
            "title": e.get("title", "")[:150],
            "snippet": e.get("content", "")[:500],
        })

    return condensed
