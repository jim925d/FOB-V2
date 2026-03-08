#!/usr/bin/env python3
"""
Compare our local-search API results to a direct Google (CSE) pull for the same query.

Usage:
  # API server must be running (e.g. uvicorn app.main:app)
  python -m scripts.compare_local_search_to_google
  python -m scripts.compare_local_search_to_google --zip 90210
  python -m scripts.compare_local_search_to_google --api-base http://localhost:8000

Requires:
  - Our API running (for "our" results).
  - Optional: GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX in .env for direct Google CSE pull.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

# Optional: add project root only if we need app (e.g. for get_settings)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.dirname(_script_dir)


def build_query(zip_code: str, radius_miles: int = None, state: str = None) -> str:
    """Same logic as employment_networking._build_search_query."""
    base = "veteran networking events"
    if state:
        # Minimal state name lookup (same as app)
        state_names = {"CO": "Colorado", "CA": "California", "TX": "Texas", "NY": "New York", "FL": "Florida"}
        state_name = state_names.get(state.upper(), state) if len(state) == 2 else state
        return f"{base} {state_name}"
    if zip_code and radius_miles and radius_miles in (10, 25, 50):
        return f"{base} within {radius_miles} miles of {zip_code}"
    if zip_code:
        return f"{base} by zip {zip_code}"
    return base


def google_search_url(query: str) -> str:
    from urllib.parse import quote_plus
    return f"https://www.google.com/search?q={quote_plus(query)}"


def main():
    parser = argparse.ArgumentParser(description="Compare local-search API to Google CSE for same query")
    parser.add_argument("--zip", default="80030", help="ZIP code for search (default 80030)")
    parser.add_argument("--api-base", default="http://localhost:8000", help="Our API base URL")
    parser.add_argument("--radius", type=int, default=None, help="Optional: 10, 25, or 50 miles")
    parser.add_argument("--state", default=None, help="Optional: 2-letter state (overrides zip for query)")
    args = parser.parse_args()

    query = build_query(args.zip, args.radius, args.state)
    print("=" * 70)
    print("QUERY (same as Google)")
    print("=" * 70)
    print(query)
    print()
    print("Open in browser to see Google's results:")
    print(google_search_url(query))
    print()

    # 1) Our API
    print("=" * 70)
    print("OUR API (local-search)")
    print("=" * 70)
    params = {"zip_code": args.zip}
    if args.radius:
        params["radius_miles"] = args.radius
    if args.state:
        params["state"] = args.state
    qs = urllib.parse.urlencode(params)
    api_url = f"{args.api_base.rstrip('/')}/api/v1/employment-networking/local-search?{qs}"
    try:
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        results = data.get("results") or []
        print(f"Count: {len(results)}")
        for i, row in enumerate(results[:15], 1):
            name = (row.get("name") or "")[:60]
            date = row.get("date") or "—"
            link = (row.get("link") or "")[:50]
            print(f"  {i}. {name}...")
            print(f"     Date: {date}  |  {link}...")
        if len(results) > 15:
            print(f"  ... and {len(results) - 15} more")
    except urllib.error.URLError as e:
        print("Could not reach API. Is it running? Start with: uvicorn app.main:app --reload")
        print(e)
    except Exception as e:
        print("Error:", e)
    print()

    # 2) Direct Google CSE (if keys set in env or .env)
    print("=" * 70)
    print("GOOGLE CSE (direct pull, same query)")
    print("=" * 70)
    # Load .env if present (optional)
    env_path = os.path.join(_api_root, ".env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    api_key = os.environ.get("GOOGLE_CSE_API_KEY", "").strip()
    cx = os.environ.get("GOOGLE_CSE_CX", "").strip()
    if not api_key or not cx:
        print("Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX in .env to compare with direct CSE.")
        return
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 10,
    }
    try:
        req_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(req_url)
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
        items = data.get("items") or []
        print(f"Count: {len(items)}")
        for i, it in enumerate(items[:15], 1):
            title = (it.get("title") or "")[:60]
            link = (it.get("link") or "")[:50]
            snippet = (it.get("snippet") or "")[:80]
            print(f"  {i}. {title}...")
            print(f"     {snippet}...")
            print(f"     {link}...")
        if len(items) > 15:
            print(f"  ... and {len(items) - 15} more")
    except Exception as e:
        print("Error:", e)
    print()
    print("Compare the two lists above and the browser Google link to see if they match.")

if __name__ == "__main__":
    main()
