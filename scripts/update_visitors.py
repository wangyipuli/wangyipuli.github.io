#!/usr/bin/env python3
"""Pull per-country visitor counts from GoatCounter into data/visitors.json.

Run by .github/workflows/update-visitors.yml with GOATCOUNTER_TOKEN set from
a repository secret. The token never reaches the site: the page only reads
the JSON this writes.
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("GOATCOUNTER_SITE", "wangyipuli")
BASE = os.environ.get("GOATCOUNTER_BASE", f"https://{SITE}.goatcounter.com/api/v0")
TOKEN = os.environ["GOATCOUNTER_TOKEN"]
START = "2020-01-01T00:00:00Z"          # before the site existed: "all time"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "visitors.json")


def get(path, **params):
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        # urllib's own message omits the URL and the server's explanation.
        body = e.read().decode("utf8", "replace")[:500]
        sys.exit(f"GoatCounter returned HTTP {e.code} for {url}\n{body}")


def fetch_countries():
    countries, offset = {}, 0
    while True:
        page = get("/stats/locations", start=START, limit=100, offset=offset)
        stats = page.get("stats") or []
        for s in stats:
            code = (s.get("id") or "").upper()
            if re.fullmatch(r"[A-Z]{2}", code):
                countries[code] = countries.get(code, 0) + int(s.get("count", 0))
            else:
                print(f"skipping location without an ISO-2 id: {s!r}", file=sys.stderr)
        if not page.get("more") or not stats:
            return countries
        offset += len(stats)
        time.sleep(0.3)                  # the API allows about 4 requests/second


def main():
    countries = fetch_countries()
    total = int(get("/stats/total", start=START).get("total", 0))

    ordered = dict(sorted(countries.items(), key=lambda kv: (-kv[1], kv[0])))
    new = {"period": "all time", "total": total, "countries": ordered}

    try:
        with open(OUT, encoding="utf8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        old = {}

    # Leave the file alone when nothing changed, so the workflow makes no commit.
    if all(old.get(k) == new[k] for k in new):
        print(f"no change: {total} visitors in {len(ordered)} countries")
        return

    new["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    with open(OUT, "w", encoding="utf8") as f:
        json.dump(new, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {total} visitors across {len(ordered)} countries: {ordered}")


if __name__ == "__main__":
    main()
