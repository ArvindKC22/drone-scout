"""Deterministic point-mass mission simulator (Eqs. 5-12 of the report).

The aircraft is a 3-D point mass with first-order velocity response, a
proportional-integral cross-track controller, correlated gust and GNSS noise, an
empirical power model and a return-home battery rule. It is a route-following
approximation, not an autopilot or a calibrated digital twin.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .field import Coverage, FieldMap
from .planner import Plan, plan_survey


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


@dataclass
class Capture:
    id: int
    t_s: float
    x_m: float
    y_m: float
    alt_m: float
    yaw_deg: float
    gnss_x_m: float
    gnss_y_m: float
    ground_speed_ms: float
    battery_pct: float
    footprint_w_m: float
    footprint_l_m: float
    gsd_cm: float
    data_fraction: float
    canopy: float
    coverage_pct: float

    CSV_COLUMNS = ("id", "t_s", "x_m", "y_m", "alt_m", "yaw_deg", "gnss_x_m", "gnss_y_m",
                   "ground_speed_ms", "battery_pct", "footprint_w_m", "footprint_l_m",
                   "gsd_cm", "data_fraction", "canopy", "coverage_pct")


@dataclass
class Result:
    cfg: Config
    plan: Plan
    outcome: str                   # landed | emergency_landing | low_battery_landing | timeout
    duration_s: float
    captures: list
    coverage_pct: float
    energy_wh: float
    battery_pct: float
    rms_track_m: float
    distance_m: float
    battery_swaps: int
    telemetry: dict = field(default_factory=dict)       # name -> np.ndarray (1 Hz)
    path: np.ndarray = None                             # (n,3) x,y,z @ 1 Hz

    @property
    def completed(self) -> bool:
        return self.outcome == "landed"

    def summary(self) -> dict:
        return dict(
            outcome=self.outcome, duration_s=round(self.duration_s, 1), captures=len(self.captures),
            coverage_pct=round(self.coverage_pct, 3), energy_wh=round(self.energy_wh, 3),
            battery_pct=round(self.battery_pct, 2), rms_track_m=round(self.rms_track_m, 3),
            distance_m=round(self.distance_m, 1), gsd_cm=round(self.plan.gsd_cm, 3),
            planner_time_s=round(self.plan.est_time, 2), planner_photos=self.plan.est_photos)

    def captures_csv(self) -> str:
        cols = Capture.CSV_COLUMNS
        rows = [",".join(cols)]
        for c in self.captures:
            rows.append(",".join(f"{getattr(c, k):.4g}" if isinstance(getattr(c, k), float)
                                else str(getattr(c, k)) for k in cols))
        return "\n".join(rows) + "\n"


def power_w(cfg: Config, airspeed: float, vz: float) -> float:
    """Eq. 9: empirical electrical power draw."""
    return (cfg.pload + cfg.phov * (1 + cfg.kv * airspeed ** 2)
            + cfg.mass * 9.81 * max(vz, 0.0) / cfg.eta)


def simulate(cfg: Config, fmap: FieldMap, swap_and_resume: bool = False,
             record: bool = True) -> Result:
    dt = cfg.dt
    plan = plan_survey(cfg, fmap.width, fmap.height)
    cov = Coverage(fmap)
    rng = np.random.default_rng(cfg.seed)
    normals = rng.standard_normal((cfg.max_steps + 2, 4))
    a_g = math.exp(-dt / cfg.gtau)
    a_n = math.exp(-dt / cfg.gnss_tau)
    sg, sn = cfg.gust * math.sqrt(1 - a_g ** 2), cfg.gnss * math.sqrt(1 - a_n ** 2)
    # mean wind vector: 'wdir' is the bearing the wind blows FROM (clockwise from map-up, -y)
    toward = math.radians(cfg.wdir + 180.0)
    wmx, wmy = cfg.wind * math.sin(toward), -cfg.wind * math.cos(toward)

    home = (cfg.home_x, cfg.home_y)
    # segments: (ax, ay, bx, by, kind)
    segs, prev = [], home
    for i in range(0, len(plan.waypoints), 2):
        s, e = plan.waypoints[i], plan.waypoints[i + 1]
        segs.append((*prev, s[0], s[1], "transit"))
        segs.append((s[0], s[1], e[0], e[1], "lane"))
        prev = (e[0], e[1])
    segs.append((*prev, *home, "return"))

    emax = cfg.energy_wh
    E = emax * cfg.start / 100.0
    x, y, z = home[0], home[1], 0.0
    vx = vy = vz = 0.0
    gx = gy = nx_ = ny_ = 0.0
    yaw = 0.0
    integ = 0.0
    phase = "takeoff"
    si = 0
    resume_si = None
    swaps = 0
    t = 0.0
    energy_used = 0.0
    dist = 0.0
    since = float("inf")          # distance flown since last capture
    last_cap_t = -1e9
    caps, e2sum, e2n = [], 0.0, 0
    tele = {k: [] for k in ("t", "alt", "gs", "power", "soc", "x", "y")}
    next_rec = 0.0
    outcome = "timeout"
    reach = 1.0

    def ret_energy(px, py, pz):
        d = math.dist((px, py), home)
        pr = power_w(cfg, cfg.vtr, 0.0)
        ph = power_w(cfg, 0.0, 0.0)
        return (d / cfg.vtr * pr + (1.2 * pz / cfg.vdown + 10.0) * ph) / 3600.0

    for step in range(cfg.max_steps):
        n0, n1, n2, n3 = normals[step]
        gx = a_g * gx + sg * n0; gy = a_g * gy + sg * n1
        nx_ = a_n * nx_ + sn * n2; ny_ = a_n * ny_ + sn * n3
        mx, my = x + nx_, y + ny_                       # what the controller sees
        soc = 100.0 * E / emax

        # ---- mode logic -------------------------------------------------
        tz = cfg.alt
        if phase == "takeoff":
            if z >= cfg.alt - cfg.alt_gate:
                phase = "fly"
        elif phase in ("land", "emergency"):
            tz = -0.3

        if phase == "fly":
            if z > cfg.alt - 2 * cfg.alt_gate:
                if soc <= cfg.crit:
                    phase = "emergency"
                elif segs[si][4] != "return" and E <= 1.1 * ret_energy(mx, my, z) + cfg.rthres / 100 * emax:
                    if swap_and_resume and swaps < 5:
                        resume_si = si
                    else:
                        resume_si = None
                    si = len(segs) - 1
                    segs[si] = (mx, my, *home, "return")
                    integ = 0.0
                    outcome = "low_battery_landing"
        # ---- horizontal guidance ---------------------------------------
        vgx = vgy = 0.0
        kind = None
        if phase == "fly":
            ax, ay, bx, by, kind = segs[si]
            lx, ly = bx - ax, by - ay
            ln = math.hypot(lx, ly) or 1.0
            tx, ty = lx / ln, ly / ln
            nxv, nyv = -ty, tx
            if kind == "lane":
                e = (mx - ax) * nxv + (my - ay) * nyv
                d = (bx - mx) * tx + (by - my) * ty
                u = _clamp(-cfg.kp * e - cfg.ki * integ, -3.0, 3.0)
                integ = _clamp(integ + e * dt, -8.0, 8.0)
                v = min(plan.survey_speed, math.sqrt(2 * cfg.dec * abs(d)))
                if d < 0:                      # overshot the waypoint: come back
                    v = -min(v, 1.0)
                vgx, vgy = v * tx + u * nxv, v * ty + u * nyv
                e2sum += e * e; e2n += 1
            else:
                dx, dy = bx - mx, by - my
                d = math.hypot(dx, dy)
                v = min(cfg.vtr, math.sqrt(2 * cfg.dec * d))
                if d > 1e-6:
                    vgx, vgy = v * dx / d, v * dy / d
            if math.hypot(bx - mx, by - my) < reach:
                integ = 0.0
                if kind == "return":
                    phase = "land"
                else:
                    si += 1
        elif phase in ("land", "takeoff", "emergency"):
            if phase == "land" or phase == "takeoff":
                dx, dy = home[0] - mx, home[1] - my
                d = math.hypot(dx, dy)
                v = min(2.0, math.sqrt(2 * cfg.dec * d))
                if d > 1e-6 and phase == "land":
                    vgx, vgy = v * dx / d, v * dy / d

        # ---- vertical ----------------------------------------------------
        vz_des = _clamp(1.0 * (tz - z), -cfg.vdown, cfg.vup)
        if phase == "emergency":
            vz_des = -cfg.vdown
        az = _clamp((vz_des - vz) / 0.5, -cfg.zacc, cfg.zacc)
        vz += az * dt

        # ---- horizontal dynamics (Eq. 6) ---------------------------------
        vdx, vdy = vgx - wmx, vgy - wmy                  # mean-wind feedforward
        acx, acy = (vdx - vx) / cfg.tau, (vdy - vy) / cfg.tau
        am = math.hypot(acx, acy)
        if am > cfg.acc:
            acx, acy = acx * cfg.acc / am, acy * cfg.acc / am
        vx += acx * dt; vy += acy * dt
        sp_air = math.hypot(vx, vy)
        if sp_air > cfg.vmax:
            vx, vy = vx * cfg.vmax / sp_air, vy * cfg.vmax / sp_air
            sp_air = cfg.vmax
        gvx, gvy = vx + wmx + gx, vy + wmy + gy
        x += gvx * dt; y += gvy * dt; z += vz * dt
        gs = math.hypot(gvx, gvy)
        dist += gs * dt
        since += gs * dt
        if gs > 0.3:
            target_yaw = math.degrees(math.atan2(gvx, -gvy))
            dy_ = (target_yaw - yaw + 180) % 360 - 180
            yaw += _clamp(dy_, -cfg.yawr * dt, cfg.yawr * dt)
            yaw = (yaw + 180) % 360 - 180
        if z <= 0.0:
            z = 0.0
            if vz < 0:
                vz = 0.0

        # ---- power / battery (Eqs. 9-10) ----------------------------------
        on_ground = (phase in ("land", "emergency") and z <= 0.05)
        P = 0.0 if on_ground else power_w(cfg, sp_air, vz)
        dE = P * dt / 3600.0
        E = max(0.0, E - dE); energy_used += dE
        t += dt

        # ---- capture ---------------------------------------------------------
        if (phase == "fly" and kind == "lane" and abs(z - cfg.alt) <= cfg.alt_gate
                and since >= plan.trigger_spacing and t - last_cap_t >= cfg.tmin):
            ax, ay, bx, by, _ = segs[si]
            along_y = abs(by - ay) >= abs(bx - ax)
            hx, hy = ((plan.fw, plan.fl) if along_y else (plan.fl, plan.fw))
            x0, x1, y0, y1 = x - hx / 2, x + hx / 2, y - hy / 2, y + hy / 2
            cov.mark(x0, x1, y0, y1)
            caps.append(Capture(len(caps) + 1, t, x, y, z, yaw, mx, my, gs,
                                100 * E / emax, hx, hy, plan.gsd_cm,
                                fmap.data_fraction(x0, x1, y0, y1),
                                fmap.sample(x0, x1, y0, y1), cov.percent))
            since = 0.0; last_cap_t = t

        if record and t >= next_rec:
            tele["t"].append(t); tele["alt"].append(z); tele["gs"].append(gs)
            tele["power"].append(P); tele["soc"].append(100 * E / emax)
            tele["x"].append(x); tele["y"].append(y)
            next_rec += 1.0

        # ---- termination ---------------------------------------------------------
        if phase in ("land", "emergency") and z <= 0.05:
            if phase == "land" and resume_si is not None:
                swaps += 1
                E = emax                                  # battery swap
                ax, ay = segs[resume_si][0], segs[resume_si][1]
                segs[len(segs) - 1] = (ax, ay, *home, "return")   # restore a return leg
                segs.insert(resume_si, (*home, ax, ay, "transit"))
                si = resume_si; resume_si = None
                phase = "takeoff"; outcome = "timeout"; since = float("inf")
                x, y = home; vx = vy = vz = 0.0
                continue
            z = 0.0
            outcome = ("emergency_landing" if phase == "emergency"
                       else "low_battery_landing" if outcome == "low_battery_landing" else "landed")
            break

    if record:
        tele["t"].append(t); tele["alt"].append(z); tele["gs"].append(0.0)
        tele["power"].append(0.0); tele["soc"].append(100 * E / emax)
        tele["x"].append(x); tele["y"].append(y)
    telemetry = {k: np.array(v) for k, v in tele.items()}
    path = np.column_stack([telemetry["x"], telemetry["y"], telemetry["alt"]]) if record else None
    return Result(cfg, plan, outcome, t, caps, cov.percent, energy_used, 100 * E / emax,
                  math.sqrt(e2sum / e2n) if e2n else 0.0, dist, swaps, telemetry, path)
