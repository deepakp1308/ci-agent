"""Master orchestrator — runs both jobs and produces the final report."""

import os
import asyncio
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from typing import Dict, List, Optional, Tuple

from agents.product_intel import run_product_intel
from agents.sentiment_trend import run_sentiment_trend
from synthesizers.analytics_lens import synthesize_analytics_lens
from reports.html_generator import generate_html_report
from reports.pdf_generator import generate_pdf_report
from storage.db import log_report_run

logger = logging.getLogger(__name__)

COMPETITORS = ["klaviyo", "hubspot"]


def get_week_iso() -> str:
    """Get current ISO week string like '2026-W12'."""
    now = datetime.now()
    return now.strftime("%G-W%V")


def run_full_report(
    triggered_by: str = "manual",
    competitors: Optional[List[str]] = None,
    dry_run: bool = False,
) -> dict:
    """Run the full CI report pipeline.

    Args:
        triggered_by: 'scheduler', 'slack', or 'manual'
        competitors: list of competitor keys to run (default: all)
        dry_run: if True, skip API calls and use placeholder data

    Returns:
        dict with html_path, pdf_path, briefs, sentiments, analytics_lens
    """
    if competitors is None:
        competitors = COMPETITORS

    week_iso = get_week_iso()
    today = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"{'=' * 60}")
    logger.info(f"CI REPORT: {week_iso} | Triggered by: {triggered_by}")
    logger.info(f"Competitors: {', '.join(competitors)}")
    logger.info(f"{'=' * 60}")

    if dry_run:
        logger.info("DRY RUN — using placeholder data")
        briefs, sentiments = _dry_run_data(competitors, week_iso)
        analytics_lens = {
            "analytics_ai_implications": {"summary": "[DRY RUN] Placeholder analytics lens."},
            "start_doing": ["Placeholder: start doing X"],
            "stop_doing": ["Placeholder: stop doing Y"],
            "continue_doing": ["Placeholder: continue doing Z"],
        }
    else:
        briefs, sentiments = _run_parallel_jobs(competitors, week_iso)
        # Analytics lens synthesis (cross-competitor)
        logger.info("Synthesizing analytics & AI lens...")
        analytics_lens = synthesize_analytics_lens(briefs)

    # Generate reports
    logger.info("Generating HTML report...")
    report_dir = os.path.join(
        os.environ.get("REPORT_OUTPUT_DIR", "./reports"),
        week_iso.replace("-", "/"),
    )
    os.makedirs(report_dir, exist_ok=True)

    html_path = os.path.join(report_dir, f"ci-report-{week_iso}.html")
    pdf_path = os.path.join(report_dir, f"ci-report-{week_iso}.pdf")

    generate_html_report(
        briefs=briefs,
        sentiments=sentiments,
        analytics_lens=analytics_lens,
        week_iso=week_iso,
        output_path=html_path,
    )
    logger.info(f"HTML report saved: {html_path}")

    logger.info("Generating PDF report...")
    pdf_ok = generate_pdf_report(html_path, pdf_path)
    if not pdf_ok:
        logger.warning("PDF generation failed — HTML report is still available")
        pdf_path = ""

    # Log the run
    log_report_run(week_iso, triggered_by, html_path, pdf_path)

    result = {
        "week_iso": week_iso,
        "html_path": html_path,
        "pdf_path": pdf_path,
        "briefs": briefs,
        "sentiments": sentiments,
        "analytics_lens": analytics_lens,
    }

    logger.info(f"{'=' * 60}")
    logger.info(f"CI REPORT COMPLETE: {week_iso}")
    logger.info(f"HTML: {html_path}")
    logger.info(f"PDF: {pdf_path or 'N/A'}")
    logger.info(f"{'=' * 60}")

    return result


def _run_parallel_jobs(
    competitors,
    week_iso,
):
    """Run jobs sequentially to avoid API rate limits and Ollama contention."""
    briefs = {}
    sentiments = {}

    for comp in competitors:
        # Product intel first
        logger.info(f"Running product intel for {comp}...")
        try:
            briefs[comp] = run_product_intel(comp, week_iso)
        except Exception as e:
            logger.error(f"Product intel failed for {comp}: {e}")
            briefs[comp] = {
                "competitor": comp,
                "week_of": week_iso,
                "error": str(e),
                "exec_summary": f"Data unavailable — product intel failed: {e}",
            }

        # Then sentiment
        logger.info(f"Running sentiment trend for {comp}...")
        try:
            sentiments[comp] = run_sentiment_trend(comp, week_iso)
        except Exception as e:
            logger.error(f"Sentiment trend failed for {comp}: {e}")
            sentiments[comp] = {
                "competitor": comp,
                "week_of": week_iso,
                "error": str(e),
                "overall_sentiment": "unknown",
                "sentiment_score": 0.0,
            }

    return briefs, sentiments


def _dry_run_data(competitors: list[str], week_iso: str) -> tuple[dict, dict]:
    """Generate placeholder data for dry runs."""
    briefs = {}
    sentiments = {}

    for comp in competitors:
        briefs[comp] = {
            "competitor": comp.title(),
            "week_of": week_iso,
            "new_launches": [{"name": "Sample Feature", "description": "Dry run placeholder", "target_icp": "SMB", "value_prop": "N/A"}],
            "feature_updates": [],
            "core_value_prop": "Dry run — no real data gathered.",
            "top_pages_resonance": [],
            "icp_targeting": {"doubling_down": [], "steady": [], "loosening": []},
            "trajectory_6mo": "Dry run — no trajectory data.",
            "earnings_investor_notes": None,
            "analytics_ai_watch": {
                "what_theyre_doing": "Dry run placeholder",
                "start_doing": ["Placeholder action"],
                "stop_doing": [],
                "continue_doing": [],
            },
            "exec_summary": f"[DRY RUN] This is placeholder data for {comp.title()}. Run without --dry-run for real intelligence.",
        }
        sentiments[comp] = {
            "competitor": comp.title(),
            "week_of": week_iso,
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "sentiment_delta_vs_last_week": 0.0,
            "top_loves": [],
            "top_hates": [],
            "steady_issues": [],
            "analytics_reporting_sentiment": {
                "summary": "Dry run",
                "specific_complaints": [],
                "specific_praise": [],
                "data_accuracy_issues": [],
                "data_availability_issues": [],
            },
            "ai_agent_sentiment": {"summary": "Dry run", "specific_complaints": [], "specific_praise": []},
            "mailchimp_mentions": [],
            "opportunity_signals": [],
        }

    return briefs, sentiments


def get_exec_summaries(briefs: dict, sentiments: dict) -> str:
    """Format executive summaries for Slack inline posting."""
    lines = []
    for comp_key, brief in briefs.items():
        name = brief.get("competitor", comp_key.title())
        summary = brief.get("exec_summary", "No summary available.")
        sentiment = sentiments.get(comp_key, {})
        score = sentiment.get("sentiment_score", "N/A")
        overall = sentiment.get("overall_sentiment", "unknown")
        lines.append(f"*{name}*\n{summary}\nSentiment: {overall} ({score})\n")
    return "\n".join(lines)
