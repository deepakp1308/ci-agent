#!/usr/bin/env python3
"""CI Agent — Entry point: Slack bot + scheduler + CLI."""

import os
import sys
import signal
import logging
import argparse
from datetime import datetime
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

# Configure logging
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            os.path.join(LOG_DIR, "ci_agent.log"),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        ),
    ],
)
logger = logging.getLogger("ci-agent")


def parse_args():
    parser = argparse.ArgumentParser(description="Competitive Intelligence Agent")
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize the SQLite database schema and exit",
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run a full report immediately (no Slack trigger needed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test with placeholder data, no live API calls",
    )
    parser.add_argument(
        "--competitors",
        type=str,
        default=None,
        help="Comma-separated list of competitors to run (e.g., 'klaviyo,hubspot')",
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Skip starting the Slack bot (run scheduler only)",
    )
    return parser.parse_args()


def init_database():
    """Initialize the SQLite database."""
    from storage.db import init_db
    init_db()
    logger.info("Database initialized successfully")


def run_immediate(competitors=None, dry_run=False):
    """Run a report immediately from CLI."""
    from agents.orchestrator import run_full_report

    comp_list = None
    if competitors:
        comp_list = [c.strip().lower() for c in competitors.split(",")]

    result = run_full_report(
        triggered_by="cli",
        competitors=comp_list,
        dry_run=dry_run,
    )
    print(f"\nReport generated!")
    print(f"  HTML: {result['html_path']}")
    print(f"  PDF:  {result.get('pdf_path') or 'N/A (WeasyPrint not available)'}")
    return result


def start_slack_bot():
    """Start the Slack bot with Socket Mode."""
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    app_token = os.environ.get("SLACK_APP_TOKEN")

    if not bot_token or not app_token:
        logger.error("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set for Slack bot")
        return None

    app = App(token=bot_token)

    @app.event("app_mention")
    def handle_mention(event, say, client):
        """Handle @ci-agent mentions in Slack."""
        text = event.get("text", "").lower()
        thread_ts = event.get("ts")
        channel = event.get("channel")

        if "run-report" in text:
            _handle_run_report(text, say, client, channel, thread_ts)
        elif "status" in text:
            _handle_status(say, thread_ts)
        elif "history" in text:
            _handle_history(text, say, thread_ts)
        else:
            say(
                text=(
                    "Available commands:\n"
                    "- `@ci-agent run-report` — Run full report for all competitors\n"
                    "- `@ci-agent run-report klaviyo` — Run for specific competitor\n"
                    "- `@ci-agent status` — Show last run info\n"
                    "- `@ci-agent history 4` — Show last 4 weeks of summaries"
                ),
                thread_ts=thread_ts,
            )

    @app.event("message")
    def handle_message(event):
        """Acknowledge DMs (no-op to prevent errors)."""
        pass

    handler = SocketModeHandler(app, app_token)
    return handler


def _handle_run_report(text, say, client, channel, thread_ts):
    """Handle the run-report command."""
    from agents.orchestrator import run_full_report, get_exec_summaries

    # Parse competitor filter
    competitors = None
    words = text.split()
    for i, word in enumerate(words):
        if word == "run-report" and i + 1 < len(words):
            comp = words[i + 1].strip().lower()
            if comp in ("klaviyo", "hubspot"):
                competitors = [comp]

    week_iso = datetime.now().strftime("%G-W%V")
    say(
        text=f"Starting CI report for week of {week_iso}. This takes ~3-5 minutes...",
        thread_ts=thread_ts,
    )

    try:
        result = run_full_report(
            triggered_by="slack",
            competitors=competitors,
        )

        # Upload files
        html_path = result.get("html_path", "")
        pdf_path = result.get("pdf_path", "")

        if html_path and os.path.exists(html_path):
            client.files_upload_v2(
                channel=channel,
                file=html_path,
                filename=os.path.basename(html_path),
                title=f"CI Report {week_iso} (HTML)",
                thread_ts=thread_ts,
            )

        if pdf_path and os.path.exists(pdf_path):
            client.files_upload_v2(
                channel=channel,
                file=pdf_path,
                filename=os.path.basename(pdf_path),
                title=f"CI Report {week_iso} (PDF)",
                thread_ts=thread_ts,
            )

        # Post inline summaries
        summaries = get_exec_summaries(result["briefs"], result["sentiments"])
        say(
            text=f"Report ready!\n\n{summaries}",
            thread_ts=thread_ts,
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        say(
            text=f"Report generation failed: {e}",
            thread_ts=thread_ts,
        )


def _handle_status(say, thread_ts):
    """Handle the status command."""
    from storage.db import get_last_run

    last_run = get_last_run()
    if last_run:
        say(
            text=(
                f"*Last Run*\n"
                f"Week: {last_run['week_iso']}\n"
                f"Triggered by: {last_run['triggered_by']}\n"
                f"Time: {last_run['created_at']}\n"
                f"HTML: {last_run.get('html_path', 'N/A')}\n"
                f"PDF: {last_run.get('pdf_path', 'N/A')}"
            ),
            thread_ts=thread_ts,
        )
    else:
        say(text="No reports have been generated yet.", thread_ts=thread_ts)


def _handle_history(text, say, thread_ts):
    """Handle the history command."""
    from storage.db import get_recent_runs

    # Parse number of weeks
    n = 4
    words = text.split()
    for i, word in enumerate(words):
        if word == "history" and i + 1 < len(words):
            try:
                n = int(words[i + 1])
            except ValueError:
                pass

    runs = get_recent_runs(n)
    if not runs:
        say(text="No report history available.", thread_ts=thread_ts)
        return

    lines = [f"*Last {len(runs)} Report Runs:*\n"]
    for run in runs:
        lines.append(
            f"- {run['week_iso']} | {run['triggered_by']} | {run['created_at']}"
        )
    say(text="\n".join(lines), thread_ts=thread_ts)


def main():
    args = parse_args()

    # Always ensure DB exists
    init_database()

    if args.init_db:
        print("Database initialized. Exiting.")
        return

    if args.run_now:
        run_immediate(competitors=args.competitors, dry_run=args.dry_run)
        return

    # Start scheduler
    from scheduler.cron import start_scheduler, stop_scheduler

    start_scheduler()

    # Start Slack bot (blocking)
    if not args.no_slack:
        handler = start_slack_bot()
        if handler:
            def shutdown(signum, frame):
                logger.info("Shutting down...")
                stop_scheduler()
                sys.exit(0)

            signal.signal(signal.SIGINT, shutdown)
            signal.signal(signal.SIGTERM, shutdown)

            logger.info("CI Agent started — Slack bot + scheduler running")
            handler.start()
        else:
            logger.warning("Slack bot not started (missing tokens). Running scheduler only.")
            _run_forever(stop_scheduler)
    else:
        logger.info("CI Agent started — scheduler only (no Slack)")
        _run_forever(stop_scheduler)


def _run_forever(cleanup_fn):
    """Keep the process alive for the scheduler."""
    import time

    def shutdown(signum, frame):
        logger.info("Shutting down...")
        cleanup_fn()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        cleanup_fn()


if __name__ == "__main__":
    main()
