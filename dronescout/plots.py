"""Matplotlib figures for missions and studies."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PAL = dict(blue="#2b6cb0", green="#2f855a", orange="#dd6b20", red="#c53030", grey="#4a5568")
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .25, "figure.dpi": 130})


def mission_map(res, fmap, path):
    fig, ax = plt.subplots(figsize=(4.6, 8.6))
    ax.imshow(fmap.canopy, extent=(0, fmap.width, fmap.height, 0), cmap="YlGn", vmin=0, vmax=100,
              alpha=.9)
    for c in res.captures:
        ax.add_patch(Rectangle((c.x_m - c.footprint_w_m / 2, c.y_m - c.footprint_l_m / 2),
                               c.footprint_w_m, c.footprint_l_m, fill=False, lw=.6,
                               ec=PAL["grey"], alpha=.55))
    ax.plot(res.path[:, 0], res.path[:, 1], color=PAL["blue"], lw=1.4, label="flown path")
    ax.scatter([c.x_m for c in res.captures], [c.y_m for c in res.captures], s=9,
               color=PAL["orange"], zorder=3, label=f"{len(res.captures)} captures")
    ax.scatter([res.cfg.home_x], [res.cfg.home_y], marker="s", color=PAL["red"], zorder=4, label="home")
    ax.set_xlim(-8, fmap.width + 8); ax.set_ylim(fmap.height + 10, -10); ax.set_aspect("equal")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_title(f"{res.cfg.alt:.0f} m · {res.cfg.fwd:.0f}% fwd overlap · seed {res.cfg.seed}\n"
                 f"{res.duration_s:.0f} s · coverage {res.coverage_pct:.1f}% · {res.energy_wh:.2f} Wh",
                 fontsize=9)
    ax.legend(loc="lower right", fontsize=7, framealpha=.9)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def telemetry(res, path):
    T = res.telemetry
    fig, axs = plt.subplots(2, 2, figsize=(8, 5.2))
    spec = [("alt", "Altitude (m)", PAL["blue"]), ("gs", "Ground speed (m/s)", PAL["green"]),
            ("power", "Electrical power (W)", PAL["orange"]), ("soc", "Battery remaining (%)", PAL["green"])]
    for ax, (k, lab, col) in zip(axs.ravel(), spec):
        ax.plot(T["t"], T[k], color=col, lw=1.2)
        ax.set_ylabel(lab); ax.set_xlabel("Simulation time (s)")
    fig.suptitle(f"Flight telemetry · {res.cfg.alt:.0f} m · seed {res.cfg.seed}", fontsize=10)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def coverage_growth(res, path):
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot([c.t_s for c in res.captures], [c.coverage_pct for c in res.captures],
            color=PAL["green"], marker="o", ms=3)
    ax.axhline(99, color=PAL["red"], ls="--", lw=1, label="99% criterion")
    ax.set_xlabel("Capture time (s)"); ax.set_ylabel("Cumulative coverage (%)"); ax.legend()
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def runtime_tradeoff(summary, path):
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=False)
    cols = {70: PAL["blue"], 80: PAL["orange"], 90: PAL["green"]}
    for ax, d, title in zip(axs, ("L", "S"), ("Lanes along long side", "Lanes along short side")):
        for fwd in (70, 80, 90):
            rows = sorted([s for s in summary if s["dir"] == (0 if d == "L" else 1) and s["fwd"] == fwd],
                          key=lambda s: s["alt"])
            ax.errorbar([r["alt"] for r in rows], [r["mean_s"] for r in rows],
                        yerr=[r["sd_s"] for r in rows], marker="o", ms=4, capsize=3, lw=1.3,
                        color=cols[fwd], label=f"{fwd}% forward overlap")
        ax.set_title(title, fontsize=9); ax.set_xlabel("Altitude (m)")
        ax.set_ylabel("Mean simulated duration (s)"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def heatmap(summary, path):
    import numpy as np
    alts, fwds = (20, 30, 40, 60), (70, 80, 90)
    fig, axs = plt.subplots(1, 2, figsize=(8, 3.2))
    for ax, d, title in zip(axs, (0, 1), ("Long-side lanes", "Short-side lanes")):
        M = np.zeros((len(fwds), len(alts)))
        for s in summary:
            if s["dir"] == d:
                M[fwds.index(s["fwd"]), alts.index(s["alt"])] = s["mean_s"]
        im = ax.imshow(M, cmap="viridis_r", aspect="auto")
        ax.set_xticks(range(4), [f"{a} m" for a in alts]); ax.set_yticks(range(3), [f"{f}%" for f in fwds])
        ax.grid(False); ax.set_title(title, fontsize=9)
        for i in range(3):
            for j in range(4):
                ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if M[i, j] > M.max() * .5 else "black")
        fig.colorbar(im, ax=ax, label="mean duration (s)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)
