"""APScheduler weekly cron job for automated CI report runs."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = None  # type: BackgroundScheduler | None


def start_scheduler():
    """Start the weekly cron scheduler. Runs every Monday at 7:00 AM."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return _scheduler

    _scheduler = BackgroundScheduler()

    _scheduler.add_job(
        _run_scheduled_report,
        trigger=CronTrigger(day_of_week="mon", hour=7, minute=0),
        id="weekly_ci_report",
        name="Weekly CI Report",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started — weekly CI report: Mondays at 7:00 AM")
    return _scheduler


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")


def _run_scheduled_report():
    """Called by the scheduler to run the full report."""
    try:
        from agents.orchestrator import run_full_report

        logger.info("Scheduled run triggered")
        result = run_full_report(triggered_by="scheduler")
        logger.info(f"Scheduled report complete: {result.get('html_path', 'unknown')}")
    except Exception as e:
        logger.error(f"Scheduled report failed: {e}", exc_info=True)
