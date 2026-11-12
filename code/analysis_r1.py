#!/usr/bin/env python3
"""Work-level analysis of the Central Asia AI-related corpus (OpenAlex snapshot 2026-11-12).

Reads  ../data_snapshot_2026-11-12/works_primary.jsonl  (main corpus)
       ../data_snapshot_2026-11-12/works_anytopic.jsonl (recall variant)
       ../data/                                          (September 2026 aggregate snapshot)
       ../data_snapshot_2026-05-30/                      (May 2026 aggregate snapshot)
Writes out/results.json and out/*.csv

Every number quoted in the revised manuscript is produced here.
"""
from __future__ import annotations
import csv, json, math, random, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent
SNAP = ROOT / "data_snapshot_2026-11-12"
SEPT = ROOT / "data"
MAY = ROOT / "data_snapshot_2026-05-30"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

CA = ["UZ", "KZ", "KG", "TJ", "TM"]
NAMES = {"UZ": "Uzbekistan", "KZ": "Kazakhstan", "KG": "Kyrgyzstan", "TJ": "Tajikistan", "TM": "Turkmenistan"}
POP2024 = {"KZ": 20.6, "UZ": 36.4, "KG": 7.2, "TJ": 10.6, "TM": 7.5}  # World Bank WDI, millions
SUBF = {"1702": "Artificial Intelligence", "1707": "Computer Vision and Pattern Recognition",
        "1703": "Computational Theory and Mathematics", "1712": "Software"}
NARROW = {"1702", "1707"}
LAST_FULL_YEAR = 2025

# OECD members (38) as of 2026
OECD = set("AU AT BE CA CL CO CR CZ DK EE FI FR DE GR HU IS IE IL IT JP KR LV LT LU MX NL NZ NO PL PT SK SI ES SE CH TR GB US".split())
POST_SOVIET_NON_OECD = set("RU UA BY MD GE AM AZ".split())
# UN M49 Asia (incl. Middle East) minus OECD members and minus the five target countries
ASIA_NON_OECD = set(("AF BH BD BT BN KH CN CY HK IN ID IR IQ JO KW LA LB MO MY MV MN MM NP KP OM PK PS PH QA SA SG LK SY TW TH "
                     "TL AE VN YE").split())


def sid(x):
    return x.rsplit("/", 1)[-1] if x else x


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ----------------------------------------------------------------------------- work parsing
def parse(w):
    ca, dom_inst, foreign, inst_all = set(), defaultdict(set), set(), set()
    for a in w.get("authorships", []):
        for i in a.get("institutions", []):
            cc = (i.get("country_code") or "").upper()
            iid = sid(i.get("id"))
            if cc in CA:
                ca.add(cc)
                dom_inst[cc].add((iid, i.get("display_name"), tuple(sid(x) for x in i.get("lineage", []) or [])))
            inst_all.add(iid)
        for c in a.get("countries", []) or []:
            c = c.upper()
            if c not in CA:
                foreign.add(c)
    src = (w.get("primary_location") or {}).get("source") or {}
    pt = w.get("primary_topic") or {}
    return {
        "id": sid(w["id"]), "doi": w.get("doi"), "title": w.get("title"), "year": w.get("publication_year"),
        "date": w.get("publication_date"), "type": w.get("type"), "lang": w.get("language"),
        "src_id": sid(src.get("id")), "src_name": src.get("display_name"), "src_type": src.get("type"),
        "oa": (w.get("open_access") or {}).get("oa_status"),
        "cites": w.get("cited_by_count", 0), "fwci": w.get("fwci"),
        "top10": ((w.get("citation_normalized_percentile") or {}).get("is_in_top_10_percent")),
        "topic_id": sid(pt.get("id")), "topic": pt.get("display_name"),
        "subfield": sid((pt.get("subfield") or {}).get("id")), "field": (pt.get("field") or {}).get("display_name"),
        "topics": [(sid(t.get("id")), sid((t.get("subfield") or {}).get("id"))) for t in w.get("topics", []) or []],
        "ca": ca, "dom_inst": dom_inst, "foreign": foreign, "n_inst": len(inst_all),
        "retracted": w.get("is_retracted"), "paratext": w.get("is_paratext"),
    }


def tier(r):
    """Mutually exclusive publication-channel classification."""
    if r["type"] == "preprint" or r["src_type"] == "repository":
        return "repository/preprint"
    if r["type"] in ("article", "review", "conference-paper", "book-chapter", "book", "conference-abstract",
                     "data-paper", "software-paper", "editorial", "letter", "erratum", "retraction", "reference-entry"):
        return "formal publication"
    return "other"


# ----------------------------------------------------------------------------- growth models
def growth_fits(series: dict[int, int], y0=2010, y1=LAST_FULL_YEAR):
    """series: year -> count. Returns dict of fits (log-OLS, Poisson, NB2) with 95% CIs."""
    import statsmodels.api as sm
    years = np.array([y for y in range(y0, y1 + 1)])
    n = np.array([series.get(y, 0) for y in years], dtype=float)
    t = years - y0
    out = {"n_years": int(len(years)), "n_nonzero": int((n > 0).sum()), "first": int(n[0]), "last": int(n[-1])}
    # log-linear OLS on non-zero years, HC1 robust SE
    m = n > 0
    X = sm.add_constant(t[m].astype(float))
    ols = sm.OLS(np.log(n[m]), X).fit(cov_type="HC1")
    r, se = ols.params[1], ols.bse[1]
    out["ols"] = {"r": r, "ci": [r - 1.96 * se, r + 1.96 * se], "r2": ols.rsquared,
                  "dw": float(sm.stats.durbin_watson(ols.resid)), "doubling": math.log(2) / r}
    # Poisson GLM on all years (zeros allowed)
    Xa = sm.add_constant(t.astype(float))
    poi = sm.GLM(n, Xa, family=sm.families.Poisson()).fit()
    r, se = poi.params[1], poi.bse[1]
    out["poisson"] = {"r": r, "ci": [r - 1.96 * se, r + 1.96 * se], "doubling": math.log(2) / r,
                      "deviance_df": poi.deviance / poi.df_resid}
    # Negative binomial (NB2) with alpha estimated by ML
    try:
        from statsmodels.discrete.discrete_model import NegativeBinomial
        nb = NegativeBinomial(n, Xa).fit(disp=0, maxiter=500)
        r, se = nb.params[1], nb.bse[1]
        out["nb2"] = {"r": r, "ci": [r - 1.96 * se, r + 1.96 * se], "doubling": math.log(2) / r,
                      "alpha": float(nb.params[-1])}
    except Exception as e:  # noqa
        out["nb2"] = {"error": str(e)}
    return out


# ----------------------------------------------------------------------------- concentration
def concentration(counts: list[int]):
    c = np.array(sorted(counts, reverse=True), dtype=float)
    tot = c.sum()
    s = c / tot
    hhi = float((s ** 2).sum())
    cs = np.sort(c)
    nn = len(cs)
    gini = float((2 * np.arange(1, nn + 1) - nn - 1).dot(cs) / (nn * cs.sum())) if nn > 1 else 0.0
    return {"n_inst": nn, "appearances": int(tot), "hhi": hhi, "effective": 1 / hhi, "gini": gini,
            "top1_share": float(s[0]), "top2_share": float(s[:2].sum()), "top5_share": float(s[:5].sum())}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, c - h, c + h)


def boot_mean(x, B=2000, seed=1):
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    if len(x) == 0:
        return (float("nan"), float("nan"), float("nan"))
    bs = [rng.choice(x, len(x), replace=True).mean() for _ in range(B)]
    return (float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))


# ----------------------------------------------------------------------------- main
def main():
    raw = load_jsonl(SNAP / "works_primary.jsonl")
    W = [parse(w) for w in raw]
    ids = {r["id"] for r in W}
    assert len(ids) == len(W), "duplicate ids"
    R = {"snapshot": "2026-11-12", "N": len(W)}
    print("corpus", len(W))

    # ---- basic distributions
    R["by_year"] = dict(sorted(Counter(r["year"] for r in W).items()))
    R["by_subfield"] = {SUBF[k]: v for k, v in Counter(r["subfield"] for r in W).most_common()}
    R["by_type"] = dict(Counter(r["type"] for r in W).most_common())
    R["by_tier"] = dict(Counter(tier(r) for r in W).most_common())
    R["by_src_type"] = dict(Counter(r["src_type"] or "none" for r in W).most_common())
    R["by_lang"] = dict(Counter(r["lang"] or "unknown" for r in W).most_common(8))
    R["retracted"] = sum(1 for r in W if r["retracted"])
    R["no_ca_country"] = sum(1 for r in W if not r["ca"])
    R["multi_ca"] = dict(Counter(len(r["ca"]) for r in W))

    # ---- country counts: full and fractional, by year, by tier, narrow/broad
    def country_table(rows, weight="full"):
        tab = {cc: defaultdict(float) for cc in CA}
        for r in rows:
            k = len(r["ca"]) or 1
            for cc in r["ca"]:
                tab[cc][r["year"]] += 1.0 if weight == "full" else 1.0 / k
        return {cc: dict(sorted(v.items())) for cc, v in tab.items()}

    R["country_year_full"] = country_table(W)
    R["country_year_frac"] = country_table(W, "frac")
    R["country_total_full"] = {cc: int(sum(v.values())) for cc, v in R["country_year_full"].items()}
    R["country_total_frac"] = {cc: round(sum(v.values()), 1) for cc, v in R["country_year_frac"].items()}
    formal = [r for r in W if tier(r) == "formal publication"]
    R["country_year_formal"] = country_table(formal)
    R["country_total_formal"] = {cc: int(sum(v.values())) for cc, v in R["country_year_formal"].items()}
    narrow = [r for r in W if r["subfield"] in NARROW]
    R["N_narrow"] = len(narrow)
    R["country_year_narrow"] = country_table(narrow)
    R["country_total_narrow"] = {cc: int(sum(v.values())) for cc, v in R["country_year_narrow"].items()}
    R["by_year_formal"] = dict(sorted(Counter(r["year"] for r in formal).items()))
    R["by_year_narrow"] = dict(sorted(Counter(r["year"] for r in narrow).items()))
    R["by_year_tier"] = {t: dict(sorted(Counter(r["year"] for r in W if tier(r) == t).items())) for t in R["by_tier"]}

    # per-capita
    R["per_capita"] = {cc: {"pop": POP2024[cc], "works": R["country_total_full"][cc],
                            "per_million": R["country_total_full"][cc] / POP2024[cc],
                            "y2025": R["country_year_full"][cc].get(2025, 0),
                            "y2025_per_million": R["country_year_full"][cc].get(2025, 0) / POP2024[cc],
                            "formal_per_million": R["country_total_formal"][cc] / POP2024[cc]} for cc in CA}

    # ---- growth fits
    R["growth"] = {}
    for label, tab in [("full", R["country_year_full"]), ("formal", R["country_year_formal"]),
                       ("narrow", R["country_year_narrow"]), ("frac", R["country_year_frac"])]:
        g = {}
        for cc in ["UZ", "KZ", "KG", "TJ"]:
            s = {int(y): v for y, v in tab[cc].items()}
            if sum(1 for y in range(2010, LAST_FULL_YEAR + 1) if s.get(y, 0) > 0) >= 8:
                g[cc] = growth_fits(s)
        region = R["by_year"] if label == "full" else R["by_year_formal"] if label == "formal" else R["by_year_narrow"] if label == "narrow" else None
        if region:
            g["REGION"] = growth_fits({int(y): v for y, v in region.items()})
        R["growth"][label] = g
    # window sensitivity 2015-2025, full counting
    R["growth"]["full_2015_2025"] = {cc: growth_fits({int(y): v for y, v in R["country_year_full"][cc].items()}, 2015)
                                     for cc in ["UZ", "KZ", "KG"]}
    R["growth"]["full_2015_2025"]["REGION"] = growth_fits({int(y): v for y, v in R["by_year"].items()}, 2015)

    # ---- institutions (domestic, complete universe from authorships)
    R["institutions"] = {}
    inst_rows = []
    for cc in CA:
        cnt, cnt_merged, names = Counter(), Counter(), {}
        nat_works = 0
        domestic_ids = {iid for r in W if cc in r["ca"] for iid, _, _ in r["dom_inst"][cc]}
        for r in W:
            if cc not in r["ca"]:
                continue
            nat_works += 1
            recs = r["dom_inst"][cc]
            for iid, name, lineage in recs:
                cnt[iid] += 1
                names[iid] = name
            # merge rule: collapse a record to its lineage ancestor when that ancestor is itself a
            # domestic record of the same country (child campuses/institutes -> parent); a foreign
            # parent (e.g. Lomonosov MSU for its Dushanbe branch) is never used. Count once per work.
            roots = set()
            for iid, name, lineage in recs:
                anc = [x for x in lineage if x != iid and x in domestic_ids]
                roots.add(anc[0] if anc else iid)
            for rt in roots:
                cnt_merged[rt] += 1
        raw_c = concentration(list(cnt.values()))
        mer_c = concentration(list(cnt_merged.values()))
        top = cnt.most_common(12)
        R["institutions"][cc] = {
            "national_works": nat_works, "raw": raw_c, "merged": mer_c,
            "top_work_share": [(names[i], n, n / nat_works) for i, n in top],
            "top": [(i, names[i], n) for i, n in top],
        }
        for i, n in cnt.most_common():
            inst_rows.append([cc, i, names[i], n, round(n / nat_works, 4), round(n / raw_c["appearances"], 4)])
    with open(OUT / "institutions_domestic_all.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["country", "institution_id", "institution", "works", "share_of_national_works", "share_of_institution_appearances"])
        w.writerows(inst_rows)

    # ---- topics: counts, ids, activity index vs global
    tc = Counter((r["topic_id"], r["topic"], r["subfield"]) for r in W)
    glob = json.load(open(SNAP / "global_topics.json"))
    gcount = {sid(g["key"]): g["count"] for g in glob["group_by"]}
    gtot = sum(gcount.values())
    R["global_topics_total"] = gtot
    rows = []
    for (tid, name, sf), n in tc.most_common():
        share = n / len(W)
        gshare = gcount.get(tid, 0) / gtot if gtot else float("nan")
        ai = share / gshare if gshare else float("nan")
        rows.append([tid, name, SUBF.get(sf, sf), n, round(100 * share, 2), gcount.get(tid, 0), round(100 * gshare, 3), round(ai, 2)])
    with open(OUT / "topics_all.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["topic_id", "openalex_label", "subfield", "works", "share_pct", "global_works_same_subfields",
                    "global_share_pct", "activity_index"])
        w.writerows(rows)
    R["topics_top25"] = rows[:25]
    R["n_topics"] = len(rows)
    # topics by subfield share within corpus
    # ---- sources, OA
    sc = Counter((r["src_id"], r["src_name"], r["src_type"]) for r in W if r["src_id"])
    R["sources_top20"] = [(sid_, name, st, n) for (sid_, name, st), n in sc.most_common(20)]
    R["no_source"] = sum(1 for r in W if not r["src_id"])
    zen = [r for r in W if r["src_id"] == "S4306400562"]
    R["zenodo"] = {"n": len(zen), "by_year": dict(sorted(Counter(r["year"] for r in zen).items())),
                   "by_country": dict(Counter(cc for r in zen for cc in r["ca"]))}
    R["repository_by_year"] = dict(sorted(Counter(r["year"] for r in W if tier(r) == "repository/preprint").items()))
    R["oa"] = dict(Counter(r["oa"] or "unknown" for r in W).most_common())
    R["oa_by_country"] = {cc: dict(Counter(r["oa"] or "unknown" for r in W if cc in r["ca"])) for cc in CA}
    R["lang_by_country"] = {cc: dict(Counter(r["lang"] or "unknown" for r in W if cc in r["ca"]).most_common(5)) for cc in CA}
    R["lang_by_year"] = {l: dict(sorted(Counter(r["year"] for r in W if (r["lang"] or "unknown") == l).items())) for l in ["en", "ru", "uz", "kk"]}
    R["type_by_country"] = {cc: dict(Counter(r["type"] for r in W if cc in r["ca"]).most_common(6)) for cc in CA}
    R["oa_formal"] = dict(Counter(r["oa"] or "unknown" for r in formal).most_common())

    # ---- collaboration
    def group_of(c):
        if c in POST_SOVIET_NON_OECD:
            return "post-Soviet (non-OECD)"
        if c in OECD:
            return "OECD"
        if c in ASIA_NON_OECD:
            return "Asia & Middle East (non-OECD)"
        return "rest of world"
    partner = Counter()
    excl = Counter()
    anyg = Counter()
    intra_ca = 0
    for r in W:
        for c in r["foreign"]:
            partner[c] += 1
        if len(r["ca"]) > 1 and not r["foreign"]:
            intra_ca += 1
        gs = {group_of(c) for c in r["foreign"]}
        for g in gs:
            anyg[g] += 1
        if not gs:
            excl["no foreign co-author"] += 1
        elif len(gs) == 1:
            excl[next(iter(gs))] += 1
        else:
            excl["two or more groups"] += 1
    R["collab"] = {"partners_top25": partner.most_common(25), "any_group": dict(anyg), "exclusive": dict(excl),
                   "intra_ca_only": intra_ca, "with_foreign": sum(1 for r in W if r["foreign"]),
                   "group_membership": {"post-Soviet (non-OECD)": sorted(POST_SOVIET_NON_OECD), "OECD": sorted(OECD),
                                        "Asia & Middle East (non-OECD)": sorted(ASIA_NON_OECD)}}
    R["collab_by_country"] = {}
    for cc in CA:
        rows_cc = [r for r in W if cc in r["ca"]]
        pc = Counter(c for r in rows_cc for c in r["foreign"])
        ag = Counter(g for r in rows_cc for g in {group_of(c) for c in r["foreign"]})
        R["collab_by_country"][cc] = {"n": len(rows_cc), "partners_top8": pc.most_common(8), "any_group": dict(ag),
                                      "with_foreign": sum(1 for r in rows_cc if r["foreign"])}

    # ---- citations / FWCI, full corpus
    def fwci_stats(rows):
        x = [r["fwci"] for r in rows if r["fwci"] is not None]
        m, lo, hi = boot_mean(x)
        xs = np.array(x) if x else np.array([np.nan])
        return {"n": len(rows), "n_fwci": len(x), "mean": m, "mean_ci": [lo, hi], "median": float(np.median(xs)),
                "q1": float(np.percentile(xs, 25)), "q3": float(np.percentile(xs, 75)),
                "share_ge1": float((xs >= 1).mean()), "share_zero_cites": sum(1 for r in rows if r["cites"] == 0) / max(1, len(rows)),
                "share_top10": sum(1 for r in rows if r["top10"]) / max(1, len(rows)),
                "mean_cites": float(np.mean([r["cites"] for r in rows])), "median_cites": float(np.median([r["cites"] for r in rows]))}
    R["fwci"] = {"ALL": fwci_stats(W), "ALL_formal": fwci_stats(formal),
                 "ALL_2010_2023": fwci_stats([r for r in W if r["year"] <= 2023])}
    for cc in CA:
        R["fwci"][cc] = fwci_stats([r for r in W if cc in r["ca"]])
        R["fwci"][cc + "_formal"] = fwci_stats([r for r in formal if cc in r["ca"]])
        R["fwci"][cc + "_2010_2023"] = fwci_stats([r for r in W if cc in r["ca"] and r["year"] <= 2023])
    top200 = sorted(W, key=lambda r: -r["cites"])[:200]
    R["top200"] = {"min_cites": top200[-1]["cites"], "mean_cites": float(np.mean([r["cites"] for r in top200])),
                   "median_cites": float(np.median([r["cites"] for r in top200])),
                   "fwci": fwci_stats(top200), "by_country_full": dict(Counter(cc for r in top200 for cc in r["ca"])),
                   "multi_country": sum(1 for r in top200 if len(r["ca"]) > 1),
                   "top20_cites_sum": int(sum(r["cites"] for r in top200[:20])),
                   "top3": [(r["title"], r["year"], r["cites"], sorted(r["ca"]), r["doi"]) for r in top200[:3]],
                   "by_country_fwci": {cc: fwci_stats([r for r in top200 if cc in r["ca"]]) for cc in CA}}

    # ---- recall variant
    anyt = {sid(w["id"]): parse(w) for w in load_jsonl(SNAP / "works_anytopic.jsonl")}
    extra = [r for i, r in anyt.items() if i not in ids]
    R["anytopic"] = {"N": len(anyt), "extra": len(extra), "primary_in_anytopic": sum(1 for i in ids if i in anyt),
                     "extra_by_field": dict(Counter(r["field"] for r in extra).most_common(12)),
                     "extra_by_subfield_primary": dict(Counter(r["subfield"] for r in extra).most_common(12)),
                     "extra_by_country": dict(Counter(cc for r in extra for cc in r["ca"])),
                     "extra_by_year": dict(sorted(Counter(r["year"] for r in extra).items())),
                     "extra_by_tier": dict(Counter(tier(r) for r in extra)),
                     "extra_top_topics": Counter((r["topic"]) for r in extra).most_common(15)}

    # ---- corpus-definition sensitivity: narrow / primary (main) / any-topic
    def summary(rows, label):
        ct = Counter(cc for r in rows for cc in r["ca"])
        by = Counter(r["year"] for r in rows)
        g = growth_fits({y: by.get(y, 0) for y in range(2010, LAST_FULL_YEAR + 1)})
        tt = Counter(r["topic"] for r in rows).most_common(10)
        return {"label": label, "N": len(rows), "by_country": {cc: ct.get(cc, 0) for cc in CA},
                "rank": [cc for cc, _ in sorted(ct.items(), key=lambda x: -x[1])],
                "y2025": by.get(2025, 0), "y2010": by.get(2010, 0),
                "growth_ols_r": g["ols"]["r"], "growth_ols_ci": g["ols"]["ci"], "growth_nb_r": g.get("nb2", {}).get("r"),
                "formal_share": sum(1 for r in rows if tier(r) == "formal publication") / len(rows),
                "top10_topics": tt,
                "uz_kz_2025": {cc: sum(1 for r in rows if r["year"] == 2025 and cc in r["ca"]) for cc in ["UZ", "KZ"]}}
    R["definition_sensitivity"] = {
        "narrow_1702_1707": summary(narrow, "primary topic in AI or CV subfield"),
        "primary_4subfields": summary(W, "primary topic in the four CS subfields (main corpus)"),
        "anytopic_4subfields": summary(list(anyt.values()), "any assigned topic in the four CS subfields"),
    }

    # ---- audit: Moscow State University Dushanbe record now
    msu = [r for r in W if any(i[0] == "I4210150146" for i in r["dom_inst"]["TJ"])]
    R["audit_now"] = {"works_linked_to_I4210150146": len(msu), "years": dict(sorted(Counter(r["year"] for r in msu).items())),
                      "TJ_total": R["country_total_full"]["TJ"],
                      "TJ_only_via_msu": sum(1 for r in msu if len(r["dom_inst"]["TJ"]) == 1)}

    # ---- snapshot comparison (May aggregate, Sept aggregate, Nov work-level)
    def yearly(p):
        d = json.load(open(p))
        g = d["group_by"] if "group_by" in d else d["years"]
        return {int(x["key"]): x["count"] for x in g}
    snap = {"may": {}, "sept": {}, "nov": {}}
    snap["sept"]["region"] = yearly(SEPT / "year_combined.json")
    snap["may"]["region"] = yearly(MAY / "year_combined.json")
    snap["nov"]["region"] = {int(k): v for k, v in R["by_year"].items()}
    for cc in CA:
        f = SEPT / f"year_{cc.lower()}.json"
        snap["sept"][cc] = yearly(f) if f.exists() else None
        f = MAY / f"year_{cc.lower()}.json"
        snap["may"][cc] = yearly(f) if f.exists() else None
        snap["nov"][cc] = {int(k): int(v) for k, v in R["country_year_full"][cc].items()}
    R["snapshots"] = snap
    # Sept topic list -> subfield distribution via topic->subfield map from Nov records
    t2s = {r["topic_id"]: r["subfield"] for r in W}
    for r in anyt.values():
        for tid, sf in r["topics"]:
            t2s.setdefault(tid, sf)
    st = json.load(open(SEPT / "top_topics.json"))["group_by"]
    sept_sf, unmapped = Counter(), 0
    for g in st:
        sf = t2s.get(sid(g["key"]))
        if sf:
            sept_sf[SUBF.get(sf, sf)] += g["count"]
        else:
            unmapped += g["count"]
    R["sept_subfield_est"] = {"mapped": dict(sept_sf), "unmapped_works": unmapped, "listed_topics": len(st),
                              "listed_total": sum(g["count"] for g in st)}
    R["sept_top20"] = [(g["key_display_name"], g["count"]) for g in st[:20]]
    nov_top20 = {name for _, name, *_ in [(x[0], x[1]) for x in rows[:20]]}
    R["top20_overlap_sept_nov"] = len(nov_top20 & {g["key_display_name"] for g in st[:20]})

    # ---- precision-coding sample (stratified by subfield), seed fixed
    rng = random.Random(20261112)
    quota = {"1702": 120, "1707": 80, "1703": 50, "1712": 50}
    sample = []
    for sf, q in quota.items():
        pool = [r for r in W if r["subfield"] == sf]
        sample += rng.sample(pool, min(q, len(pool)))
    rng.shuffle(sample)
    with open(OUT / "precision_sample.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_no", "openalex_id", "doi", "year", "type", "source", "subfield", "primary_topic", "title",
                    "abstract", "rater1_ai_relevant", "rater2_ai_relevant", "notes"])
        for k, r in enumerate(sample, 1):
            w.writerow([k, r["id"], r["doi"], r["year"], r["type"], r["src_name"], SUBF[r["subfield"]], r["topic"], r["title"], "", "", "", ""])
    R["precision_sample_n"] = len(sample)

    # ---- yearly table csv
    with open(OUT / "yearly_country.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year"] + CA + ["unique_total", "formal_total", "repository_total", "narrow_total"])
        for y in range(2010, 2027):
            w.writerow([y] + [int(R["country_year_full"][cc].get(y, 0)) for cc in CA] +
                       [R["by_year"].get(y, 0), R["by_year_formal"].get(y, 0), R["repository_by_year"].get(y, 0), R["by_year_narrow"].get(y, 0)])

    def default(o):
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (set, tuple)):
            return list(o)
        raise TypeError(str(type(o)))
    (OUT / "results.json").write_text(json.dumps(R, indent=1, default=default, ensure_ascii=False))
    print("wrote", OUT / "results.json")


if __name__ == "__main__":
    main()
