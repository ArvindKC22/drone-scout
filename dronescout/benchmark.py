"""Parameter-grid and wind-sensitivity study (report Chapters 10, 13, 15)."""
from __future__ import annotations

import csv
import json
import statistics as st
import time
from itertools import product
from pathlib import Path

from .config import Config
from .field import FieldMap
from .sim import simulate

ALTS = (20, 30, 40, 60)
FWDS = (70, 80, 90)
DIRS = (0, 1)
SEEDS = (1, 7, 21, 42, 99)
WINDS = (0, 3, 6, 10)


def run_grid(fmap: FieldMap, base: Config | None = None, seeds=SEEDS, progress=None):
    base = (base or Config()).with_(side=70.0, wind=3.0)
    rows = []
    for alt, fwd, d, seed in product(ALTS, FWDS, DIRS, seeds):
        r = simulate(base.with_(alt=alt, fwd=fwd, dir=d, seed=seed), fmap, record=False)
        rows.append(dict(alt=alt, fwd=fwd, dir="L" if d == 0 else "S", seed=seed,
                         completed=int(r.completed), duration_s=r.duration_s,
                         captures=len(r.captures), coverage_pct=r.coverage_pct,
                         energy_wh=r.energy_wh, rms_track_m=r.rms_track_m, gsd_cm=r.plan.gsd_cm))
        if progress:
            progress(len(rows))
    return rows


def run_wind(fmap: FieldMap, base: Config | None = None, seeds=SEEDS):
    base = base or Config()
    rows = []
    for w, seed in product(WINDS, seeds):
        r = simulate(base.with_(wind=w, seed=seed), fmap, record=False)
        rows.append(dict(wind=w, seed=seed, completed=int(r.completed), duration_s=r.duration_s,
                         energy_wh=r.energy_wh, rms_track_m=r.rms_track_m))
    return rows


def summarize(rows):
    groups = {}
    for r in rows:
        groups.setdefault((r["alt"], r["fwd"], r["dir"]), []).append(r)
    out = []
    for (alt, fwd, d), g in groups.items():
        dur = [x["duration_s"] for x in g]
        out.append(dict(alt=alt, fwd=fwd, dir=d, n=len(g),
                        completed_all=all(x["completed"] for x in g),
                        mean_s=st.mean(dur), sd_s=st.stdev(dur) if len(dur) > 1 else 0.0,
                        min_cover_pct=min(x["coverage_pct"] for x in g),
                        mean_wh=st.mean(x["energy_wh"] for x in g),
                        mean_captures=st.mean(x["captures"] for x in g),
                        gsd_cm=g[0]["gsd_cm"]))
    return sorted(out, key=lambda s: s["mean_s"])


def select_best(summary, gsd_ceiling_cm: float, min_cover: float = 99.0):
    ok = [s for s in summary if s["completed_all"] and s["min_cover_pct"] >= min_cover
          and s["gsd_cm"] <= gsd_ceiling_cm]
    return min(ok, key=lambda s: s["mean_s"]) if ok else None


def summarize_wind(rows):
    out = []
    for w in sorted({r["wind"] for r in rows}):
        g = [r for r in rows if r["wind"] == w]
        out.append(dict(wind=w, mean_s=st.mean(r["duration_s"] for r in g),
                        mean_wh=st.mean(r["energy_wh"] for r in g),
                        mean_rms=st.mean(r["rms_track_m"] for r in g),
                        completed=f"{sum(r['completed'] for r in g)}/{len(g)}"))
    return out


def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


def run_study(out_dir="results", fmap: FieldMap | None = None):
    out = Path(out_dir)
    fmap = fmap or FieldMap.synthetic_potato()
    t0 = time.time()
    grid = run_grid(fmap)
    wind = run_wind(fmap)
    summ = summarize(grid)
    best25 = select_best(summ, 2.5)
    best20 = select_best(summ, 2.0)
    write_csv(out / "benchmark.csv", grid)
    write_csv(out / "settings-summary.csv", summ)
    write_csv(out / "wind-sensitivity.csv", wind)
    write_csv(out / "wind-summary.csv", summarize_wind(wind))
    meta = dict(runs=len(grid) + len(wind), seconds=round(time.time() - t0, 1),
                map=fmap.name, best_gsd_2_5=best25, best_gsd_2_0=best20)
    (out / "study.json").write_text(json.dumps(meta, indent=2, default=str))
    return grid, summ, wind, meta
