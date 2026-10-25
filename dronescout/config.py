"""Aircraft, mission and environment parameters.

Defaults are the baseline configuration of Appendix A of the technical report.
Reference-aircraft values are based on the published DJI Phantom 4 Multispectral
specifications; everything else is a simulation assumption.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace


@dataclass(frozen=True)
class Config:
    # --- airframe -------------------------------------------------------
    mass: float = 1.487        # kg
    cap_mah: float = 5870.0    # mAh
    vnom: float = 15.2         # V
    vmax: float = 14.0         # m/s   max airspeed
    vup: float = 6.0           # m/s   max climb speed
    vdown: float = 3.0         # m/s   max descent speed
    acc: float = 3.0           # m/s^2 horizontal acceleration limit
    dec: float = 3.0           # m/s^2 braking deceleration used by the controller
    tau: float = 0.7           # s     velocity response time
    zacc: float = 3.0          # m/s^2 vertical acceleration limit
    yawr: float = 90.0         # deg/s yaw-rate limit
    # --- camera ---------------------------------------------------------
    px: int = 1600             # image columns
    py: int = 1300             # image rows
    gsdk: float = 18.9         # reference GSD constant (m per cm/pixel)
    tmin: float = 2.0          # s     minimum capture interval
    # --- controller -----------------------------------------------------
    kp: float = 0.8            # 1/s
    ki: float = 0.05           # 1/s^2
    # --- empirical power model -----------------------------------------
    phov: float = 165.0        # W
    pload: float = 12.0        # W
    kv: float = 0.004          # (m/s)^-2
    eta: float = 0.85          # climb efficiency
    start: float = 100.0       # % initial state of charge
    rthres: float = 15.0       # % reserve used by return-home rule
    crit: float = 10.0         # % critical level -> emergency landing
    # --- mission --------------------------------------------------------
    alt: float = 30.0          # m
    fwd: float = 80.0          # % forward overlap
    side: float = 70.0         # % side overlap
    vtr: float = 8.0           # m/s transit speed
    dir: int = 0               # 0 = lanes along the long side, 1 = along the short side
    # --- environment ----------------------------------------------------
    wind: float = 3.0          # m/s mean wind
    wdir: float = 270.0        # deg, direction the wind blows FROM, clockwise from map-up
    gust: float = 0.8          # m/s SD per axis
    gtau: float = 5.0          # s gust correlation time
    gnss: float = 0.75         # m SD per axis
    gnss_tau: float = 15.0     # s GNSS correlation time
    seed: int = 7

    # --- fixed implementation constants (not exported config fields) ----
    dt: float = 0.1            # s integration step
    cell: float = 0.5          # m coverage grid cell
    home_x: float = -5.0
    home_y: float = -5.0
    max_steps: int = 60_000
    alt_gate: float = 0.8      # m tolerance for takeoff gate / capture gate

    @property
    def energy_wh(self) -> float:
        return self.cap_mah * self.vnom / 1000.0          # Eq. 8

    def with_(self, **kw) -> "Config":
        return replace(self, **kw)

    def as_dict(self) -> dict:
        return asdict(self)
