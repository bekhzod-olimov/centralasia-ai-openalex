# Central Asia AI-related research output in OpenAlex, 2010–2026

Reproducibility archive for:

> Olimov B. et al. *Mapping Artificial Intelligence Research Across Central Asia (2010–2026): A Bibliometric Assessment of OpenAlex Data, Institutional Attribution, and Topic-Classification Drift.* Frontiers in Research Metrics and Analytics (manuscript 2022866, under review).

Every number and figure in the paper is computed from the files in this repository; no proprietary database is needed. Release v1.1.0 (24 Nov 2026) corrects the layout and documentation problems of v1.0.0 and the negative-binomial fits (see *Changes* below).

## Corpus definition

OpenAlex works, publication years 2010–2026, with at least one authorship affiliated with an institution in UZ, KZ, KG, TJ or TM, and primary topic in the Computer Science subfields 1702 (Artificial Intelligence), 1707 (Computer Vision and Pattern Recognition), 1703 (Computational Theory and Mathematics) or 1712 (Software):

```
filter=authorships.institutions.country_code:uz|kz|kg|tj|tm,
       primary_topic.subfield.id:subfields/1702|subfields/1707|subfields/1703|subfields/1712,
       publication_year:2010-2026
```

## Reproduce (three commands)

```bash
pip install -r requirements.txt          # pinned versions; Python 3.12
gunzip -k data_snapshot_2026-11-12/*.jsonl.gz
python code/analysis_r1.py               # writes results/results.json and results/*.csv (about 1 minute)
python code/make_figures_r1.py           # writes figures/fig1_*.png ... fig8_*.png (and .tif)
```

The scripts resolve every path relative to the repository root (`code/analysis_r1.py` uses `Path(__file__).parent.parent`), so they can be run from any working directory. `CA_OUT=<dir>` and `CA_FIG=<dir>` override the output directories. Running `analysis_r1.py` with `python -W error` succeeds: no warning of any kind is emitted.

Re-running `code/pull_works.py` against the live API returns a different corpus, because OpenAlex is continuously updated, replaced its topic classifier on 6–7 October 2026 and revised its topic hierarchy in November 2026; the frozen records here are the analytical baseline.

## Layout

| Path | Content |
|---|---|
| `data_snapshot_2026-11-12/works_primary.jsonl.gz` | 9,358 complete work records (main corpus), retrieved 12 Nov 2026 with `code/pull_works.py` |
| `data_snapshot_2026-11-12/works_anytopic.jsonl.gz` | 20,036 records of the broad definition (`topics.subfield.id`, any assigned topic) |
| `data_snapshot_2026-11-12/global_topics.json` | world counts per primary topic in the four subfields, 2010–2026 (activity-index baseline) |
| `data_snapshot_2026-11-12/topic_hierarchy_as_of_snapshot.csv` | topic → subfield/field/domain placement embedded in the 12 Nov records (1,675 topics) |
| `data_snapshot_2026-11-12/meta_works.json` | retrieval metadata (filters, fields, counts) |
| `data_snapshot_2026-09-03/` | **aggregate** (`group_by`) responses of the identical query on 3 Sept 2026, retrieved with `code/pull_data.py` (classifier v1, pre-revision hierarchy). No work-level records exist for this snapshot. |
| `data_snapshot_2026-05-30/` | **aggregate** responses of the identical query on 30 May 2026 (contains the Moscow State University / Dushanbe attribution error). No work-level records exist for this snapshot. |
| `reference_topic_hierarchy/topics_v1_hierarchy_2026-10-06.json` | OpenAlex's topic list with subfield placements as committed to `ourresearch/openalex-topic-classification` (`v2/data/topics/topics.json`) on 6 Oct 2026, i.e. the hierarchy in force under classifier v1 and at the classifier replacement |
| `reference_topic_hierarchy/topics_live_2026-11-24.csv` | all 4,516 topics from `api.openalex.org/topics` on 24 Nov 2026 (post-revision hierarchy) |
| `code/pull_works.py` | work-level retrieval (page-based paging, one query per year, de-duplication asserted against API counts) |
| `code/pull_data.py` | aggregate retrieval used for the May and September snapshots |
| `code/analysis_r1.py` | every indicator in the paper → `results/` |
| `code/make_figures_r1.py` | Figures 1–8, numbered as in the paper |
| `code/fetch_abstracts.py` | abstracts for the 300-record precision-coding sample |
| `docs/llm_coding_protocol.md` | model, date, settings and verbatim prompt of the two language-model coding runs, and what their agreement does and does not show |
| `results/results.json` | all numbers quoted in the paper, including the convergence record (`method`, `converged`, `alpha`, `llf`) of every growth fit and the topic-hierarchy comparison (`hierarchy`) |
| `results/topics_all.csv` | 125 primary topics: counts, global counts, activity index |
| `results/institutions_domestic_all.csv` | 318 domestic institution records with both share denominators |
| `results/yearly_country.csv` | annual counts per country, channel and definition |
| `results/topic_hierarchy_moves.csv` | the 22 topics moved out of, and 13 moved into, the four subfields by the November 2026 hierarchy revision, with September and November work counts |
| `results/precision_sample.csv` | the stratified 300-record sample with abstracts |
| `results/precision_sample_coded.csv` | the sample with both runs' decisions, confidence and reasons, and the adjudicated value |
| `results/coding_agentA.csv`, `coding_agentB.csv` | raw output of the two coding runs (same model; see `docs/llm_coding_protocol.md`) |
| `results/coding_disagreements.csv` | the five records on which the runs disagreed, with the adjudication |
| `results/coding_agreement.json`, `precision_results.json` | within-model repeated-run agreement (295/300, kappa 0.966), per-subfield model-estimated precision with Wilson intervals, corpus-weighted estimate |
| `figures/` | PNG and TIF renderings of the eight figures: `fig1_trajectories`, `fig2_institutions`, `fig3_topics`, `fig4_channel_by_year`, `fig5_open_access`, `fig6_collaboration`, `fig7_fwci`, `fig8_snapshot_drift` |

## Snapshot, classifier and hierarchy versions

| Snapshot | Classifier | Topic hierarchy | Corpus size | Archived as |
|---|---|---|---|---|
| 30 May 2026 | v1 | pre-revision | 7,248 | aggregates only |
| 3 Sept 2026 | v1 | pre-revision | 7,137 | aggregates only |
| 12 Nov 2026 | v2 (announced 7 Oct 2026 UTC) | November 2026 revision (56 topics renamed, 972 moved) | 9,358 | complete records |

OpenAlex does not version the hierarchy. That the 12 Nov records already carry the revised hierarchy was established by comparison: their embedded placements match the live API of 24 Nov 2026 for all 1,675 topics present and differ from the 6 Oct 2026 file for 371 of them (`results/results.json` → `hierarchy`). The v1 per-work assignments frozen on 5 Oct 2026 are published by OpenAlex at https://github.com/ourresearch/openalex-topic-classification/releases/tag/v2.0.0 and can be joined to the records here by work id.

## Changes in v1.1.0 (24 Nov 2026)

- **Negative-binomial fits.** v1.0.0 called `NegativeBinomial(...).fit(disp=0, maxiter=500)` from default start values without checking `mle_retvals["converged"]`. For the Uzbek series (full, formal and fractional counts) the optimizer stopped at a non-converged point with alpha ≈ 1e-4 and returned the Poisson slope (47.3 %/yr) with a Poisson interval. Fits are now started from the Poisson coefficients, accepted only on reported convergence with an invertible Hessian, and cross-checked against a profile likelihood over alpha; boundary cases (alpha → 0) are reported as Poisson and flagged. Corrected Uzbek NB rates: 38.3 %/yr (95 % CI 31.8–44.8; full counting), 39.1 %/yr (formal channel), 38.3 %/yr (fractional). No other estimate changed by more than rounding. The script now runs without any warning.
- **Paths.** The September snapshot is read from `data_snapshot_2026-09-03/` (v1.0.0 looked for `../data`); outputs go to `results/` as the README always said (v1.0.0 wrote to `code/out/`); the figure script reads `results/results.json`.
- **Figure numbering** now follows the paper (v1.0.0 file numbers did not).
- **Topic hierarchy**: three hierarchy tables added and compared; `results/topic_hierarchy_moves.csv` added.
- **Pinned environment** (`requirements.txt`) and the **language-model coding protocol** (`docs/llm_coding_protocol.md`) added.
- `fwci_stats` no longer computes statistics on empty groups (Tajikistan and Turkmenistan have no works among the 200 most cited).

## Redactions

E-mail addresses that OpenAlex returns inside `raw_affiliation_strings` (author contact lines copied from publisher metadata) were replaced by `[email redacted]` in every data file; no other field was altered, and no indicator in the paper uses that field. The retrieval scripts carry the placeholder `mailto:YOUR_EMAIL_HERE` in the User-Agent header; insert your own address, as the OpenAlex polite-pool policy asks.

## Licenses

Code: MIT (`LICENSE`). Data: the OpenAlex records are CC0 and are redistributed unchanged under CC0 (`LICENSE-DATA.md`). Derived tables and figures: CC BY 4.0.

## Citation

See `CITATION.cff`.
