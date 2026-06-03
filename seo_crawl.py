#!/usr/bin/env python3
"""Lightweight SEO recon for a single public page.

Fetches the target URL, reports the heading outline (H1/H2/H3),
key SEO meta, and infers the article URL pattern from on-page links.
"""
import re
import sys
from collections import Counter
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.hardrock.bet/news/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def fetch(url):
    s = requests.Session()
    r = s.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    return r


def main():
    print(f"=== Fetching {URL} ===")
    r = fetch(URL)
    print(f"HTTP {r.status_code}  |  final URL: {r.url}")
    print(f"Server: {r.headers.get('server')}  |  Content-Type: {r.headers.get('content-type')}")
    print(f"HTML length: {len(r.text)} bytes\n")
    if r.status_code != 200:
        print("Non-200 response — body preview:")
        print(r.text[:1500])
        return

    soup = BeautifulSoup(r.text, "lxml")

    # --- SEO meta ---
    print("=== SEO META ===")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    print(f"<title>: {title}")
    for name in ("description", "robots", "keywords"):
        tag = soup.find("meta", attrs={"name": name})
        if tag:
            print(f"meta[{name}]: {tag.get('content')}")
    canon = soup.find("link", rel="canonical")
    if canon:
        print(f"canonical: {canon.get('href')}")
    for prop in ("og:title", "og:type", "og:url", "og:description"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag:
            print(f"{prop}: {tag.get('content')}")
    # JSON-LD structured data
    ld = soup.find_all("script", attrs={"type": "application/ld+json"})
    print(f"JSON-LD blocks: {len(ld)}")
    print()

    # --- Heading outline ---
    print("=== HEADING OUTLINE (H1/H2/H3) ===")
    headings = soup.find_all(["h1", "h2", "h3"])
    if not headings:
        print("(no h1-h3 found — page is likely client-side rendered / JS SPA)")
    for h in headings:
        txt = " ".join(h.get_text(" ", strip=True).split())
        if txt:
            indent = {"h1": "", "h2": "  ", "h3": "    "}[h.name]
            print(f"{indent}{h.name.upper()}: {txt[:120]}")
    counts = Counter(h.name for h in headings)
    print(f"\nCounts: {dict(counts)}")
    print()

    # --- Link / URL pattern analysis ---
    print("=== URL PATTERN ANALYSIS ===")
    base = urlparse(URL)
    paths = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        p = urlparse(href)
        # same-host (or relative) links only
        if p.netloc and p.netloc != base.netloc:
            continue
        path = p.path
        if path and path != "/":
            paths.append(path)

    news_paths = [p for p in paths if "/news" in p or "/article" in p or "/blog" in p]
    print(f"Total internal links: {len(paths)}  |  news-related: {len(news_paths)}")

    # Build a structural template by replacing slugs/years/ids with placeholders
    def templ(path):
        segs = [s for s in path.split("/") if s]
        out = []
        for s in segs:
            if re.fullmatch(r"\d{4}", s):
                out.append("{year}")
            elif re.fullmatch(r"\d{1,2}", s):
                out.append("{num}")
            elif re.fullmatch(r"[0-9a-f]{8,}", s):
                out.append("{id}")
            elif "-" in s or len(s) > 20:
                out.append("{slug}")
            else:
                out.append(s)
        return "/" + "/".join(out)

    pattern_counts = Counter(templ(p) for p in (news_paths or paths))
    print("\nTop path templates:")
    for pat, n in pattern_counts.most_common(15):
        print(f"  {n:>3}  {pat}")

    print("\nSample news-related URLs:")
    for p in news_paths[:15]:
        print(f"  {p}")


if __name__ == "__main__":
    main()
