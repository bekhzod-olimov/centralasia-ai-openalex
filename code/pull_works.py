"""Download the complete work-level corpus from OpenAlex.

Corpus definition is identical to pull_data.py (September 2026 aggregate pull):
  authorships.institutions.country_code:uz|kz|kg|tj|tm
  primary_topic.subfield.id in {1702, 1703, 1707, 1712}
  publication_year 2010-2026

Two variants are pulled so that precision and recall of the corpus definition can be
examined (Reviewer 1, Observations 1-2):
  works_primary.jsonl   primary-topic subfield in the four CS subfields (main corpus)
  works_anytopic.jsonl  ANY assigned topic's subfield in the four CS subfields (recall check)

Paging: OpenAlex basic page paging (page=1..N, per-page=200) is limited to 10,000 results
per query and needs no API key; cursor paging needs a key. Each query is therefore split
by publication year (every year has < 10,000 matches) and results are de-duplicated by id.

Cost: list calls are USD 0.0001 each; the whole pull is ~180 calls (< USD 0.02).

Usage: python3 pull_works.py [outdir]
"""
import json, sys, time, datetime, urllib.request, urllib.parse, urllib.error
from pathlib import Path

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "data_snapshot_2026-11-12")
OUT.mkdir(exist_ok=True)
API = "https://api.openalex.org/works"
HDR = {"User-Agent": "KU-bibliometrics (mailto:YOUR_EMAIL_HERE)"}
SUB = "primary_topic.subfield.id:subfields/1702|subfields/1707|subfields/1703|subfields/1712"
SUB_ANY = "topics.subfield.id:subfields/1702|subfields/1707|subfields/1703|subfields/1712"
CC = "authorships.institutions.country_code:uz|kz|kg|tj|tm"
SELECT = ",".join([
    "id", "doi", "title", "publication_year", "publication_date", "type", "language",
    "primary_location", "open_access", "authorships", "institutions_distinct_count",
    "countries_distinct_count", "cited_by_count", "fwci", "citation_normalized_percentile",
    "primary_topic", "topics", "indexed_in", "is_retracted", "is_paratext", "referenced_works_count",
    "created_date", "updated_date",
])


def get(url):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read()[:300]
            print("  HTTP", e.code, body, flush=True)
            if e.code in (401, 403):
                raise SystemExit("budget/key problem: " + body.decode(errors="replace"))
        except Exception as e:  # noqa
            print("  retry", attempt, e, flush=True)
        time.sleep(5 * (attempt + 1))
    raise SystemExit(f"failed: {url}")


def pull(base_filter, name):
    path = OUT / name
    seen, n_expected = set(), 0
    with path.open("w", encoding="utf-8") as f:
        for year in range(2010, 2027):
            filt = f"{base_filter},publication_year:{year}"
            page, got, count = 1, 0, None
            while True:
                q = urllib.parse.urlencode({"filter": filt, "per-page": 200, "page": page,
                                            "sort": "publication_date:desc", "select": SELECT})
                d = get(f"{API}?{q}")
                count = d["meta"]["count"]
                for w in d["results"]:
                    if w["id"] not in seen:
                        seen.add(w["id"])
                        f.write(json.dumps(w, ensure_ascii=False) + "\n")
                got += len(d["results"])
                if got >= count or not d["results"]:
                    break
                page += 1
                time.sleep(0.2)
            n_expected += count
            print(f"{name} {year}: {got}/{count} (unique so far {len(seen)})", flush=True)
    print(f"{name}: unique {len(seen)} of expected {n_expected}", flush=True)
    return len(seen), n_expected


meta = {"snapshot_date": datetime.date.today().isoformat(), "select": SELECT, "paging": "page-based, per year"}
meta["primary_filter"] = f"{CC},{SUB},publication_year:2010-2026"
meta["primary_unique"], meta["primary_expected"] = pull(f"{CC},{SUB}", "works_primary.jsonl")
meta["anytopic_filter"] = f"{CC},{SUB_ANY},publication_year:2010-2026"
meta["anytopic_unique"], meta["anytopic_expected"] = pull(f"{CC},{SUB_ANY}", "works_anytopic.jsonl")
(OUT / "meta_works.json").write_text(json.dumps(meta, indent=1))
print("DONE", meta, flush=True)
