"""Jinja2 HTML report generator."""

import os
import logging
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def generate_html_report(
    briefs: dict,
    sentiments: dict,
    analytics_lens: dict,
    week_iso: str,
    output_path: str,
) -> str:
    """Generate the HTML report from templates and data. Returns the output path."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=True,
    )
    template = env.get_template("weekly_report.html")

    html = template.render(
        briefs=briefs,
        sentiments=sentiments,
        analytics_lens=analytics_lens,
        week_iso=week_iso,
        today=datetime.now().strftime("%B %d, %Y"),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"HTML report generated: {output_path}")
    return output_path
