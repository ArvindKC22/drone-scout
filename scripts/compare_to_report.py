"""Compare this repo's re-implementation with Appendix C of the technical report.

    python scripts/compare_to_report.py      # writes docs/REPRODUCTION.md and assets/sim-vs-report.png
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dronescout import Config, FieldMap, simulate                      # noqa: E402
from dronescout.benchmark import run_grid, summarize, select_best     # noqa: E402

# (alt m, forward overlap %, direction, mean s, SD s, min coverage %, mean Wh)  -- report Appendix C
REPORT = """40 70 L 67.16 4.06 100.000 3.814
60 70 L 71.14 3.68 100.000 4.143
40 80 L 79.72 9.15 100.000 4.438
60 80 L 80.06 6.77 100.000 4.573
60 70 S 90.84 1.90 96.647 5.168
30 70 L 96.96 8.32 96.618 5.217
60 80 S 98.24 5.09 97.922 5.507
60 90 L 103.64 12.21 100.000 5.761
40 70 S 111.00 4.20 97.863 6.112
40 90 L 113.46 16.11 100.000 6.152
30 80 L 125.42 15.11 99.343 6.642
60 90 S 129.84 9.86 98.598 7.092
40 80 S 132.92 6.51 98.500 7.181
30 70 S 163.50 8.18 98.412 8.745
40 90 S 196.18 21.69 98.824 10.364
30 90 L 214.48 42.38 98.804 11.147
30 80 S 215.26 13.30 97.892 11.318
20 70 L 217.68 15.88 99.147 11.336
20 80 L 282.70 39.00 99.020 14.602
20 70 S 319.14 19.99 98.088 16.555
30 90 S 375.74 58.47 98.824 19.431
20 80 S 429.50 24.86 98.765 22.099
20 90 L 580.34 52.29 99.402 29.684
20 90 S 912.68 117.83 98.902 46.665"""
rep = {}
for ln in REPORT.splitlines():
    a, f, d, m, sd, mc, wh = ln.split()
    rep[(int(a), int(f), d)] = dict(mean=float(m), sd=float(sd), cov=float(mc), wh=float(wh))

fmap = FieldMap.synthetic_potato()
ours = {(s["alt"], s["fwd"], s["dir"] if isinstance(s["dir"], str) else "LS"[s["dir"]]): s
        for s in summarize(run_grid(fmap))}
keys = list(rep)
rm = np.array([rep[k]["mean"] for k in keys]); om = np.array([ours[k]["mean_s"] for k in keys])
rw = np.array([rep[k]["wh"] for k in keys]); ow = np.array([ours[k]["mean_wh"] for k in keys])


def spearman(a, b):
    ra, rb = a.argsort().argsort(), b.argsort().argsort()
    return float(np.corrcoef(ra, rb)[0, 1])


base = simulate(Config(seed=7), fmap)
fast = simulate(Config(seed=7, alt=40, fwd=70), fmap)
best25 = select_best(list(ours.values()), 2.5); best20 = select_best(list(ours.values()), 2.0)

L = []
L += ["# Reproduction check against the technical report", "",
      "This repository is an **independent re-implementation** of the equations published in the report.",
      "The report's frozen JavaScript model and its potato canopy raster are not redistributed, so the",
      "Python package flies a *synthetic* map of the same size (29.846 × 84.618 m) with its own PRNG.",
      "Exact agreement on stochastic runs is therefore neither expected nor claimed. What can be checked is",
      "(a) the deterministic planner, which must match exactly, and (b) whether the stochastic results",
      "reproduce the report's trends.", "",
      "Regenerate with `python scripts/compare_to_report.py`.", "",
      "## 1. Deterministic planner (exact)", "",
      "| Quantity | Report | This repo |", "|---|---|---|"]
from dronescout import plan_survey                                         # noqa: E402
p = plan_survey(Config(), fmap.width, fmap.height)
pf = plan_survey(Config(alt=40, fwd=70), fmap.width, fmap.height)
L += [f"| Baseline lanes / photos | 2 / 42 | {p.n_lanes} / {p.est_photos} |",
      f"| Baseline survey speed (Eq. 4) | 1.965 m/s | {p.survey_speed:.3f} m/s |",
      f"| Baseline path length | 215 m | {p.path_length:.0f} m |",
      f"| Baseline time estimate (Eq. 17) | 134.975 s | {p.est_time:.3f} s |",
      f"| 40 m / 70 % lanes, photos, speed | 1, 11, 3.93 m/s | {pf.n_lanes}, {pf.est_photos}, {pf.survey_speed:.2f} m/s |",
      f"| Pack energy (Eq. 8) | 89.224 Wh | {Config().energy_wh:.3f} Wh |", "",
      "## 2. Seed-7 baseline mission (stochastic)", "",
      "| Quantity | Report | This repo |", "|---|---|---|",
      f"| Duration | 145.0 s | {base.duration_s:.1f} s |",
      f"| Captures | 40 | {len(base.captures)} |",
      f"| Grid coverage | 100 % | {base.coverage_pct:.1f} % |",
      f"| Energy | 7.605 Wh | {base.energy_wh:.3f} Wh |",
      f"| Battery remaining | 91.48 % | {base.battery_pct:.2f} % |",
      f"| Cross-track RMS | 0.810 m | {base.rms_track_m:.3f} m |",
      f"| 40 m / 70 % seed 7: duration, captures | 72.6 s, 11 | {fast.duration_s:.1f} s, {len(fast.captures)} |", "",
      "## 3. 24-setting × 5-seed grid", "",
      f"- Spearman rank correlation of mean duration: **{spearman(rm, om):.3f}**",
      f"- Spearman rank correlation of mean energy: **{spearman(rw, ow):.3f}**",
      f"- Mean absolute difference in mean duration: **{np.mean(np.abs(om - rm) / rm) * 100:.1f} %**",
      f"- Fastest setting meeting GSD ≤ 2.5 cm/px and ≥ 99 % coverage in every seed: report 40 m / 70 % / long side "
      f"(67.16 s); here {best25['alt']} m / {best25['fwd']} % / {'long' if best25['dir'] in ('L', 0) else 'short'} side ({best25['mean_s']:.2f} s)",
      f"- Fastest setting for GSD ≤ 2.0 cm/px: report 30 m / 80 % / long side (125.42 s); here {best20['alt']} m / {best20['fwd']} % / "
      f"{'long' if best20['dir'] in ('L', 0) else 'short'} side ({best20['mean_s']:.2f} s)", "",
      "The GSD ≤ 2.0 cm/px choice is the least stable result: it hinges on which settings clear the 99 % coverage",
      "bar in *every* seed, and that depends on edge-strip misses that differ between the real and synthetic",
      "canopy masks and between PRNG streams. Treat it as sensitive to modelling details, as the report itself warns.", "",
      "| Alt | Fwd | Dir | Report mean s | Repo mean s | Report Wh | Repo Wh | Report min cov % | Repo min cov % |", "|--:|--:|:-:|--:|--:|--:|--:|--:|--:|"]
for k in keys:
    o = ours[k]
    L.append(f"| {k[0]} | {k[1]} | {k[2]} | {rep[k]['mean']:.2f} | {o['mean_s']:.2f} | {rep[k]['wh']:.2f} | "
             f"{o['mean_wh']:.2f} | {rep[k]['cov']:.2f} | {o['min_cover_pct']:.2f} |")
(ROOT / "docs" / "REPRODUCTION.md").write_text("\n".join(L) + "\n")

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt                                            # noqa: E402
fig, ax = plt.subplots(figsize=(4.8, 4.4), dpi=130)
ax.scatter(rm, om, c="#dd6b20", s=28, zorder=3)
lim = [10, 1100]; ax.plot(lim, lim, color="#718096", lw=1, ls="--", label="y = x")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Report mean duration (s)"); ax.set_ylabel("This repo mean duration (s)")
ax.set_title(f"24 settings · Spearman ρ = {spearman(rm, om):.3f}", fontsize=9); ax.legend(); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(ROOT / "assets" / "sim-vs-report.png")
print("rho", spearman(rm, om), "mad%", np.mean(np.abs(om - rm) / rm) * 100)
