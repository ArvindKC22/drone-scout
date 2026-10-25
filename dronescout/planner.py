"""Camera geometry and rectangular lawn-mower survey planner (Eqs. 1-4, 17)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import Config


def gsd_m(h: float, k: float = 18.9) -> float:
    """Eq. 1: ground sample distance in metres/pixel at altitude h."""
    return h / (100.0 * k)


def footprint(h: float, cfg: Config) -> tuple[float, float]:
    """Eq. 2: across-track width Fw and along-track length Fl (m)."""
    g = gsd_m(h, cfg.gsdk)
    return cfg.px * g, cfg.py * g


@dataclass
class Plan:
    n_lanes: int
    lane_xs: list            # lane centre coordinate across-track (m, map frame)
    lane_len: float          # along-track extent L
    across: float            # across-track extent A
    fw: float
    fl: float
    lane_spacing: float      # target sp
    trigger_spacing: float   # dF
    survey_speed: float      # Eq. 4
    waypoints: list = field(default_factory=list)   # (x, y, kind) kind in {'transit','lane'}
    path_length: float = 0.0
    lane_distance: float = 0.0
    transit_distance: float = 0.0
    est_photos: int = 0
    est_time: float = 0.0
    gsd_cm: float = 0.0


def plan_survey(cfg: Config, width: float, height: float) -> Plan:
    """Plan a back-and-forth survey over a [0,width] x [0,height] rectangle (map metres)."""
    h = cfg.alt
    fw, fl = footprint(h, cfg)
    os_, of_ = cfg.side / 100.0, cfg.fwd / 100.0
    sp = max(0.01, fw * (1 - os_))                 # Eq. 3
    dF = max(0.01, fl * (1 - of_))                 # Eq. 3
    long_side = max(width, height)
    short_side = min(width, height)
    along_long = (cfg.dir == 0)
    across = short_side if along_long else long_side
    L = long_side if along_long else short_side
    # lanes (Section 6)
    if across <= fw:
        n = 1
        centres = [across / 2.0]
    else:
        n = math.ceil((across - fw) / sp) + 1
        step = (across - fw) / (n - 1)
        centres = [fw / 2.0 + i * step for i in range(n)]
    # map-frame lane geometry: "long side" is the y axis for the potato-style portrait map,
    # so the along-track axis is y when the map is taller than wide (and vice versa).
    portrait = height >= width
    lanes_along_y = (portrait == along_long)
    wps = []
    for i, c in enumerate(centres):
        a, b = (0.0, L) if i % 2 == 0 else (L, 0.0)
        if lanes_along_y:
            wps.append((c, a, "lane")); wps.append((c, b, "lane"))
        else:
            wps.append((a, c, "lane")); wps.append((b, c, "lane"))
    vs = min(cfg.vmax, dF / (1.05 * cfg.tmin))     # Eq. 4
    # distances
    lane_d = n * L
    pts = [(cfg.home_x, cfg.home_y)] + [(w[0], w[1]) for w in wps] + [(cfg.home_x, cfg.home_y)]
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    trans = total - lane_d
    photos = n * (math.floor(L / dF) + 1)
    est = (lane_d / vs + trans / cfg.vtr + 3 * n + 4 * cfg.vmax / cfg.dec
           + 1.3 * h / cfg.vup + 1.2 * h / cfg.vdown)   # Eq. 17
    return Plan(n, centres, L, across, fw, fl, sp, dF, vs, wps, total, lane_d, trans,
                photos, est, gsd_m(h, cfg.gsdk) * 100.0)
