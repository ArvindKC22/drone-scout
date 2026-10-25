"""Matplotlib figures for missions and studies."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PAL = dict(blue="#2b6cb0", green="#2f855a", orange="#dd6b20", red="#c53030", grey="#4a5568")
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .25, "figure.dpi": 130})

# summarize() labels lane direction "L" (long side) / "S" (short side); older callers used 0 / 1.
_DIR_KEYS = {"L": "L", 0: "L", "0": "L", "S": "S", 1: "S", "1": "S"}


def _dir(s):
    return _DIR_KEYS[s["dir"]]


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


INK, MUTED, GRID = "#1a202c", "#5a6578", "#e2e8f0"
GSD_K = 18.9  # report Eq. 1: g = h / (100 k) m/px


def runtime_tradeoff(summary, path, gsd_ceiling_cm=2.5):
    """Mean duration vs altitude, one panel per lane direction, log y-axis, +/- 1 sd."""
    import numpy as np
    from matplotlib.lines import Line2D
    style = {70: (PAL["blue"], "o"), 80: (PAL["orange"], "s"), 90: (PAL["green"], "^")}
    alts = sorted({s["alt"] for s in summary})
    best = min((s for s in summary if s["completed_all"] and s["min_cover_pct"] >= 99
                and s["gsd_cm"] <= gsd_ceiling_cm), key=lambda s: s["mean_s"], default=None)
    ymax = max(s["mean_s"] + s["sd_s"] for s in summary) * 1.35
    ymin = min(s["mean_s"] - s["sd_s"] for s in summary) * .8
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 4.5), sharey=True)
    with plt.rc_context({"axes.edgecolor": MUTED, "text.color": INK, "axes.labelcolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED}):
        for ax, d, title in zip(axs, ("L", "S"), ("Lanes along the long side", "Lanes along the short side")):
            # region where the nominal GSD exceeds the ceiling
            alt_lim = gsd_ceiling_cm * 100 * GSD_K / 100
            ax.axvspan(alt_lim, max(alts) + 5, color="#edf2f7", zorder=0)
            ax.text(alt_lim + 1, ymax / 1.12, f"GSD > {gsd_ceiling_cm:g} cm/px", fontsize=7.5,
                    color=MUTED, va="top")
            for i, fwd in enumerate((70, 80, 90)):
                rows = sorted((s for s in summary if _dir(s) == d and s["fwd"] == fwd), key=lambda s: s["alt"])
                col, mk = style[fwd]
                x = np.array([r["alt"] for r in rows], float) + (i - 1) * .7  # nudge so bars don't overlap
                y = np.array([r["mean_s"] for r in rows]); e = np.array([r["sd_s"] for r in rows])
                ax.errorbar(x, y, yerr=e, color=col, marker=mk, ms=6.5, mfc=col, mec="white", mew=1.1,
                            lw=2, capsize=3, elinewidth=1.2, zorder=3)
                ax.annotate(f"{fwd}%", (x[0], y[0]), xytext=(-9, 0), textcoords="offset points",
                            ha="right", va="center", fontsize=8, color=INK, fontweight="bold")
            if best and _dir(best) == d:
                ax.scatter([best["alt"]], [best["mean_s"]], s=330, facecolors="none", edgecolors=INK,
                           linewidths=1.4, zorder=4)
                ax.annotate(f"fastest valid setting\n{best['alt']} m · {best['fwd']}% · {best['mean_s']:.1f} s",
                            (best["alt"], best["mean_s"]), xytext=(48, 100), textcoords="offset points",
                            ha="left", fontsize=8, color=INK,
                            arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
            ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
            ax.set_xlim(min(alts) - 6, max(alts) + 5); ax.set_xticks(alts)
            ax.set_yticks([60, 100, 200, 400, 800]); ax.set_yticklabels(["60", "100", "200", "400", "800"])
            ax.minorticks_off()
            ax.set_title(title, fontsize=11, fontweight="bold", loc="left", color=INK)
            ax.set_xlabel("Altitude (m)")
            ax.grid(axis="y", color=GRID, alpha=1, lw=.8); ax.grid(axis="x", visible=False)
            ax.set_axisbelow(True)
        axs[0].set_ylabel("Mean simulated mission duration (s, log scale)")
        handles = [Line2D([0], [0], color=style[f][0], marker=style[f][1], ms=7, lw=2, mec="white",
                          label=f"{f}% forward overlap") for f in (70, 80, 90)]
        fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=9,
                   bbox_to_anchor=(.5, -.01))
        fig.suptitle("Flying higher and overlapping less is faster, until the footprint spans the field",
                     fontsize=12.5, fontweight="bold", x=.012, ha="left", color=INK)
        fig.text(.012, .905, "24 settings × 5 seeds, synthetic potato map. Markers = mean, bars = ±1 sample SD.",
                 fontsize=8.5, color=MUTED)
        fig.tight_layout(rect=(0, .07, 1, .89)); fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=.15); plt.close(fig)


def heatmap(summary, path):
    """Mean duration per (forward overlap, altitude) cell for both lane directions."""
    import numpy as np
    alts, fwds = (20, 30, 40, 60), (70, 80, 90)
    best = min((s for s in summary if s["completed_all"] and s["min_cover_pct"] >= 99 and s["gsd_cm"] <= 2.5),
               key=lambda s: s["mean_s"], default=None)
    vmax = max(s["mean_s"] for s in summary)
    from matplotlib.colors import LogNorm
    norm = LogNorm(vmin=min(s["mean_s"] for s in summary), vmax=vmax)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.9))
    im = None
    for ax, d, title in zip(axs, ("L", "S"), ("Lanes along the long side", "Lanes along the short side")):
        M = np.full((len(fwds), len(alts)), np.nan)
        for s in summary:
            if _dir(s) == d:
                M[fwds.index(s["fwd"]), alts.index(s["alt"])] = s["mean_s"]
        im = ax.imshow(M, cmap="YlGnBu_r", norm=norm, aspect="auto")
        ax.set_xticks(range(len(alts)), [f"{a} m" for a in alts]); ax.set_yticks(range(len(fwds)), [f"{f}%" for f in fwds])
        ax.set_xlabel("Altitude"); ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
        ax.set_title(title, fontsize=10.5, fontweight="bold", loc="left")
        for i in range(len(fwds)):
            for j in range(len(alts)):
                v = M[i, j]
                ax.text(j, i, f"{v:.0f} s", ha="center", va="center", fontsize=9.5, fontweight="bold",
                        color="white" if norm(v) < .45 else "#1a202c")
        if best and _dir(best) == d:
            ax.add_patch(Rectangle((alts.index(best["alt"]) - .5, fwds.index(best["fwd"]) - .5), 1, 1,
                                   fill=False, ec="#c53030", lw=2.6))
        ax.set_ylabel("Forward overlap" if d == "L" else "")
    fig.suptitle("Mean mission duration by setting (red box = fastest setting meeting 99 % coverage and 2.5 cm/px)",
                 fontsize=10.5, fontweight="bold", x=.012, ha="left")
    fig.tight_layout(rect=(0, 0, .91, .95))
    cax = fig.add_axes([.925, .16, .013, .66]); cb = fig.colorbar(im, cax=cax, label="mean duration (s, log scale)")
    from matplotlib.ticker import FixedLocator, FixedFormatter
    cb.ax.yaxis.set_major_locator(FixedLocator([100, 200, 400, 800])); cb.ax.yaxis.set_major_formatter(FixedFormatter(["100", "200", "400", "800"])); cb.ax.minorticks_off()
    fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=.15); plt.close(fig)
