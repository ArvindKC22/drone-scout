"""Map raster, canopy sampler and footprint-hit coverage grid (Eqs. 11, 13-14).

The report's potato canopy derivative is not redistributed here, so a *synthetic*
excess-green-like canopy raster with the same extent (29.846 x 84.618 m, 0.5 m cells)
is generated. Any raster of 0-100 canopy percentages can be dropped in via
``FieldMap.from_array``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

POTATO_W = 29.84615   # m (x, image right)
POTATO_H = 84.61764   # m (y, image bottom)


@dataclass
class FieldMap:
    width: float
    height: float
    cell: float
    canopy: np.ndarray            # (ny, nx) values 0..100, NaN = invalid
    name: str = "synthetic"

    def __post_init__(self):
        self.ny, self.nx = self.canopy.shape
        valid = ~np.isnan(self.canopy)
        self.valid = valid
        v = np.where(valid, self.canopy, 0.0)
        self._sat_v = _sat(v)
        self._sat_n = _sat(valid.astype(float))
        self.n_valid = int(valid.sum())

    # ------------------------------------------------------------------ builders
    @classmethod
    def synthetic_potato(cls, cell: float = 0.5, seed: int = 2026) -> "FieldMap":
        rng = np.random.default_rng(seed)
        nx, ny = math.ceil(POTATO_W / cell), math.ceil(POTATO_H / cell)
        xs = (np.arange(nx) + 0.5) * cell
        ys = (np.arange(ny) + 0.5) * cell
        X, Y = np.meshgrid(xs, ys)
        # plot-level vigour: blocks of ~7 m along y, smooth gradient across x
        blocks = rng.uniform(0.25, 0.95, size=math.ceil(POTATO_H / 7.0) + 1)
        level = blocks[(Y / 7.0).astype(int)] * (0.85 + 0.15 * np.sin(X / 9.0))
        rows = 0.55 + 0.45 * np.cos(2 * math.pi * X / 0.9) ** 2       # 0.9 m ridge spacing
        noise = rng.normal(0, 0.06, size=X.shape)
        canopy = np.clip(100 * (level * rows + noise), 0, 100)
        return cls(POTATO_W, POTATO_H, cell, np.round(canopy), "synthetic potato trial")

    @classmethod
    def from_array(cls, arr, width: float, height: float, name: str = "custom") -> "FieldMap":
        arr = np.asarray(arr, dtype=float)
        return cls(width, height, width / arr.shape[1], arr, name)

    # ------------------------------------------------------------------ queries
    def _bounds(self, x0, x1, y0, y1):
        c = self.cell
        i0 = max(0, math.floor(x0 / c)); i1 = min(self.nx - 1, math.floor(x1 / c))
        j0 = max(0, math.floor(y0 / c)); j1 = min(self.ny - 1, math.floor(y1 / c))
        return i0, i1, j0, j1

    def sample(self, x0, x1, y0, y1):
        """Mean canopy over valid cells touched by the footprint (Section 9)."""
        i0, i1, j0, j1 = self._bounds(x0, x1, y0, y1)
        if i1 < i0 or j1 < j0:
            return float("nan")
        n = _box(self._sat_n, i0, i1, j0, j1)
        if n <= 0:
            return float("nan")
        return _box(self._sat_v, i0, i1, j0, j1) / n / 100.0

    def data_fraction(self, x0, x1, y0, y1) -> float:
        """Share of the footprint area that lies on the map rectangle."""
        ox = max(0.0, min(x1, self.width) - max(x0, 0.0))
        oy = max(0.0, min(y1, self.height) - max(y0, 0.0))
        return (ox * oy) / max((x1 - x0) * (y1 - y0), 1e-9)


class Coverage:
    """Footprint-hit coverage on a 0.5 m raster: Coverage = 100 * Nhit / Nvalid (Eq. 11)."""

    def __init__(self, fmap: FieldMap):
        self.fmap = fmap
        self.hit = np.zeros_like(fmap.valid)
        self.n_hit = 0

    def mark(self, x0, x1, y0, y1):
        i0, i1, j0, j1 = self.fmap._bounds(x0, x1, y0, y1)
        if i1 < i0 or j1 < j0:
            return
        sub = self.hit[j0:j1 + 1, i0:i1 + 1]
        new = self.fmap.valid[j0:j1 + 1, i0:i1 + 1] & ~sub
        self.n_hit += int(new.sum())
        sub |= new

    @property
    def percent(self) -> float:
        return 100.0 * self.n_hit / max(self.fmap.n_valid, 1)


def _sat(a):
    s = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
    s[1:, 1:] = a.cumsum(0).cumsum(1)
    return s


def _box(s, i0, i1, j0, j1):
    return s[j1 + 1, i1 + 1] - s[j0, i1 + 1] - s[j1 + 1, i0] + s[j0, i0]
