#!/usr/bin/env python3
"""Figures for the revised manuscript (snapshot 2026-11-12). Reads out/results.json and the raw corpus."""
import json, math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import analysis_r1 as A

HERE = Path(__file__).parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
R = json.load(open(HERE / "out" / "results.json"))
W = [A.parse(w) for w in A.load_jsonl(A.SNAP / "works_primary.jsonl")]

# fixed categorical slots (colourblind-safe reference palette), never re-assigned
COL = {"KZ": "#2a78d6", "UZ": "#eb6834", "KG": "#1baf7a", "TJ": "#eda100", "TM": "#e87ba4", "REGION": "#444444"}
NAME = A.NAMES | {"REGION": "Region (unique works)"}
GREY = "#8a8a8a"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e3e3e3", "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "figure.dpi": 100})
YEARS = list(range(2010, 2026))


def save(fig, name):
    for ext in ("png", "tif"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"} if ext == "tif" else {})
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- Figure 1: trajectories (linear + log with NB fits)
def fig1():
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4))
    cy = R["country_year_full"]
    for cc in ["KZ", "UZ", "KG", "TJ"]:
        y = [cy[cc].get(str(t), 0) for t in YEARS]
        a.plot(YEARS, y, color=COL[cc], lw=2, label=NAME[cc])
        a.annotate(NAME[cc], (YEARS[-1], y[-1]), xytext=(4, 0), textcoords="offset points", color=COL[cc], va="center", fontsize=8)
    a.set_xlim(2010, 2027.5); a.set_ylabel("Works per year (full counting)"); a.set_title("(a) Annual output, 2010–2025", loc="left", fontsize=9)
    a.set_xticks(range(2010, 2026, 3))
    for cc in ["KZ", "UZ", "KG", "REGION"]:
        y = [cy[cc].get(str(t), 0) for t in YEARS] if cc != "REGION" else [R["by_year"].get(str(t), 0) for t in YEARS]
        yy = [v if v > 0 else np.nan for v in y]
        b.plot(YEARS, yy, "o", ms=3.5, color=COL[cc], label=NAME[cc])
        g = R["growth"]["full"][cc]["nb2"]
        n0 = np.exp(np.log(np.nanmean([v for v in y if v > 0])))  # anchor via fitted intercept below
        # refit intercept for display: use OLS intercept implied by NB rate through geometric mean
        t = np.array(YEARS) - 2010
        m = np.array(y) > 0
        c = np.mean(np.log(np.array(y)[m]) - g["r"] * t[m])
        b.plot(YEARS, np.exp(c + g["r"] * t), "-", lw=1.5, color=COL[cc])
        b.annotate(f"{NAME[cc].split(' (')[0]}: {100*g['r']:.0f}%/yr", (2025.2, np.exp(c + g["r"] * 15)), fontsize=8, color=COL[cc], va="center")
    b.set_yscale("log"); b.set_xlim(2010, 2029); b.set_xticks(range(2010, 2026, 3))
    b.set_ylabel("Works per year (log scale)"); b.set_title("(b) Negative-binomial exponential fits", loc="left", fontsize=9)
    fig.tight_layout(); save(fig, "fig1_trajectories")


# ---------------------------------------------------------------- Figure 2: snapshot drift
def fig2():
    S = R["snapshots"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [1.5, 1]})
    styles = {"may": ("30 May 2026", ":", GREY), "sept": ("3 Sept 2026", "--", "#555555"), "nov": ("12 Nov 2026", "-", "#111111")}
    for k, (lab, ls, col) in styles.items():
        y = [S[k]["region"].get(str(t), 0) for t in range(2010, 2027)]
        a.plot(range(2010, 2027), y, ls, color=col, lw=2, label=lab)
    a.axvspan(2025.5, 2026.5, color="#f0f0f0", zorder=0); a.text(2026, 50, "2026\npartial", ha="center", fontsize=7, color=GREY)
    a.set_yscale("log"); a.set_ylabel("Unique works per year (log scale)"); a.legend(loc="upper left")
    a.set_title("(a) Same query, three snapshots", loc="left", fontsize=9); a.set_xticks(range(2010, 2027, 4))
    ccs = ["UZ", "KZ", "KG", "TJ", "TM"]
    x = np.arange(len(ccs)); w = 0.26
    for i, (k, (lab, ls, col)) in enumerate(styles.items()):
        vals = [sum((S[k].get(cc) or {}).values()) for cc in ccs]
        b.bar(x + (i - 1) * w, vals, w, color=col if k != "may" else "#c8c8c8", label=lab, edgecolor="white", linewidth=1)
        for xi, v in zip(x + (i - 1) * w, vals):
            b.text(xi, v * 1.15, f"{v:,}", ha="center", fontsize=6.5, rotation=90, color="#333333")
    b.set_yscale("log"); b.set_xticks(x); b.set_xticklabels([NAME[c] for c in ccs], rotation=20, ha="right")
    b.set_ylabel("Works 2010–2026 (log scale)"); b.set_title("(b) Country totals by snapshot", loc="left", fontsize=9)
    b.set_ylim(5, 20000)
    fig.tight_layout(); save(fig, "fig2_snapshot_drift")


# ---------------------------------------------------------------- Figure 3: publication channel by year
def fig3():
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    yrs = list(range(2016, 2027))
    formal = [R["by_year_tier"]["formal publication"].get(str(t), 0) for t in yrs]
    zen = [R["zenodo"]["by_year"].get(str(t), 0) for t in yrs]
    repo_other = [R["by_year_tier"]["repository/preprint"].get(str(t), 0) - z for t, z in zip(yrs, zen)]
    ax.bar(yrs, formal, color="#2a78d6", label="Formal publications (journal, conference, book)", edgecolor="white")
    ax.bar(yrs, repo_other, bottom=formal, color="#1baf7a", label="Preprints and other repositories", edgecolor="white")
    ax.bar(yrs, zen, bottom=np.array(formal) + np.array(repo_other), color="#eda100", label="Zenodo deposits", edgecolor="white")
    for t, f, ro, z in zip(yrs, formal, repo_other, zen):
        tot = f + ro + z
        ax.text(t, tot + 30, f"{100*(ro+z)/tot:.0f}%", ha="center", fontsize=7, color="#333333")
    ax.set_xticks(yrs); ax.set_xticklabels([str(t) if t < 2026 else "2026*" for t in yrs])
    ax.set_ylabel("Works per year"); ax.legend(loc="upper left", fontsize=8)
    ax.set_title("Publication channel by year (labels: repository share)", loc="left", fontsize=9)
    fig.tight_layout(); save(fig, "fig3_channel_by_year")


# ---------------------------------------------------------------- Figure 4: top-8 domestic institutions, share of national works
def fig4():
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.2))
    for ax, cc in zip(axes.flat, ["UZ", "KZ", "KG", "TJ"]):
        rows = R["institutions"][cc]["top_work_share"][:8][::-1]
        names = [n if len(n) < 48 else n[:45] + "…" for n, _, _ in rows]
        shares = [100 * s for _, _, s in rows]
        ax.barh(names, shares, color=COL[cc], height=0.65)
        for i, (n, k, s) in enumerate(rows):
            ax.text(100 * s + 0.4, i, f"{k:,}", va="center", fontsize=7, color="#333333")
        ax.set_xlim(0, 30); ax.set_xlabel("Share of national works (%)")
        ax.set_title(f"{NAME[cc]} (n = {R['institutions'][cc]['national_works']:,} works)", loc="left", fontsize=9)
        ax.tick_params(axis="y", labelsize=7.5)
    fig.tight_layout(); save(fig, "fig4_institutions")


# ---------------------------------------------------------------- Figure 5: top-20 topics with activity index
def fig5():
    rows = R["topics_top25"][:20][::-1]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [2.2, 1]}, sharey=True)
    sfcol = {"Artificial Intelligence": "#2a78d6", "Computer Vision and Pattern Recognition": "#eb6834",
             "Computational Theory and Mathematics": "#1baf7a", "Software": "#eda100"}
    labels = [f"{r[1]}" for r in rows]
    a.barh(labels, [r[4] for r in rows], color=[sfcol[r[2]] for r in rows], height=0.65)
    for i, r in enumerate(rows):
        a.text(r[4] + 0.1, i, f"{r[3]:,}", va="center", fontsize=7)
    a.set_xlabel("Share of corpus (%)"); a.set_title("(a) Twenty most frequent primary topics", loc="left", fontsize=9)
    a.legend(handles=[Patch(color=c, label=s) for s, c in sfcol.items()], loc="lower right", fontsize=7, title="Subfield", title_fontsize=7)
    a.tick_params(axis="y", labelsize=7.5)
    ai = [r[7] for r in rows]
    b.barh(labels, ai, color=["#555555" if v >= 1 else "#bbbbbb" for v in ai], height=0.65)
    b.axvline(1, color="#111111", lw=1); b.set_xlabel("Activity index (share ÷ global share)")
    b.set_title("(b) Specialization vs. world", loc="left", fontsize=9); b.set_xlim(0, 5)
    for i, v in enumerate(ai):
        b.text(v + 0.05, i, f"{v:.1f}", va="center", fontsize=7)
    fig.tight_layout(); save(fig, "fig5_topics")


# ---------------------------------------------------------------- Figure 6: FWCI distributions
def fig6():
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"width_ratios": [1.4, 1]})
    ccs = ["KZ", "UZ", "KG", "TJ"]
    data = [[r["fwci"] for r in W if cc in r["ca"] and r["fwci"] is not None] for cc in ccs]
    bp = a.boxplot(data, labels=[f"{NAME[c]}\n(n = {len(d):,})" for c, d in zip(ccs, data)], showfliers=False, widths=0.55,
                   patch_artist=True, medianprops={"color": "#111111"})
    for p, cc in zip(bp["boxes"], ccs):
        p.set_facecolor(COL[cc]); p.set_alpha(0.75)
    a.axhline(1, color="#111111", lw=1, ls="--"); a.text(4.45, 1.05, "world average", fontsize=7, ha="right")
    a.set_ylabel("Field-weighted citation impact (boxes: IQR)"); a.set_ylim(-0.05, 2.0)
    a.set_title("(a) FWCI, full corpus (outliers not drawn)", loc="left", fontsize=9)
    # (b) share of works with FWCI >= 1 and in top 10 %, with Wilson CIs
    x = np.arange(len(ccs)); w = 0.36
    for j, (key, lab, col) in enumerate([("share_ge1", "FWCI ≥ 1", "#555555"), ("share_top10", "Top 10 % of field", "#2a78d6")]):
        vals, lo, hi = [], [], []
        for cc in ccs:
            f = R["fwci"][cc]
            n = f["n_fwci"] if key == "share_ge1" else f["n"]
            k = round(f[key] * n)
            p, l, h = A.wilson(k, n)
            vals.append(100 * p); lo.append(100 * (p - l)); hi.append(100 * (h - p))
        b.bar(x + (j - 0.5) * w, vals, w, yerr=[lo, hi], capsize=2, color=col, label=lab, edgecolor="white")
    b.set_xticks(x); b.set_xticklabels([NAME[c] for c in ccs], rotation=15, ha="right"); b.set_ylabel("Share of works (%)")
    b.legend(fontsize=8); b.set_title("(b) Shares with 95 % Wilson intervals", loc="left", fontsize=9)
    fig.tight_layout(); save(fig, "fig6_fwci")


# ---------------------------------------------------------------- Figure 7: open access by country
def fig7():
    order = ["diamond", "gold", "hybrid", "bronze", "green", "closed"]
    cols = {"diamond": "#1c5cab", "gold": "#2a78d6", "hybrid": "#6da7ec", "bronze": "#b7d3f6", "green": "#1baf7a", "closed": "#bbbbbb"}
    rows = [("Region", R["oa"])] + [(NAME[cc], R["oa_by_country"][cc]) for cc in ["KZ", "UZ", "KG"]]
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    for i, (lab, d) in enumerate(rows[::-1]):
        tot = sum(d.values()); left = 0
        for k in order:
            v = 100 * d.get(k, 0) / tot
            ax.barh(lab, v, left=left, color=cols[k], edgecolor="white", linewidth=1.2, label=k if i == 0 else None)
            if v > 6:
                ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=7, color="white" if k in ("diamond", "gold", "green") else "#222222")
            left += v
    ax.set_xlim(0, 100); ax.set_xlabel("Share of works (%), OpenAlex open-access status at snapshot date")
    ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, 1.18), fontsize=8)
    fig.tight_layout(); save(fig, "fig7_open_access")


# ---------------------------------------------------------------- Figure 8: collaboration partners and groups


def fig8():
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 5), gridspec_kw={"width_ratios": [1.3, 1]})
    gcol = {"post-Soviet (non-OECD)": "#eb6834", "OECD": "#2a78d6", "Asia & Middle East (non-OECD)": "#1baf7a", "rest of world": "#bbbbbb"}
    CN = {"IN": "India", "RU": "Russia", "CN": "China", "US": "United States", "UA": "Ukraine", "KR": "South Korea", "TR": "Türkiye",
          "PL": "Poland", "IQ": "Iraq", "MY": "Malaysia", "SA": "Saudi Arabia", "GB": "United Kingdom", "PK": "Pakistan",
          "AE": "United Arab Emirates", "JP": "Japan", "JO": "Jordan", "IT": "Italy", "DE": "Germany", "ID": "Indonesia", "IR": "Iran"}
    def grp(c):
        if c in A.POST_SOVIET_NON_OECD: return "post-Soviet (non-OECD)"
        if c in A.OECD: return "OECD"
        if c in A.ASIA_NON_OECD: return "Asia & Middle East (non-OECD)"
        return "rest of world"
    top = R["collab"]["partners_top25"][:20][::-1]
    a.barh([CN.get(c, c) for c, _ in top], [n for _, n in top], color=[gcol[grp(c)] for c, _ in top], height=0.65)
    for i, (c, n) in enumerate(top):
        a.text(n + 5, i, f"{n}", va="center", fontsize=7)
    a.set_xlabel("Co-authored works (a work counts once per partner country)")
    a.set_title("(a) Twenty largest partner countries", loc="left", fontsize=9)
    a.legend(handles=[Patch(color=c, label=g) for g, c in gcol.items()], loc="lower right", fontsize=7)
    a.tick_params(axis="y", labelsize=8)
    ccs = ["KZ", "UZ", "KG", "TJ"]
    groups = ["post-Soviet (non-OECD)", "OECD", "Asia & Middle East (non-OECD)"]
    x = np.arange(len(ccs)); w = 0.26
    for j, g in enumerate(groups):
        vals = [100 * R["collab_by_country"][cc]["any_group"].get(g, 0) / R["collab_by_country"][cc]["n"] for cc in ccs]
        b.bar(x + (j - 1) * w, vals, w, color=gcol[g], label=g, edgecolor="white")
        for xi, v in zip(x + (j - 1) * w, vals):
            b.text(xi, v + 0.4, f"{v:.0f}", ha="center", fontsize=7)
    b.set_xticks(x); b.set_xticklabels([NAME[c] for c in ccs], rotation=15, ha="right")
    b.set_ylabel("Share of national works with ≥1 co-author in group (%)")
    b.set_ylim(0, 36); b.set_title("(b) Partner groups by country (non-exclusive)", loc="left", fontsize=9); b.legend(fontsize=7, loc="upper left")
    fig.tight_layout(); save(fig, "fig8_collaboration")


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8):
        f()
