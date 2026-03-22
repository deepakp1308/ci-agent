"""PDF generator using Playwright (headless Chromium). No system deps needed."""

import os
import logging

logger = logging.getLogger(__name__)


def generate_pdf_report(html_path: str, pdf_path: str) -> bool:
    """Generate PDF from HTML report using Playwright headless Chromium.
    Returns True on success, False on failure."""
    try:
        from playwright.sync_api import sync_playwright

        abs_html = os.path.abspath(html_path)
        abs_pdf = os.path.abspath(pdf_path)

        logger.info(f"Generating PDF: {abs_html} -> {abs_pdf}")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{abs_html}", wait_until="networkidle")
            page.pdf(
                path=abs_pdf,
                format="A4",
                print_background=True,
                margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"},
            )
            browser.close()

        logger.info(f"PDF report generated: {abs_pdf}")
        return True
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False
