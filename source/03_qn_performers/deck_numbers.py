#!/usr/bin/env python
"""deck_numbers.py - every number on the QN performers deck, read from the pipeline's data/manifest.js.

    python deck_numbers.py <path to 0_qn_performers\\data\\manifest.js> [--out numbers.json]

Lists: the R1 lists (top 15 / bottom 15 by |bias|); R2 is near-identical (see slide 3).
No numbers are typed into the deck by hand; this file is their source.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
from collections import Counter


def load(path):
    s = open(path, encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def hyper_p0(N, K, n):
    """P(no item of the K-group in a random draw of n from N)"""
    return math.comb(N - K, n) / math.comb(N, n)


def hyper_tail(N, K, n, k):
    """P(at least k of the K-group in a random draw of n from N)"""
    return sum(math.comb(K, j) * math.comb(N - K, n - j) for j in range(k, min(K, n) + 1)) / math.comb(N, n)


def med(v):
    v = [x for x in v if x is not None]
    return st.median(v) if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", default="numbers.json")
    a = ap.parse_args()
    Q = load(a.manifest)
    out = {"n": Q["meta"]["n"], "auc_budget": Q["meta"]["auc_budget"], "made": Q["meta"]["made"], "regions": {}}
    for reg, R in Q["regions"].items():
        runs, info = R["runs"], R["info"]
        top = [runs[e["run"]] for e in R["lists"]["R1_top"]]
        bot = [runs[e["run"]] for e in R["lists"]["R1_bottom"]]
        n = len(top)
        o = {"info": info, "rank_spearman": R["rank_spearman"], "flag_rule": R["flag_rule"]}
        o["overlap"] = {end: sum(e["in_both"] for e in R["lists"][f"R1_{end}"]) for end in ("top", "bottom")}
        o["composition"] = {end: dict(Counter(r["group"] for r in L)) for end, L in (("top", top), ("bottom", bot))}
        N, K = info["n_gated"], info["gated_by_group"].get("DisCo alone", 0)
        kb = o["composition"]["bottom"].get("DisCo alone", 0)
        o["null"] = {"N": N, "K": K, "expected_in_15": n * K / N, "p_none_in_top": hyper_p0(N, K, n),
                     "bottom_k": kb, "p_at_least_bottom_k": hyper_tail(N, K, n, kb)}
        o["blocks"] = {end: dict(Counter(r["block"] for r in L)) for end, L in (("top", top), ("bottom", bot))}
        o["flags"] = {end: {"median": med([r["health"]["counts"]["FLAG"] for r in L]),
                            "min": min(r["health"]["counts"]["FLAG"] for r in L),
                            "max": max(r["health"]["counts"]["FLAG"] for r in L)} for end, L in (("top", top), ("bottom", bot))}
        rows = Counter(), Counter()
        for i, L in enumerate((top, bot)):
            for r in L:
                for row in r["health"]["rows"]:
                    if row[4] == "FLAG":
                        rows[i][row[1]] += 1
        o["flag_rows"] = sorted([[k, rows[0][k], rows[1][k]] for k in set(rows[0]) | set(rows[1])],
                                key=lambda x: (x[1] - x[2], x[0]))
        sc = {}
        for k in ("pnc_trained", "x_null_trained", "pnc_tail", "spec_abs_z11", "logit_span1", "logit_span2", "sat2",
                  "pull_width", "roughness"):
            sc[k] = [med([r["health"]["scalars"].get(k) for r in L]) for L in (top, bot)]
        for k in ("auc1", "auc2", "auc1_drop", "auc2_drop", "abs_bias", "abs_pull"):
            sc[k] = [med([r["rank_metrics"][k] for r in L]) for L in (top, bot)]
        for net in ("NN1", "NN2"):
            for k in ("d_hull", "d_hull_z", "chi2_ratio", "chi2_ratio_null_p95", "rho", "spike", "sat_bkg",
                      "modes_bkg", "bce_calibration", "bce_refinement", "bce_ece"):
                sc[f"{net}_{k}"] = [med([r["hood"]["nets"][net].get(k) for r in L]) for L in (top, bot)]
        o["medians_top_bottom"] = sc
        allr = list(runs.values())
        o["hood_all"] = {
            "n": len(allr),
            "hull_z_median": {net: med([r["hood"]["nets"][net]["d_hull_z"] for r in allr]) for net in ("NN1", "NN2")},
            "hull_z_max": {net: max(r["hood"]["nets"][net]["d_hull_z"] for r in allr) for net in ("NN1", "NN2")},
            "fails": {net: dict(Counter(f for r in allr for f in r["hood"]["nets"][net]["fails"])) for net in ("NN1", "NN2")},
            "chi2_median": {net: med([r["hood"]["nets"][net]["chi2_ratio"] for r in allr]) for net in ("NN1", "NN2")},
            "chi2_null_p95_median": {net: med([r["hood"]["nets"][net]["chi2_ratio_null_p95"] for r in allr]) for net in ("NN1", "NN2")},
            "rho_median": {net: med([r["hood"]["nets"][net]["rho"] for r in allr]) for net in ("NN1", "NN2")},
            "chi2_pass": {net: sum(1 for r in allr if r["hood"]["nets"][net]["chi2_ratio"] <= max(r["hood"]["nets"][net]["chi2_ratio_null_p95"] or 0, 2.0)) for net in ("NN1", "NN2")},
            "table": {e: {h: len(R["table"][e][h]) for h in ("healthy", "unhealthy")} for e in ("expected", "unexpected")},
        }
        fl = [r["health"]["counts"]["FLAG"] for r in allr]

        def sp(v):
            def rk(x):
                o_ = sorted(range(len(x)), key=lambda i: x[i]); r_ = [0] * len(x)
                for j, i in enumerate(o_):
                    r_[i] = j
                return r_
            a_, b_ = rk(v), rk(fl); m = (len(v) - 1) / 2
            num = sum((x - m) * (y - m) for x, y in zip(a_, b_))
            den = math.sqrt(sum((x - m) ** 2 for x in a_) * sum((y - m) ** 2 for y in b_))
            return num / den
        o["spearman_vs_flags"] = {f"{net}_{k}": sp([r["hood"]["nets"][net][k] for r in allr])
                                   for net in ("NN1", "NN2") for k in ("bce_refinement", "bce_ece", "d_hull")}
        o["lists"] = {end: [{"rank": i + 1, "run": r["run"], "group": r["group"], "alpha": r["alpha"], "beta": r["beta"],
                             "block": r["block"], "seed": r["seed"], "bias": r["rank_metrics"]["bias"],
                             "pull": r["rank_metrics"]["pull"], "auc1": r["rank_metrics"]["auc1"],
                             "auc2": r["rank_metrics"]["auc2"], "flags": r["health"]["counts"]["FLAG"],
                             "span2": r["health"]["scalars"].get("logit_span2"), "sat2": r["hood"]["nets"]["NN2"]["sat_bkg"],
                             "partner": r["partner"], "partner_metrics": r.get("partner_metrics")}
                            for i, r in enumerate(L)] for end, L in (("top", top), ("bottom", bot))}
        out["regions"][reg] = o
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
