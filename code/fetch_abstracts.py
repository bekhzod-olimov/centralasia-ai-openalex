#!/usr/bin/env python3
"""Add abstracts to out/precision_sample.csv via free single-entity OpenAlex calls."""
import csv, json, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
P = HERE / "out" / "precision_sample.csv"
HDR = {"User-Agent": "KU-bibliometrics (mailto:YOUR_EMAIL_HERE)"}


def invert(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


rows = list(csv.DictReader(open(P, encoding="utf-8")))
for k, r in enumerate(rows, 1):
    if r.get("abstract"):
        continue
    url = f"https://api.openalex.org/{r['openalex_id']}?select=id,abstract_inverted_index"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60) as resp:
                d = json.load(resp)
            r["abstract"] = invert(d.get("abstract_inverted_index")) or "(no abstract in OpenAlex)"
            break
        except Exception as e:  # noqa
            print("retry", attempt, r["openalex_id"], e, flush=True)
            time.sleep(3 * (attempt + 1))
    if k % 25 == 0:
        print(k, flush=True)
    time.sleep(0.25)
with open(P, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print("done", sum(1 for r in rows if r["abstract"] and not r["abstract"].startswith("(no")), "with abstracts of", len(rows))
