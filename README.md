# CI Agent — Competitive Intelligence Report Generator

Automated competitive intelligence agent that generates weekly executive-grade reports comparing **Klaviyo** and **HubSpot** against **Mailchimp R&A**. Built for product managers who need actionable competitor insights without the manual research grind.

## What It Does

Every week (or on demand), CI Agent:

1. **Searches** the web for product updates, feature launches, earnings data, and pricing changes
2. **Crawls** competitor product pages for latest capabilities
3. **Analyzes sentiment** from Reddit, social media, and review sites
4. **Synthesizes** everything through a local LLM into structured executive briefs
5. **Generates** a polished HTML + PDF report with actionable recommendations

### Report Contents

- **Product Intelligence** — new launches, feature updates, ICP targeting shifts, earnings/investor signals
- **Analytics Deep Dive** — reporting capabilities, attribution models, data accuracy, custom reports, real-time vs batch
- **Omnichannel Analysis** — channel coverage, cross-channel capabilities, CDP features
- **Email/Content Builder** — editor types, AI content features, personalization, template ecosystem
- **Sentiment Analysis** — top loves/hates from Reddit + web, churn signals, opportunity gaps
- **Executive Analytics Lens** — cross-competitor landscape analysis with start/stop/continue recommendations
- **Risk Matrix** — threat levels and 90-day priority actions

## Prerequisites

- **Python 3.9+**
- **Ollama** with `gemma3:12b` model (runs locally, free, no API costs for LLM)
- **Tavily API key** (web search)
- **Firecrawl API key** (web crawling)

### Optional

- Reddit API credentials (for direct Reddit access — falls back to Tavily web search if missing)
- Slack bot tokens (for Slack bot mode)
- SimilarWeb API key (for traffic estimation)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/deepakp1308/ci-agent.git
cd ci-agent

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Install and start Ollama
# Download from https://ollama.com
ollama pull gemma3:12b
ollama serve  # keep this running

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys (at minimum: TAVILY_API_KEY, FIRECRAWL_API_KEY)

# 5. Run the report
python3 main.py --run-now
```

Reports are saved to `./reports/<year>/W<week>/`.

## Usage

### CLI

```bash
# Full report (all competitors) — takes ~15 minutes
python3 main.py --run-now

# Single competitor
python3 main.py --run-now --competitors klaviyo
python3 main.py --run-now --competitors hubspot

# Both competitors explicitly
python3 main.py --run-now --competitors klaviyo,hubspot

# Dry run (placeholder data, no API calls)
python3 main.py --run-now --dry-run

# Initialize database only
python3 main.py --init-db
```

### Claude Code

Open Claude Code in the `ci-agent` directory and say:

> "run my competitor agent report"

Or for a specific competitor:

> "run the competitor report for klaviyo only"

### Slack Bot

```bash
# Start with Slack bot + weekly scheduler
python3 main.py

# Scheduler only (no Slack)
python3 main.py --no-slack
```

**Slack commands** (mention the bot):
- `@ci-agent run-report` — Run full report
- `@ci-agent run-report klaviyo` — Run for one competitor
- `@ci-agent status` — Show last run info
- `@ci-agent history 4` — Show last 4 weeks

### Scheduled Runs

The built-in scheduler runs automatically every **Monday at 7:00 AM UTC** when the bot is running.

## Architecture

```
ci-agent/
├── main.py                          # Entry point — CLI, Slack bot, scheduler
│
├── agents/
│   ├── orchestrator.py              # Pipeline coordinator
│   ├── product_intel.py             # Product feature & earnings gathering
│   └── sentiment_trend.py           # Reddit & social sentiment gathering
│
├── synthesizers/
│   ├── competitor_brief.py          # Per-competitor executive brief (LLM)
│   ├── sentiment_synth.py           # Per-competitor sentiment report (LLM)
│   └── analytics_lens.py           # Cross-competitor strategic analysis (LLM)
│
├── tools/
│   ├── llm.py                       # Ollama local LLM (gemma3:12b)
│   ├── web_search.py                # Tavily search (rate-limited, retries)
│   ├── web_crawler.py               # Firecrawl scraper (Tavily fallback)
│   ├── earnings_tool.py             # Earnings call & investor data search
│   ├── reddit_tool.py               # Reddit via PRAW (Tavily fallback)
│   └── traffic_tool.py              # SimilarWeb traffic (optional)
│
├── reports/
│   ├── html_generator.py            # Jinja2 HTML report
│   ├── pdf_generator.py             # Playwright PDF conversion
│   └── templates/
│       └── weekly_report.html       # Dark-themed report template
│
├── storage/
│   └── db.py                        # SQLite — snapshots, history, run logs
│
├── scheduler/
│   └── cron.py                      # APScheduler weekly cron
│
├── .env.example                     # Required environment variables
└── requirements.txt                 # Python dependencies
```

### Pipeline Flow

```
Orchestrator
  ├── Product Intel Agent (per competitor)
  │   ├── Web Search (Tavily) — 12 discovery queries
  │   ├── Website Crawl (Firecrawl) — product/features/pricing pages
  │   ├── Earnings Search — investor relations, SeekingAlpha
  │   ├── Deep Dive Search — 5 focused queries
  │   ├── History Lookup — last 12 weeks from SQLite
  │   └── LLM Synthesis → Executive Brief JSON
  │
  ├── Sentiment Agent (per competitor)
  │   ├── Reddit Search — 14 queries across subreddits
  │   ├── Web Social Signals — 8 search queries
  │   ├── History Lookup — last 12 weeks from SQLite
  │   └── LLM Synthesis → Sentiment Report JSON
  │
  ├── Analytics Lens Synthesis (cross-competitor)
  │   └── LLM Synthesis → Strategic Analysis JSON
  │
  └── Report Generation
      ├── HTML (Jinja2 template)
      └── PDF (Playwright headless Chromium)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TAVILY_API_KEY` | Yes | Web search API key ([tavily.com](https://tavily.com)) |
| `FIRECRAWL_API_KEY` | Yes | Web crawling API key ([firecrawl.dev](https://firecrawl.dev)) |
| `REDDIT_CLIENT_ID` | No | Reddit API client ID (falls back to Tavily) |
| `REDDIT_CLIENT_SECRET` | No | Reddit API client secret |
| `REDDIT_USER_AGENT` | No | Reddit API user agent (default: `ci-agent/1.0`) |
| `SLACK_BOT_TOKEN` | No | Slack bot token (for Slack mode) |
| `SLACK_APP_TOKEN` | No | Slack app token (for Socket Mode) |
| `SIMILARWEB_API_KEY` | No | SimilarWeb traffic data (graceful skip if missing) |
| `REPORT_OUTPUT_DIR` | No | Report output path (default: `./reports`) |
| `DB_PATH` | No | SQLite database path (default: `./storage/ci_agent.db`) |

## LLM Configuration

CI Agent uses **Ollama** with `gemma3:12b` running locally. This means:

- **No LLM API costs** — everything runs on your machine
- **No data leaves your network** — all synthesis is local
- Requires ~8GB RAM for the 12B model
- Each synthesis call takes ~2-3 minutes on Apple Silicon

To use a different model, edit `tools/llm.py`:

```python
MODEL = "gemma3:12b"  # Change this to any Ollama model
```

## Output

Reports are saved to `./reports/<year>/W<week>/`:

- `ci-report-<year>-W<week>.html` — Interactive dark-themed HTML report
- `ci-report-<year>-W<week>.pdf` — Print-ready PDF version

Historical data is stored in SQLite (`./storage/ci_agent.db`) for trend analysis across weeks.

## Customization

### Adding a Competitor

Edit `agents/product_intel.py` and `agents/sentiment_trend.py`:

1. Add competitor config to `COMPETITOR_CONFIG` / `SENTIMENT_CONFIG`
2. Add the competitor key to `COMPETITORS` list in `agents/orchestrator.py`
3. Add color badge in `reports/templates/weekly_report.html`

### Changing Search Queries

Each competitor has configurable search queries in:
- `agents/product_intel.py` — `COMPETITOR_CONFIG[key]["search_queries"]`
- `agents/sentiment_trend.py` — `SENTIMENT_CONFIG[key]["queries"]`

### Changing the Report Template

Edit `reports/templates/weekly_report.html` (Jinja2 template with embedded CSS).

## License

MIT
