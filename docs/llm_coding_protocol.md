# Language-model coding protocol for the 300-record validation sample

This file documents exactly how the two coding runs behind `results/coding_agentA.csv` and `results/coding_agentB.csv` were produced, so that the procedure can be repeated or criticised. It also states what the resulting agreement does and does not show.

## What the exercise measures

Both runs were executed by the **same** language model. Their agreement (295 of 300 records, Cohen's kappa 0.966; `results/coding_agreement.json`) is therefore **within-model repeated-run agreement**: it shows that the model reproduces its own judgments under the written criterion. It does **not** show that the judgments are correct. The 295 agreements were not checked by a human; only the five disagreements were adjudicated (by the corresponding author, against the complete OpenAlex record). The precision figures derived from these runs (`results/precision_results.json`) are reported in the paper as *model-estimated precision*, not as validated precision. A further dependence should be noted: OpenAlex's current topic classifier was trained on topic choices made by Claude Opus 5.5 (see https://help.openalex.org/data/topics/ and the `v2/README.md` of https://github.com/ourresearch/openalex-topic-classification), a model from the same developer as the coder used here, so the estimate is not independent of the classifier it evaluates. Independent human coding of the same sample (`results/precision_sample.csv`) is the obvious next step; a blank coding sheet for that purpose can be generated from that file.

## Model and settings

| Item | Value |
|---|---|
| Model | Claude Fable 5.1 (Anthropic), model identifier `claude-fable-5-1` |
| Access path | Anthropic's Claude Code agent interface (two sub-agent runs started from one session) |
| Date | 12 November 2026 (runs started 12:37 UTC, seven seconds apart) |
| Sampling | Interface defaults; the interface exposes no temperature or top-p control, so none was set |
| System prompt | The interface's own tool-use harness; no task-specific system prompt |
| Examples / few-shot | None |
| Retrieval, web access, tools | File reading and Python only (to print the sample in batches); no web access; no access to the OpenAlex topic labels beyond the two columns present in the CSV, which the prompt instructed the model to ignore |
| Shared state | None: each run was a fresh context; neither run could read the other's output file |
| Input | `results/precision_sample.csv` (300 rows, with abstracts for the 256 records that have one in OpenAlex) |
| Output | `results/coding_agentA.csv`, `results/coding_agentB.csv` (300 rows each: `sample_no, openalex_id, ai_relevant, confidence, note`) |

## Prompt (verbatim)

The two prompts were identical except for the coder letter ("Coder A" / "Coder B") and the output file name (`coding_agentA.csv` / `coding_agentB.csv`). Absolute paths have been shortened to the archive layout; nothing else was changed.

```
You are Coder A in a two-coder content-analysis task for a bibliometric paper. Work entirely alone; do not look for or read any other coder's output or any file other than the one named below.

Input: results/precision_sample.csv (300 rows; columns sample_no, openalex_id, doi, year, type, source, subfield, primary_topic, title, abstract, ...). Read it with Python (csv module) and print the records in batches of about 25 (sample_no, title, abstract truncated to ~600 characters) so that you actually read every record. Do not use keyword matching or any automated rule to decide; read and judge each record on its content.

Criterion. Code 1 (AI-relevant) if the record's principal contribution develops, evaluates, or applies a machine-learning, knowledge-representation, reasoning, natural-language, speech, vision, robotics, or agent-based method, OR studies the use, adoption, ethics, pedagogy, or governance of such methods. Code 0 (not AI-relevant) if it only mentions AI in passing; is pure mathematics (algebra, matrix theory, computability, optimization theory without a learning component); is cryptography, steganography, or security without any learning component; is general software, web, mobile, database, or network engineering; is a dataset or software record with no AI method described; or if the abstract is missing AND the title gives no AI indication. Decide on content, not on the OpenAlex topic label in the subfield/primary_topic columns. Abstracts may be in Russian or Uzbek; read them in that language.

Output: write results/coding_agentA.csv with header sample_no,openalex_id,ai_relevant,confidence,note — ai_relevant is 0 or 1; confidence is high/medium/low; note is at most 12 words giving the reason (e.g., "CNN for crop disease images", "pure graph theory", "no abstract, title generic"). Exactly 300 rows, one per sample_no, in the original order. After writing, print the counts of 1 and 0 overall and per subfield, and report them in your final message along with the path.
```

## Adjudication

The five records on which the runs disagreed (`results/coding_disagreements.csv`) were resolved by the corresponding author against the complete OpenAlex record (full abstract, keywords, topics) under one additional rule: a corpus, dataset, or benchmark built explicitly for an AI task counts as relevant; the word "intelligent" in a title without an abstract does not. The adjudicated values are the `final` column of `results/precision_sample_coded.csv`; precision per subfield with Wilson 95% intervals and the corpus-weighted estimate are in `results/precision_results.json`.
