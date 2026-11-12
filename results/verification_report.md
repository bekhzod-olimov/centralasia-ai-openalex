# Verification report: main_frma_r1.tex against results files and scripts

Verifier run: 2026-11-12. Sources used: `out/results.json`, `out/numbers_sheet.txt`, `out/precision_results.json`, `out/coding_agreement.json`, `out/precision_sample_coded.csv`, `out/topics_all.csv`, `out/institutions_domestic_all.csv`, `out/yearly_country.csv`, `out/fetch_abstracts.log`, `analysis_r1.py`, `make_figures_r1.py`, `../pull_works.py`, `../pull_data.py`, `fetch_abstracts.py`, `../data_snapshot_2026-11-12/{works_primary.jsonl,works_anytopic.jsonl,global_topics.json,meta_works.json}`, `../data_snapshot_2026-11-12_pull.log`, `../data/` (September aggregates), `../data_snapshot_2026-05-30/` (May aggregates). Record-level quantities (channel splits by type, repository share by year, OA status of non-formal works, total citations) were recomputed from `works_primary.jsonl` with `analysis_r1.parse` and `analysis_r1.tier`.

## 1. Mismatches found

| # | Location | Manuscript says | Source says | Severity |
|---|----------|-----------------|-------------|----------|
| 1 | §4.8 Citation impact, text after Table 12 | "The non-overlapping bootstrap intervals for Kazakhstan and Uzbekistan indicate that the difference is not sampling noise" | results.json `fwci.KZ.mean_ci` = 0.568–0.673, `fwci.UZ.mean_ci` = 0.443–0.585. The intervals overlap on 0.568–0.585 (also visible in Table 12 itself: 0.57–0.67 vs 0.44–0.58). | High (incorrect statistical inference) |
| 2 | §4.2 Headline volume, "First" paragraph | "Fractional counting changes these totals by less than 1%" | `country_total_full` vs `country_total_frac`: UZ −0.48%, KZ −0.70%, KG 375 → 359.3 = −4.2%, TJ 59 → 58.3 = −1.2%, TM 0%. Claim false for Kyrgyzstan and Tajikistan. | Medium |
| 3 | §4.6 Venues, repository-deposition paragraph | "The channel's share of annual output was 3–5% through 2021" | Recomputed from records (repo ÷ unique works): 2010 11.1%, 2011 0%, 2012 5.9%, 2013 5.9%, 2014 6.9%, 2015 5.8%, 2016 3.6%, 2017 9.7%, 2018 7.7%, 2019 2.6%, 2020 3.3%, 2021 5.3%. Within the figure window 2016–2021 the range is 2.6–9.7%; only 2016 and 2020 fall inside 3–5%. The 2022–2023 (11.5, 12.6), 2024 (4.3), 2025 (8.6), 2026 (23.8) figures are correct. | Medium |
| 4 | Appendix A.1 | "The November pull used 183 list requests" | `../data_snapshot_2026-11-12_pull.log`: sum over years of ceil(count/200) = 57 (primary) + 109 (any-topic) = 166 list requests; plus one `group_by` request for the global baseline = 167. 183 is not reproducible from the log or from `pull_works.py` (which issues exactly ceil(count/200) requests per year). | Medium (reproducibility statement) |
| 5 | §4.4 Concentration indices paragraph | "Merging child records into domestic parents changes every index by less than 0.02 (HHI) or 0.011 (Gini)" | Gini raw → merged: UZ 0.7194 → 0.7076 (Δ = 0.0118), TJ 0.4748 → 0.4571 (Δ = 0.0177), KZ Δ = 0.0074. Two of the five Gini changes exceed 0.011. HHI changes (max 0.018, TJ) are below 0.02 as stated. | Low–medium |
| 6 | §4.4 Concentration indices paragraph | Top-2 work shares "39.0% and 29.3%" | KZ: 832/4017 + 736/4017 = 20.71 + 18.32 = 39.03 → 39.0 (OK). UZ: 1001/4959 + 449/4959 = 20.19 + 9.05 = 29.24 → 29.2, not 29.3 (29.3 arises only by adding the rounded table entries 20.2 + 9.1). | Low |
| 7 | Abstract, last sentences | "which halved the 2010–2013 counts and raised the 2023–2025 counts by a quarter" | Table 13 / snapshot files: 2010–2013 fell 192 → 75 (−61%, i.e. more than halved, to 39%); 2023–2025 rose 3,181 → 4,128 (+29.8%, i.e. closer to "by 30%" / "by a third" than "by a quarter"). | Low (approximation drift) |
| 8 | §4.9, "September to November" paragraph | "1,660 works (23.3%) whose primary topic belongs ... to a subfield outside computer science" | `sept_subfield_est.mapped` includes CS subfields 1705 (46 works), 1708 (12), 1704 (9) = 67 works inside Computer Science but outside the four target subfields. The sum 1,660 and 23.3% are correct only for "outside the four target subfields" (which is how Table 13 words it); "outside computer science" overstates. | Low |
| 9 | §4.6 Open access paragraph | "because repository deposits are by construction green or diamond" | Recomputed OA status of the 1,220 non-formal works: green 1,190, diamond 7, closed 14, gold 8, bronze 1. Not "by construction"; 23 exceptions. | Low |
| 10 | §4.6 Open access paragraph | "The closed share is highest for Kazakhstan (33.5%) and lowest for Uzbekistan (27.3%)" | `oa_by_country` closed: KZ 33.5, KG 29.6, UZ 27.3, TM 25.0, TJ 15.3. Uzbekistan is lowest only among the three countries with >100 works (the figure's scope); unqualified in the text. | Low |
| 11 | Table 4 caption | "Years: number of non-zero years used by OLS (NB uses all 16)" | For the 2015–25 block NB uses 11 years (`full_2015_2025.*.n_years` = 11). | Low |
| 12 | Figure 1 caption | "Annual AI-related output per country ... (a) Linear scale. (b) ... Tajikistan and Turkmenistan are omitted from (b)" | `make_figures_r1.fig1` plots KZ, UZ, KG, TJ in panel (a) — Turkmenistan is omitted from (a) too, which the caption does not say. | Low |
| 13 | Appendix A.1 field list | "selecting the fields id, doi, title, publication_year, publication_date, type, language, primary_location, open_access, authorships, cited_by_count, fwci, citation_normalized_percentile, primary_topic, topics, indexed_in, is_retracted" | `pull_works.py` SELECT (and `meta_works.json`) also includes `institutions_distinct_count, countries_distinct_count, is_paratext, referenced_works_count, created_date, updated_date` (23 fields, not 17). | Low |
| 14 | §4.4 "Two differently shaped leading systems" | "the top five institutions appear on 72.6% of national works" (KZ) / "the top five appear on 47.5% of works" (UZ) | 72.6 and 47.5 are the sums of the five individual work shares (20.7+18.3+14.6+10.2+8.8 = 72.6; 20.19+9.05+6.57+6.31+5.42 = 47.5), not the share of works carrying at least one top-5 institution (a union, which the wording "appear on x% of works" implies and which must be smaller because works carry several domestic institutions). Values match the source as sums; the phrasing is the issue. | Low (wording) |

No other numeric mismatches were found. In particular, every cell of Tables 1–13 that could be derived from the files agreed with the source (details in Section 3).

## 2. Claims that could not be verified from the files

1. Table 13 / §4.9 "Other drift": Turkmenistan all-subject count **870** (November). Not present in any file under the project directory (grep over data, scripts, logs, tex); only the September value 4,433 is in `../data/tm_all_subjects.json`. **Not reproducible from files** (recorded from a live API check in conversation, per the task brief).
2. §3.1: OpenAlex taxonomy "4,516 topics, 252 subfields"; classifier replacement on 7 October 2026; frozen assignments of 5 October 2026 (external OpenAlex claims).
3. §3.2: "The API accepts the subfield identifiers with or without the `subfields/` prefix; both forms return identical counts" — the corpus pull used the prefixed form and the global baseline the unprefixed form on different filters; no file compares both forms on the same filter.
4. §3.9 / Table 3: World Bank 2024 populations (36.4, 20.6, 7.2, 10.6, 7.5 M) — external; per-million values were verified arithmetically against these inputs as stored in `per_capita`.
5. Limitations (sixth): "OpenAlex reports that institution-level mean FWCI moved by a median of 4.5% at the change" — external.
6. §4.6: geographic attributions "UBMK in Türkiye, SIST in Kazakhstan, ICISCT in Uzbekistan"; "all Kazakhstani venues indexed by OpenAlex but not by the commercial databases" — not in files.
7. §4.4: "Mamun (Khiva)", University of Central Asia campus description, Nazarbayev University strategy — external.
8. Appendix A.1: "the May 2026 aggregates were produced by the same script" — no May pull log or script version is archived.
9. §3.3: adjudication rule and the `\TODO{BO: confirm the five adjudications}` — the five adjudicated values exist in `precision_results.json` (`adjudication`: 49→1, 125→1, 175→1, 290→0, 294→1) but the manuscript's own TODO marks them unconfirmed.
10. §4.9: "the Moscow parent's works ... By September OpenAlex's affiliation matching had re-linked those works to Moscow" — the mechanism is inferred; only the counts (1,250 → 38 → 1) are in the files.
11. Data Availability: GitHub release v1.0.0 and licenses — external.

## 3. Claims checked (count and coverage)

| Section / table | Items checked | Result |
|---|---|---|
| Abstract | 24 numeric/procedural claims | 23 OK; 1 approximation issue (#7) |
| Introduction (>1,000 Moscow works; corpus changed by a third = +31%) | 2 | OK |
| §3.1–3.2 Methods (filter string, 9,358, page-based paging per year, de-dup matched API count every year, snapshot dates) | 8 | OK (log confirms 17/17 years matched) |
| §3.3 Validation (300; 120/80/50/50; seed 20261112; 256 abstracts; two coders; κ; Wilson; corpus-weighting) | 10 | OK (quota and seed in `analysis_r1.py` lines 438–439; `fetch_abstracts.log`: "done 256 with abstracts of 300") |
| §3.4 Counting (66 two-country, 1 three-country, 9,426 sum) | 4 | OK (`multi_ca` 9291/66/1; 9358+66+2 = 9,426) |
| §3.5 Channel rule (type list, repository override) | 3 | OK vs `tier()`; manuscript list matches code list exactly |
| §3.6 Institutions (153/120/27/14/4; HHI, N_eff, Gini formulas; merge rule) | 9 | OK vs `concentration()` and merge code (lines 243–251) |
| §3.7 Activity index (N = 9,358; G = 4,400,019; 125 topics) | 4 | OK (`global_topics.json` meta count 4,400,019, 127 groups fully returned, sum equals count) |
| §3.8 Collaboration groups (7 post-Soviet, 38 OECD incl. TR/JP/KR/IL/Baltics, Asia list, precedence) | 6 | OK (OECD set has 38 codes; post-Soviet 7; code checks post-Soviet before OECD) |
| §3.9–3.10 Citation and growth methods (HC1, DW, Poisson deviance/df, NB2, ln2/r, 2026 excluded, 2,000 resamples, 2015–2025 window) | 10 | OK vs `growth_fits()`, `boot_mean(B=2000)` |
| §4.1 Corpus composition (4 subfield counts + shares; 12.5%; 5 language counts + shares; 219 no code; 64 retracted) | 19 | OK |
| §4.1 Precision (295/300, 98.3%, κ 0.97, nature of 5 disagreements, 168/300 56.0% CI, 4 per-subfield k/n/p/CI, 71.1%, 79.5%, 12.5%) | 24 | OK (disagreement rows 49/125/175 datasets, 290 "Intelligent Robot" no abstract, 294 pedagogy model confirmed in CSV) |
| §4.1 Definition variants text (8,185; 87.5%; 20,036; 2.14×; 10,678; 5 extra topics; 5 fields; rank order; 1.6–1.7; 86–87%; 31–39%) | 20 | OK (AI in Education subfield = Education confirmed from `works_anytopic.jsonl`) |
| Table 1 (3 columns × 10 rows) | 30 cells | All OK |
| §4.2 text (18 → 2,079; 6/17; 103; twentyfold; 53.0/42.9/4.0/0.6/0.2; 67 multi-country; 462 vs 408; 1,241 vs 744; 1,142 vs 690; 792 vs 750; 1,956; populations and per-million values) | 26 | 25 OK; 1 mismatch (#2) |
| Table 2 (17 years × 8 columns + full totals + fractional totals + footnote) | 150 cells | All OK; column sums recomputed: UZ 4,959, KZ 4,017, KG 375, TJ 59, TM 16 (sum 9,426), Total 9,358, formal 8,138, repository 1,205, 15 other; fractional row sums to 9,357.9 |
| Table 3 (5 rows × 5 numeric columns) | 25 cells | All OK (recomputed from population and counts) |
| §4.3 text (8.8/5.2/9.1; 32.6%, CI, 2.1; 34.0%, CI, R² 0.96, DW 1.81; <0.5 pt formal; 47%/1.5; 51%; 28%/2.5; DW 0.60; 23%; 33%; 7 zero years; 14% vs 28%) | 18 | OK |
| Table 4 (13 rows × 8 columns) | 104 cells | All OK (rates = 100 × stored r; CIs, R², DW, doubling = ln2/r_NB, non-zero years) |
| Tables 5–7 (UZ 10 × 3, KZ 10 × 3, small 12 × 2 numeric) | 84 cells | All OK (work shares = works/N; appearance shares = works/A, recomputed) |
| §4.4 text (20.7, 18.3, 72.6, 20.2, 47.5, eighth-largest, 11–12 each, 14 records, 38, 1,250, 1, Gini 0.77/16.4, 0.72/26.5, 26.1/19.9, 39.0/29.3, 12 eff./0.58, <8 eff., merge deltas) | 22 | 19 OK; #5, #6, #14 |
| Table 8 (5 rows × 9 columns) | 45 cells | All OK |
| Table 9 (20 rows × id, label, subfield, works, share, AI) | 120 cells | All OK; activity index recomputed for all 125 topics from `topics_all.csv` with G = 4,400,019: 0 mismatches |
| §4.5 text (1,916 = 924+383+382+227; 20.5%; 4.3; 2.4; 3.9/3.1/2.6/2.2/4.1; 0.97/0.57; 0.55 rank 23; 0.66 rank 24; 113/3.9; 125 in top 25; four Sept topics 138–285) | 20 | OK |
| Table 10 (8 type rows × count/share/channel split + 3 channel totals) | 30 cells | All OK; channel splits recomputed from records: article 4,774/494; conference 2,995/176; dataset 169/4; "other" 162 = 84 formal + 67 repository + 11 other |
| Table 11 (15 sources × count/type) | 30 cells | All OK |
| §4.6 text (782/112/69/66; 1,205/12.9%; 673; 544; channel shares by year; 1,038 = 172+157+158+150+132+97+90+82; 33.9%; 530/126; 64/59; 44/0.5%) | 20 | 19 OK; 1 mismatch (#3) |
| §4.6 OA (25.2/10.6/13.8/5.8/14.7; 70.1; 29.9; 34.2 = 2,787/8,138; 33.5; 27.3) | 10 | 10 numeric OK; #9, #10 wording |
| §4.7 (2,775/29.7%; 51; 6,583/70.3%; 4 group counts + shares; 552/5.9%; 3 exclusive counts + shares; 8 partner counts; KZ 35.7%, 5 partners, 6.9%, 19.5%; UZ 24.1%, 5 partners, 9.6%, 14.8/8.3; KG 4 partners; TJ 16/59 27.1%) | 48 | All OK |
| Table 12 (9 rows × 8 + 4 top-200 rows) | 86 cells | All OK (n_F 195 for top-200 confirmed) |
| §4.8 text (0.55 CI; median 0; 61%; 14%; 0.10; 38%; 0.51; 14%; 5.5% ≈ half of 10%; 0.62/0.51; 0.07/0.00; 48/72; ≥30; mean 61; median 45; 5.74; 98%; 119/73/9, 201; 7.49 CI n=73; 4.82 CI n=119; top-3 titles/citations/countries; 3,646; >tenth = 11.2% of 32,658) | 30 | 29 OK; 1 mismatch (#1) |
| Table 13 (3 columns × 13 quantities + footnote) | 36 cells | 35 OK against raw May/Sept aggregates and results.json (corpus 7,248/7,137/9,358; all country totals; MSU 1,250/38/1; TJ 2010 106/2/0; 2010–13 554/192/75; 2023–25 3,148/3,181/4,128; 1,660/23.3%; 151/2.1%; 140 topics; 656 = 530+126; 10 of 20 shared; 4,433); 870 unverifiable |
| §4.9 text (1,317 → 116; 7,248 → 7,137; 106 vs 2; May top-cited Tajik "work" with US/Moscow authors; Gini 0.85; lineage now points to Moscow parent; +31%; direction of change per country; 192 → 75; 3,181 → 4,128; half of top 20; 1,660; 530/126; almost all ≥2023; +66% / +8%; 4,433 → 870; 23 → 16) | 20 | 18 OK (May Gini from `inst_tj.tsv` = 0.847; May top-cited TJ-flagged work "Averaging Weights Leads to Wider Optima..." 616 cites, RU/TJ/US; November record lineage includes I19880235); #8; 870 unverifiable |
| Discussion / Limitations / Conclusions (72% uncited; two fifths; 59; 49%; 27%; 16 works/4 institutions; 31–39%; 2023 vs 2025 parity; 71%; 9,358 of 20,036; <0.02; 716 of 3,013; a third/two years; 61%; 14%; 34%) | 17 | OK |
| Appendix A (per-page 200, page paging per year, field list, de-dup assertion, group_by baseline, single-entity abstracts, 183 requests, USD 0.0001, pull_data.py group_by + 200 most-cited, parse fields, HC1/Poisson/NegativeBinomial, 2,000 resamples, seeded sampling, outputs: 125 topics, 318 institution rows, 29,394 = 9,358+20,036; Python 3.12 / numpy 2.x / statsmodels 0.15) | 20 | 18 OK (318 rows in `institutions_domestic_all.csv`; 125 rows in `topics_all.csv`; cost_usd 0.0001 in API meta; env 3.12.3 / 2.2.6 / 0.15.0); #4, #13 |
| Figure captions (Fig. 1 omissions; Fig. 3 window 2016–2026; Fig. 4 top eight, four countries; Fig. 5 top 20; Fig. 6 four countries >50 works; Fig. 7 three countries >100 works, label threshold 6%; Fig. 8 twenty partners) | 9 | 8 OK; #12 |

**Total claims checked: approximately 1,170 (about 820 table cells and about 350 text/procedural statements). Mismatches: 14 (1 high, 3 medium, 10 low). Unverifiable from files: 11 items, of which the 870 Turkmenistan count is the only numeric table cell.**
