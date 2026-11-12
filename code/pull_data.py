"""Re-pull every OpenAlex aggregation used in the paper into data/ (fresh snapshot).

All queries share the corpus definition:
  authorships.institutions.country_code:uz|kz|kg|tj|tm
  primary_topic.subfield.id in {1702, 1703, 1707, 1712}
  publication_year 2010-2026
"""
import csv, json, time, datetime, urllib.request, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
API = "https://api.openalex.org"
HDR = {"User-Agent": "mailto:YOUR_EMAIL_HERE"}
SUB = "primary_topic.subfield.id:subfields/1702|subfields/1707|subfields/1703|subfields/1712"
CC = ["uz", "kz", "kg", "tj", "tm"]
CORE = f"authorships.institutions.country_code:uz|kz|kg|tj|tm,{SUB},publication_year:2010-2026"


def get(path, **params):
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=90))
        except Exception as e:  # noqa
            print("  retry", attempt, e)
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"failed: {url}")


def works(filt, group=None, **kw):
    p = {"filter": filt, "per-page": 200}
    if group:
        p["group_by"] = group
    p.update(kw)
    return get("works", **p)


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    print("wrote", name)


snapshot = datetime.date.today().isoformat()
meta = {"snapshot_date": snapshot, "corpus_filter": CORE}

# 1. yearly counts
combined = works(CORE, "publication_year"); save("year_combined.json", combined)
meta["corpus_count"] = combined["meta"]["count"]
years = {}
for cc in CC:
    r = works(f"authorships.institutions.country_code:{cc},{SUB},publication_year:2010-2026", "publication_year")
    save(f"year_{cc}.json", {"country": cc, "years": r["group_by"], "total": r["meta"]["count"]})
    years[cc] = {int(g["key"]): g["count"] for g in r["group_by"]}
with (DATA / "yearly_trend.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["year"] + CC)
    for y in range(2010, 2027):
        w.writerow([y] + [years[cc].get(y, 0) for cc in CC])

# 2. institutions (all contributing, and domestic-only per country)
save("top_institutions.json", works(CORE, "authorships.institutions.id"))


def inst_countries(ids):
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        r = get("institutions", filter="ids.openalex:" + "|".join(chunk), per_page=50,
                select="id,display_name,country_code")
        for x in r["results"]:
            out[x["id"]] = x
    return out


for cc in CC:
    r = works(f"authorships.institutions.country_code:{cc},{SUB},publication_year:2010-2026",
              "authorships.institutions.id")
    groups = [g for g in r["group_by"] if g["key"] and g["key"] != "unknown"]
    info = inst_countries([g["key"] for g in groups])
    with (DATA / f"inst_{cc}_all.tsv").open("w") as f:
        for g in groups:
            f.write(f"{g['count']}\t{g['key_display_name']}\t{info.get(g['key'], {}).get('country_code')}\n")
    with (DATA / f"inst_{cc}.tsv").open("w") as f:
        for g in groups:
            if (info.get(g["key"], {}).get("country_code") or "").lower() == cc:
                f.write(f"{g['count']}\t{g['key_display_name']}\n")
    print("inst", cc, len(groups))

# 3. topics, sources, OA, doc types, co-author countries
save("top_topics.json", works(CORE, "primary_topic.id"))
save("top_sources.json", works(CORE, "primary_location.source.id"))
save("oa_status.json", works(CORE, "open_access.oa_status"))
save("doc_types.json", works(CORE, "type"))
save("coauthor_countries.json", works(CORE, "authorships.countries"))
for cc in CC:
    save(f"coauthor_{cc}.json", works(f"authorships.institutions.country_code:{cc},{SUB},publication_year:2010-2026",
                                      "authorships.countries"))

# 4. top-200 most cited with FWCI
tc = works(CORE, sort="cited_by_count:desc",
           select="id,doi,title,display_name,publication_year,type,cited_by_count,fwci,authorships,primary_location,open_access,primary_topic")
save("top_cited.json", tc)

# 5. auxiliary checks used in the text
save("zenodo_by_year.json", works(CORE + ",primary_location.source.id:S4306400562", "publication_year"))
save("tm_all_subjects.json", {"count": works("authorships.institutions.country_code:tm,publication_year:2010-2026")["meta"]["count"]})
save("msu_dushanbe_record.json", get("institutions/I4210150146"))
save("msu_dushanbe_ai_by_year.json", works(f"authorships.institutions.id:I4210150146,{SUB},publication_year:2010-2026", "publication_year"))
save("meta.json", meta)
print("DONE", meta)
