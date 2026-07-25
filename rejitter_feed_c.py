#!/usr/bin/env python3
"""Feed Lab — the HOST-SIDE daily re-jitter for feed-c.json (stdlib only).

Runs in the public feeds repo's scheduled GitHub Action, where no Django
and no catalog exist: it rewrites price/stock per (seed, gtin) with the
SAME deterministic scheme `export_feed_lab` uses, keeping the row set
identical. The seed defaults to today's date (UTC), so each day's run is
a REAL content change and re-running the same day is byte-identical —
which is exactly what exercises changed-run applies against content-hash
short-circuits on the BuyDecide side.

    python rejitter_feed_c.py [feeds/feed-c.json] [--seed 20260726]
"""
import argparse
import datetime as dt
import hashlib
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

STOCKS = ("in stock", "in stock", "in stock", "out of stock", "preorder")


def jittered_price(base, gtin, seed):
    digest = hashlib.sha256(f"{seed}:{gtin}".encode()).digest()
    factor = Decimal(85 + digest[0] % 31) / Decimal(100)
    value = (Decimal(base) * factor).quantize(Decimal("0.01"),
                                              rounding=ROUND_HALF_UP)
    return value if value > 0 else Decimal("1.00")


def stock_for(gtin, seed):
    digest = hashlib.sha256(f"stock:{seed}:{gtin}".encode()).digest()
    return STOCKS[digest[0] % len(STOCKS)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="feeds/feed-c.json")
    ap.add_argument("--seed", type=int,
                    default=int(dt.datetime.now(dt.timezone.utc)
                                .strftime("%Y%m%d")))
    args = ap.parse_args()
    path = Path(args.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("offers", [])
    if not rows:
        sys.exit("feed-c.json carries no offers — refusing to write an "
                 "empty feed (an empty batch reads as a total withdrawal).")
    # ★ The jitter derives from the ORIGINAL exported price the first time
    # and every time: rows carry `base_price` (planted on first run) so
    # daily jitter never compounds toward zero or infinity.
    for r in rows:
        base = r.get("base_price") or r["price"]
        r["base_price"] = str(base)
        r["price"] = str(jittered_price(base, r["gtin"], args.seed))
        r["stock"] = stock_for(r["gtin"], args.seed)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1,
                               sort_keys=True) + "\n", encoding="utf-8")
    print(f"re-jittered {len(rows)} rows with seed {args.seed}")


if __name__ == "__main__":
    main()
