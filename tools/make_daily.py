#!/usr/bin/env python3
"""Make today's Robot Lab Breakout daily challenge and add it to daily.json. Runs unattended (GitHub Actions).

Usage:  python3 tools/make_daily.py [daily.json] [--date YYYY-MM-DD] [--backfill N]
Every lock comes from the level generators and is re-solved from its data by daily_tool.solve before it is kept.
The same date always gives the same challenge, so re-running is safe. Dates use Africa/Johannesburg time.
"""
import json, os, re, sys, random, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_tool as T
import gen as G
from worlds_content import WORLDS
from daily_themes import THEMES, WORDS

KEEP = 14


def today_sa():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Africa/Johannesburg")).date()
    except Exception:
        return (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).date()


def cycle(items, salt, idx):
    order = list(range(len(items))); random.Random(salt).shuffle(order)
    return [items[order[(idx + k) % len(items)]] for k in range(len(items))]


def make(day):
    idx = day.toordinal(); sat = day.weekday() == 5; n = 5 if sat else 4
    wi_th, name, story = cycle(THEMES, "robotlab-themes", idx)[0]
    words = [w for w in WORDS if len(w[0]) == n and w[0] not in G.FINALS]
    for word, clue in cycle(words, f"robotlab-words-{n}", idx):
        if re.search(r"\b" + word + r"\b", (name + " " + story).upper()): continue
        W = dict(WORLDS[wi_th]); W["levels"] = [(word, ("Weekend Boss: " if sat else "") + name, story, clue)]
        r = random.Random(f"robotlab-daily-{day.isoformat()}")
        for attempt in range(30):
            try:
                spec, types = G.make_level(r, 6 if sat else r.choice([2, 3, 4]), 0, W, [], {t: 0 for t in G.ALLT})
            except (RuntimeError, AssertionError):
                continue
            if sum(t in G.NEW for t in types) < 2: continue
            # independent re-check of every lock and the final word
            for lk in spec["locks"]:
                got = T.solve(lk)
                assert (T.norm(lk["answer"]) in got.split()) if lk["type"] == "cipher" else T.norm(got) == T.norm(lk["answer"])
                assert lk["type"] in T.ALLOWED
            assert sorted(lk["r"] for lk in spec["locks"]) == sorted(word)
            spec["limit"] = 30 if sat else 20
            e = G.page_entry(spec); e.pop("key", None)
            e.update({"date": day.isoformat(), "tag": "Daily challenge"})
            return e, spec
    raise SystemExit(f"could not make a challenge for {day}")


def main():
    args = sys.argv[1:]; out = "daily.json"; days = [today_sa()]
    if args and not args[0].startswith("--"): out = args.pop(0)
    if "--date" in args: days = [datetime.date.fromisoformat(args[args.index("--date") + 1])]
    if "--backfill" in args:
        k = int(args[args.index("--backfill") + 1]); days = [days[0] - datetime.timedelta(d) for d in range(k - 1, -1, -1)]
    try: cur = json.load(open(out))
    except (FileNotFoundError, ValueError): cur = []
    for day in days:
        e, spec = make(day)
        cur = [x for x in cur if x.get("date") != e["date"]] + [e]
        print(f"OK {e['date']}: {e['name']} ({len(e['locks'])} locks: {', '.join(lk['type'] for lk in e['locks'])})")
    cur = sorted(cur, key=lambda x: x["date"], reverse=True)[:KEEP]
    json.dump(cur, open(out, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
