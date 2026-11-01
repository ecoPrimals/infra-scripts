#!/usr/bin/env python3
"""
sitemap-graph.py — The sitemap is a graph OPENER, not a fossil.

Scans the live HUD directory, discovers all pages and feeds,
generates sitemap.xml dynamically. Run from cron or pre-push hook.

The sitemap is a living document. It opens the graph for crawlers.
It should NEVER be hand-maintained — that's a fossil.

scyBorg Triple License: AGPL-3.0 + ORC + CC-BY-SA 4.0
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

HUD_PUBLIC = Path("/home/eastgate/Development/ecoPrimals/infra/hud/site/public")
BASE_URL = "https://hud.primals.eco"
OUTPUT = HUD_PUBLIC / "sitemap.xml"

# Priority rules: higher = more important to crawl
PRIORITY_RULES = {
    "index.html": 1.0,
    "water.html": 0.9,
    "journey.html": 0.9,
    "digest.html": 0.9,
    "study.html": 0.9,
    "vision.html": 0.9,
    "welcome.html": 0.9,
    "easel.html": 0.8,
    "banana.html": 0.8,
    "play.html": 0.8,
    "classics.html": 0.8,
    "homunculus.html": 0.8,
    "gates.html": 0.8,
    "cns.html": 0.8,
    "chromatograph.html": 0.8,
}

# Pages to exclude from sitemap
EXCLUDE = {"404.html", "five-o-five.html"}

# Feed priority based on content type
FEED_PRIORITY = {
    "heartbeat.json": 0.5,
    "galactic-bounce.json": 0.7,
}


def get_mod_date(path):
    """Get file modification date as YYYY-MM-DD."""
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")


def classify_changefreq(path, name):
    """Estimate how often a page changes."""
    mtime = os.path.getmtime(path)
    age_days = (datetime.now(timezone.utc).timestamp() - mtime) / 86400

    if age_days < 1:
        return "daily"
    elif age_days < 7:
        return "weekly"
    else:
        return "monthly"


def scan_pages():
    """Find all HTML pages."""
    pages = []
    for f in sorted(HUD_PUBLIC.glob("*.html")):
        name = f.name
        if name in EXCLUDE:
            continue

        priority = PRIORITY_RULES.get(name, 0.6)
        freq = classify_changefreq(f, name)
        mod = get_mod_date(f)

        loc = f"{BASE_URL}/{name}" if name != "index.html" else f"{BASE_URL}/"
        pages.append((loc, mod, freq, priority))

    return pages


def scan_subdirs():
    """Find sub-surface index pages."""
    entries = []
    for subdir in ["neutron", "desk", "braid", "chipmunk", "core", "graph", "live"]:
        idx = HUD_PUBLIC / subdir / "index.html"
        if idx.exists():
            mod = get_mod_date(idx)
            entries.append((f"{BASE_URL}/{subdir}/", mod, "daily", 0.7))

        # Also scan for sub-pages
        subdir_path = HUD_PUBLIC / subdir
        if subdir_path.is_dir():
            for f in sorted(subdir_path.glob("*.html")):
                if f.name == "index.html":
                    continue
                mod = get_mod_date(f)
                entries.append((f"{BASE_URL}/{subdir}/{f.name}", mod, "weekly", 0.6))

    return entries


def scan_feeds():
    """Find important JSON feeds — these are structured data for machines."""
    feeds = []
    data_dir = HUD_PUBLIC / "data"
    if not data_dir.exists():
        return feeds

    for f in sorted(data_dir.glob("*.json")):
        name = f.name
        mod = get_mod_date(f)
        size = f.stat().st_size

        # Klein disc: ALL feeds exist on both surfaces.
        # Prior (old/small) is not bad. Later (new/big) is not good.
        # Both is best. Only skip truly broken files.
        if size < 10:
            continue

        try:
            with open(f) as fh:
                json.load(fh)  # just validate it's parseable JSON
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        priority = FEED_PRIORITY.get(name, 0.6)
        freq = classify_changefreq(f, name)
        feeds.append((f"{BASE_URL}/data/{name}", mod, freq, priority))

    return feeds


def scan_special():
    """RSS, beacon, and other discovery endpoints."""
    entries = []
    for name, priority in [("feed.xml", 0.8), ("llms.txt", 0.5)]:
        path = HUD_PUBLIC / name
        if path.exists():
            mod = get_mod_date(path)
            entries.append((f"{BASE_URL}/{name}", mod, "daily", priority))
    return entries


def generate_sitemap():
    """Generate the sitemap XML."""
    pages = scan_pages()
    subdirs = scan_subdirs()
    feeds = scan_feeds()
    special = scan_special()

    all_urls = pages + subdirs + feeds + special

    # Sort by priority descending
    all_urls.sort(key=lambda x: -x[3])

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for loc, mod, freq, priority in all_urls:
        lines.append(f'  <url>')
        lines.append(f'    <loc>{loc}</loc>')
        lines.append(f'    <lastmod>{mod}</lastmod>')
        lines.append(f'    <changefreq>{freq}</changefreq>')
        lines.append(f'    <priority>{priority:.1f}</priority>')
        lines.append(f'  </url>')

    lines.append('</urlset>')

    xml = "\n".join(lines) + "\n"

    with open(OUTPUT, "w") as f:
        f.write(xml)

    print(f"sitemap.xml: {len(all_urls)} URLs")
    print(f"  {len(pages)} pages + {len(subdirs)} sub-surfaces + "
          f"{len(feeds)} feeds + {len(special)} special")
    return len(all_urls)


if __name__ == "__main__":
    generate_sitemap()
