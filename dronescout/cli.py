"""Command-line interface: ``python -m dronescout {plan,run,study}``."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Config
from .field import FieldMap
from .planner import plan_survey


def _cfg(a) -> Config:
    return Config(alt=a.alt, fwd=a.fwd, side=a.side, dir=a.dir, wind=a.wind, wdir=a.wdir,
                  gust=a.gust, gnss=a.gnss, seed=a.seed)


def main(argv=None):
    p = argparse.ArgumentParser(prog="dronescout", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--alt", type=float, default=30); sp.add_argument("--fwd", type=float, default=80)
        sp.add_argument("--side", type=float, default=70); sp.add_argument("--dir", type=int, default=0,
                                                                         choices=(0, 1), help="0=long side, 1=short side")
        sp.add_argument("--wind", type=float, default=3); sp.add_argument("--wdir", type=float, default=270)
        sp.add_argument("--gust", type=float, default=0.8); sp.add_argument("--gnss", type=float, default=0.75)
        sp.add_argument("--seed", type=int, default=7)

    sp = sub.add_parser("plan", help="print the survey plan and estimates"); common(sp)
    sp = sub.add_parser("run", help="fly one simulated mission"); common(sp)
    sp.add_argument("--out", default="out", help="output directory")
    sp.add_argument("--plots", action="store_true", help="write PNG figures")
    sp.add_argument("--swap", action="store_true", help="swap battery and resume after low-battery return")
    sp = sub.add_parser("study", help="run the 24-setting x 5-seed grid + wind study")
    sp.add_argument("--out", default="results")
    a = p.parse_args(argv)

    fmap = FieldMap.synthetic_potato()
    if a.cmd == "plan":
        pl = plan_survey(_cfg(a), fmap.width, fmap.height)
        print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                          for k, v in vars(pl).items() if k not in ("waypoints", "lane_xs")}, indent=2))
    elif a.cmd == "run":
        from .sim import simulate
        r = simulate(_cfg(a), fmap, swap_and_resume=a.swap)
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / "captures.csv").write_text(r.captures_csv())
        (out / "summary.json").write_text(json.dumps(r.summary(), indent=2))
        print(json.dumps(r.summary(), indent=2))
        if a.plots:
            from . import plots
            plots.mission_map(r, fmap, out / "mission-map.png")
            plots.telemetry(r, out / "telemetry.png")
            plots.coverage_growth(r, out / "coverage.png")
        print(f"wrote {out}/")
    else:
        from .benchmark import run_study, select_best
        from . import plots
        grid, summ, wind, meta = run_study(a.out, fmap)
        plots.runtime_tradeoff(summ, Path(a.out) / "runtime-tradeoff.png")
        plots.heatmap(summ, Path(a.out) / "duration-heatmap.png")
        for lab, k in (("GSD <= 2.5 cm/px", "best_gsd_2_5"), ("GSD <= 2.0 cm/px", "best_gsd_2_0")):
            b = meta[k]
            print(lab, "->", "none" if not b else
                  f"{b['alt']} m, {b['fwd']}% fwd, dir {b['dir']}: {b['mean_s']:.2f} +/- {b['sd_s']:.2f} s")
        print(f"{meta['runs']} runs in {meta['seconds']} s; results in {a.out}/")


if __name__ == "__main__":
    main()
