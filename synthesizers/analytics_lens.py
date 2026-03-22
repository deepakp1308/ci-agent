"""Analytics & AI lens synthesizer — executive-grade cross-competitor analysis for Deepak."""

import json
import logging

from tools.llm import generate_json

logger = logging.getLogger(__name__)

ANALYTICS_LENS_PROMPT = """You are a senior strategy consultant writing for the Group Product Manager of Reporting & Analytics at Mailchimp (Intuit).
The PM (Deepak) owns: Marketing Analytics, Reporting Dashboards, Data Visualization, AI Agents, and is expanding into omnichannel analytics.

Given the competitive intelligence briefs below, produce an executive-ready JSON:

{
  "executive_brief": string (3-4 paragraph strategic brief suitable for an executive review. Lead with the most important competitive threat. Include specific numbers, feature names, and competitive positioning. End with clear recommendation.),

  "analytics_reporting_landscape": {
    "summary": string (2 paragraphs: state of analytics/reporting across competitors vs Mailchimp),
    "competitor_strengths": [ string ] (specific analytics features where competitors are ahead — name the feature AND the competitor),
    "competitor_weaknesses": [ string ] (specific analytics gaps competitors have — opportunities for Mailchimp),
    "data_accuracy_comparison": string (how each competitor fares on data accuracy based on user signals),
    "attribution_comparison": string (how attribution models compare across competitors),
    "custom_reporting_comparison": string (report builder capabilities comparison),
    "real_time_data_comparison": string (data freshness comparison)
  },

  "omnichannel_landscape": {
    "summary": string (state of omnichannel across competitors),
    "channel_comparison": string (which channels each competitor supports and how well),
    "cross_channel_analytics_gap": string (where cross-channel analytics is weakest — Mailchimp opportunity),
    "cdp_comparison": string (customer data platform capabilities across competitors)
  },

  "email_content_builder_landscape": {
    "summary": string (state of email/content builders across competitors),
    "ai_content_comparison": string (AI writing/generation features compared),
    "editor_comparison": string (drag-drop builders compared),
    "personalization_comparison": string (dynamic content capabilities compared)
  },

  "ai_agent_landscape": {
    "summary": string (what competitors are doing with AI agents and copilots),
    "biggest_ai_threat": string (which competitor's AI move is most threatening and why),
    "ai_adoption_reality": string (are users actually using these AI features based on sentiment data?)
  },

  "start_doing": [ string ] (5-7 specific, actionable items. Each must reference a specific competitive signal. Format: "ACTION because EVIDENCE"),
  "stop_doing": [ string ] (3-4 things to deprioritize. Each must reference competitive evidence),
  "continue_doing": [ string ] (3-4 things validated by competitor gaps. Format: "CONTINUE X because EVIDENCE"),

  "key_battlegrounds": [ string ] (top 5 specific areas where competition is intensifying — ranked by threat level),

  "90_day_priorities": [ string ] (top 3 things Deepak should prioritize in the next 90 days based on this competitive intelligence),

  "risk_matrix": {
    "high_risk": [ string ] (competitive moves that could materially impact Mailchimp R&A in 6 months),
    "medium_risk": [ string ] (moves to monitor but not urgent),
    "low_risk": [ string ] (moves that are unlikely to impact Mailchimp)
  }
}

RULES:
- Be specific and quantitative. "Invest in custom reporting" is bad. "Build drag-drop custom report builder with SQL export — Klaviyo launched this in Q1 and HubSpot users cite lack of it as #1 complaint" is good.
- Every recommendation must cite the competitive evidence behind it
- Compare to Mailchimp explicitly
- This is for a PM making product bets — be direct and opinionated
- Return ONLY the JSON object"""


def synthesize_analytics_lens(briefs: dict) -> dict:
    """Produce executive-grade cross-competitor analysis."""
    context = json.dumps(briefs, indent=2, default=str)[:15000]

    logger.info("Synthesizing executive analytics & AI lens...")
    result = generate_json(ANALYTICS_LENS_PROMPT, context)

    if "error" in result and len(result) == 1:
        logger.error(f"Analytics lens synthesis failed: {result['error']}")
        return {
            "executive_brief": f"Synthesis error: {result['error']}",
            "start_doing": [],
            "stop_doing": [],
            "continue_doing": [],
        }

    logger.info("Executive analytics lens synthesized successfully")
    return result
