"""
VA/Veteran News RSS Scraper
The FOB Platform

Scrapes RSS feeds from major veteran news sources, categorizes articles
by keyword matching, and stores them in the database.
"""

import logging
import re
from datetime import datetime
from typing import Optional

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import NewsArticle

logger = logging.getLogger(__name__)

# ─── RSS Feed Sources ───

FEEDS = [
    {
        "name": "Military Times",
        "url": "https://www.militarytimes.com/arc/outboundfeeds/rss/category/veterans/?outputType=xml",
        "default_cat": "policy",
    },
    {
        "name": "Stars and Stripes",
        "url": "https://www.stripes.com/theaters/us",
        "default_cat": "policy",
    },
    {
        "name": "VA News",
        "url": "https://news.va.gov/feed/",
        "default_cat": "benefits",
    },
    {
        "name": "Military.com",
        "url": "https://www.military.com/rss-feeds/content?keyword=veteran",
        "default_cat": "employment",
    },
    {
        "name": "Veteran Affairs Blog",
        "url": "https://www.blogs.va.gov/VAntage/feed/",
        "default_cat": "benefits",
    },
    {
        "name": "Task and Purpose",
        "url": "https://taskandpurpose.com/feed/",
        "default_cat": "policy",
    },
    {
        "name": "DAV",
        "url": "https://www.dav.org/feed/",
        "default_cat": "benefits",
    },
]

# ─── Category Keywords ───
# Order matters: first match wins

CATEGORY_RULES = [
    ("doge", [
        r"\bdoge\b", r"efficiency\s+review", r"workforce\s+reduction",
        r"staffing\s+cut", r"government\s+efficiency",
    ]),
    ("healthcare", [
        r"\bhealthcare\b", r"\bhealth\s+care\b", r"\bmental\s+health\b",
        r"\btelehealth\b", r"\bmedical\b", r"\bvamc\b", r"\bhospital\b",
        r"\bcommunity\s+care\b", r"\bmission\s+act\b", r"\bwhole\s+health\b",
        r"\bptsd\b", r"\btbi\b", r"\bnursing\b", r"\bfertility\b",
    ]),
    ("education", [
        r"\bgi\s+bill\b", r"\beducation\b", r"\byellow\s+ribbon\b",
        r"\bvet\s+tec\b", r"\bscholarship\b", r"\btuition\b",
        r"\bapprenticeship\b", r"\btraining\b", r"\buniversity\b",
        r"\bcollege\b", r"\bmha\b",
    ]),
    ("employment", [
        r"\bskillbridge\b", r"\bemployment\b", r"\bhiring\b",
        r"\bjob\b", r"\bcareer\b", r"\bworkforce\b", r"\bfellowship\b",
        r"\btap\s+program\b", r"\btransition\b", r"\bapprentice\b",
    ]),
    ("benefits", [
        r"\bbenefit\b", r"\bdisability\b", r"\bclaim\b", r"\bpact\s+act\b",
        r"\btoxic\s+exposure\b", r"\bburn\s+pit\b", r"\bva\s+loan\b",
        r"\bcompensation\b", r"\brating\b", r"\bentitlement\b",
        r"\bcaregiver\b", r"\bsbp\b", r"\bsurvivor\b",
    ]),
    ("policy", [
        r"\bpolicy\b", r"\blegislation\b", r"\bbill\b", r"\bbudget\b",
        r"\bcongress\b", r"\bsenate\b", r"\bwhite\s+house\b",
        r"\bbipartisan\b", r"\bcommittee\b",
    ]),
]

# Compiled patterns for performance
_COMPILED_RULES = [
    (cat, [re.compile(p, re.IGNORECASE) for p in patterns])
    for cat, patterns in CATEGORY_RULES
]


def categorize_article(title: str, summary: str = "", default: str = "policy") -> str:
    """Categorize an article by keyword matching against title + summary."""
    text = f"{title} {summary}"
    for cat, patterns in _COMPILED_RULES:
        for pat in patterns:
            if pat.search(text):
                return cat
    return default


def _estimate_impact(title: str, summary: str = "") -> Optional[str]:
    """Heuristic impact rating based on keywords."""
    text = f"{title} {summary}".lower()
    high_signals = [
        "record", "billion", "largest", "all veteran", "nationwide",
        "emergency", "eliminated", "reduction", "at risk", "expansion",
    ]
    medium_signals = [
        "new", "update", "change", "adjust", "expand", "launch",
        "increase", "cut", "reform",
    ]
    for signal in high_signals:
        if signal in text:
            return "high"
    for signal in medium_signals:
        if signal in text:
            return "medium"
    return None


def _parse_published(entry) -> Optional[datetime]:
    """Extract published datetime from a feed entry (timezone-naive UTC)."""
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                from time import mktime
                # Return naive datetime (no tzinfo) for TIMESTAMP WITHOUT TIME ZONE
                dt = datetime.utcfromtimestamp(mktime(parsed))
                return dt
            except Exception:
                pass
    return None


def _clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:1000]  # cap summary length


def _get_image(entry) -> Optional[str]:
    """Try to extract an image URL from a feed entry."""
    # media:thumbnail or media:content
    for media in getattr(entry, "media_thumbnail", []):
        if media.get("url"):
            return media["url"]
    for media in getattr(entry, "media_content", []):
        if media.get("url"):
            return media["url"]
    # enclosure
    for enc in getattr(entry, "enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("href") or enc.get("url")
    return None


class NewsScraper:
    """Scrapes RSS feeds and stores articles in the database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def scrape_all(self) -> dict:
        """Scrape all configured feeds. Returns summary stats."""
        # Prune articles older than 7 days
        try:
            from datetime import timedelta
            from sqlalchemy import delete
            cutoff = datetime.utcnow() - timedelta(days=7)
            result = await self.session.execute(
                delete(NewsArticle).where(NewsArticle.published_at < cutoff)
            )
            pruned = result.rowcount
            await self.session.commit()
            if pruned:
                logger.info("Pruned %d articles older than 7 days", pruned)
        except Exception as e:
            logger.warning("Failed to prune old articles: %s", e)
            await self.session.rollback()

        total_new = 0
        total_skipped = 0
        feed_results = []

        for feed_config in FEEDS:
            try:
                new, skipped = await self._scrape_feed(feed_config)
                # Commit after each successful feed to avoid cascade rollbacks
                await self.session.commit()
                total_new += new
                total_skipped += skipped
                feed_results.append({
                    "name": feed_config["name"],
                    "status": "ok",
                    "new_articles": new,
                    "skipped": skipped,
                })
            except Exception as e:
                logger.error("Feed %s failed: %s", feed_config["name"], e)
                await self.session.rollback()
                feed_results.append({
                    "name": feed_config["name"],
                    "status": "error",
                    "error": str(e)[:200],
                })

        return {
            "total_new": total_new,
            "total_skipped": total_skipped,
            "feeds": feed_results,
        }

    async def _scrape_feed(self, feed_config: dict) -> tuple[int, int]:
        """Scrape a single RSS feed. Returns (new_count, skipped_count)."""
        name = feed_config["name"]
        url = feed_config["url"]
        default_cat = feed_config.get("default_cat", "policy")

        logger.info("Scraping feed: %s", name)

        # Fetch the feed (follow redirects)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "TheFOB-NewsBot/1.0 (veteran resource platform)"
            })
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)

        if not feed.entries:
            logger.warning("No entries in feed: %s", name)
            return 0, 0

        new_count = 0
        skipped = 0

        for entry in feed.entries[:25]:  # cap per feed
            article_url = getattr(entry, "link", None)
            if not article_url:
                continue

            # Check if we already have this URL
            existing = await self.session.execute(
                select(NewsArticle.id).where(NewsArticle.url == article_url)
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue

            title = _clean_html(getattr(entry, "title", ""))
            if not title:
                continue

            summary = _clean_html(
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
            )
            published = _parse_published(entry)

            # Only keep articles from the last 7 days
            if published:
                from datetime import timedelta
                cutoff = datetime.utcnow() - timedelta(days=7)
                if published < cutoff:
                    skipped += 1
                    continue

            category = categorize_article(title, summary, default=default_cat)
            impact = _estimate_impact(title, summary)
            image = _get_image(entry)

            article = NewsArticle(
                title=title,
                summary=summary or None,
                url=article_url,
                source_name=name,
                source_feed=url,
                category=category,
                impact=impact,
                image_url=image,
                published_at=published,
            )
            self.session.add(article)
            new_count += 1

        logger.info("Feed %s: %d new, %d skipped", name, new_count, skipped)
        return new_count, skipped
