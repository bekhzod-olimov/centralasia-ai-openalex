# Central Asia AI-related research output in OpenAlex, 2010–2026

Reproducibility archive for:

> Olimov B. et al. *Mapping Artificial Intelligence Research Output Across Central Asia (2010–2026): A Bibliometric Assessment of OpenAlex Data, Institutional Attribution, and Topic-Classification Drift.* Frontiers in Research Metrics and Analytics (manuscript 2022866, under review).

Everything reported in the paper is computed from the files in this repository; no proprietary database is needed.

## Corpus definition

OpenAlex works, publication years 2010–2026, with at least one authorship affiliated with an institution in UZ, KZ, KG, TJ or TM, and primary topic in the Computer Science subfields 1702 (Artificial Intelligence), 1707 (Computer Vision and Pattern Recognition), 1703 (Computational Theory and Mathematics) or 1712 (Software):

```
filter=authorships.institutions.country_code:uz|kz|kg|tj|tm,
       primary_topic.subfield.id:subfields/1702|subfields/1707|subfields/1703|subfields/1712,
       publication_year:2010-2026
```

## Layout

| Path | Content |
|---|---|
| `data_snapshot_2026-11-12/works_primary.jsonl.gz` | 9,358 complete work records (main corpus), retrieved 12 Nov 2026 with `code/pull_works.py` |
| `data_snapshot_2026-11-12/works_anytopic.jsonl.gz` | 20,036 records of the broad definition (`topics.subfield.id`, any assigned topic) |
| `data_snapshot_2026-11-12/global_topics.json` | world counts per primary topic in the four subfields, 2010–2026 (activity-index baseline) |
| `data_snapshot_2026-11-12/meta_works.json` | retrieval metadata (filters, fields, counts) |
| `data_snapshot_2026-09-03/` | aggregate (`group_by`) responses of the identical query on 3 Sept 2026, retrieved with `code/pull_data.py` (OpenAlex topic classifier v1) |
| `data_snapshot_2026-05-30/` | aggregate responses of the identical query on 30 May 2026 (contains the Moscow State University / Dushanbe attribution error) |
| `code/pull_works.py` | work-level retrieval (page-based paging, one query per year, de-duplication asserted against API counts) |
| `code/pull_data.py` | aggregate retrieval used for the May and September snapshots |
| `code/analysis_r1.py` | every indicator in the paper → `results/results.json` and CSV tables |
| `code/make_figures_r1.py` | Figures 1–8 |
| `code/fetch_abstracts.py` | abstracts for the 300-record precision-coding sample |
| `results/results.json` | all numbers quoted in the paper |
| `results/topics_all.csv` | 125 primary topics: counts, global counts, activity index |
| `results/institutions_domestic_all.csv` | 318 domestic institution records with both share denominators |
| `results/yearly_country.csv` | annual counts per country, channel and definition |
| `results/precision_sample.csv` | the stratified 300-record sample with abstracts |
| `results/precision_sample_coded.csv` | the sample with both coders' decisions, confidence and reasons, and the adjudicated value |
| `results/coding_agentA.csv`, `coding_agentB.csv` | raw output of the two independent coding runs (Claude, Anthropic; written criterion in the paper, Section 3.3) |
| `results/coding_agreement.json`, `precision_results.json` | agreement (295/300, kappa 0.966), per-subfield precision with Wilson intervals, corpus-weighted precision |
| `figures/` | PNG renderings of the eight figures |

## Reproduce

```bash
pip install numpy scipy statsmodels matplotlib
cd code
gunzip -k ../data_snapshot_2026-11-12/*.jsonl.gz
python analysis_r1.py        # writes ../results/*
python make_figures_r1.py    # writes ../figures/*
```

`analysis_r1.py` expects the directory layout above (it resolves paths relative to its own location); edit the `SNAP`, `SEPT`, `MAY` constants if you move files. Re-running `pull_works.py` against the live API will return a different corpus, because OpenAlex is continuously updated and replaced its topic classifier on 7 October 2026; the frozen records here are the analytical baseline.

## Snapshot and classifier versions

| Snapshot | Classifier | Corpus size |
|---|---|---|
| 30 May 2026 | v1 | 7,248 |
| 3 Sept 2026 | v1 | 7,137 |
| 12 Nov 2026 | v2 (title/abstract model, announced 7 Oct 2026) | 9,358 |

The v1 assignments frozen on 5 Oct 2026 are published by OpenAlex at https://github.com/ourresearch/openalex-topic-classification/releases/tag/v2.0.0 and can be joined to the records here by work id.

## Redactions

E-mail addresses that OpenAlex returns inside `raw_affiliation_strings` (author contact lines copied from publisher metadata) were replaced by `[email redacted]` in every data file; no other field was altered, and no indicator in the paper uses that field. The retrieval scripts carry the placeholder `mailto:YOUR_EMAIL_HERE` in the User-Agent header; insert your own address, as the OpenAlex polite-pool policy asks.

## Licenses

Code: MIT (`LICENSE`). Data: the OpenAlex records are CC0 and are redistributed unchanged under CC0 (`LICENSE-DATA.md`). Derived tables and figures: CC BY 4.0.

## Citation

See `CITATION.cff`.
