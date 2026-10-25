# Reproduction check against the technical report

This repository is an **independent re-implementation** of the equations published in the report.
The report's frozen JavaScript model and its potato canopy raster are not redistributed, so the
Python package flies a *synthetic* map of the same size (29.846 × 84.618 m) with its own PRNG.
Exact agreement on stochastic runs is therefore neither expected nor claimed. What can be checked is
(a) the deterministic planner, which must match exactly, and (b) whether the stochastic results
reproduce the report's trends.

Regenerate with `python scripts/compare_to_report.py`.

## 1. Deterministic planner (exact)

| Quantity | Report | This repo |
|---|---|---|
| Baseline lanes / photos | 2 / 42 | 2 / 42 |
| Baseline survey speed (Eq. 4) | 1.965 m/s | 1.965 m/s |
| Baseline path length | 215 m | 215 m |
| Baseline time estimate (Eq. 17) | 134.975 s | 134.975 s |
| 40 m / 70 % lanes, photos, speed | 1, 11, 3.93 m/s | 1, 11, 3.93 m/s |
| Pack energy (Eq. 8) | 89.224 Wh | 89.224 Wh |

## 2. Seed-7 baseline mission (stochastic)

| Quantity | Report | This repo |
|---|---|---|
| Duration | 145.0 s | 127.7 s |
| Captures | 40 | 40 |
| Grid coverage | 100 % | 99.1 % |
| Energy | 7.605 Wh | 6.765 Wh |
| Battery remaining | 91.48 % | 92.42 % |
| Cross-track RMS | 0.810 m | 0.849 m |
| 40 m / 70 % seed 7: duration, captures | 72.6 s, 11 | 69.4 s, 11 |

## 3. 24-setting × 5-seed grid

- Spearman rank correlation of mean duration: **0.986**
- Spearman rank correlation of mean energy: **0.987**
- Mean absolute difference in mean duration: **4.6 %**
- Fastest setting meeting GSD ≤ 2.5 cm/px and ≥ 99 % coverage in every seed: report 40 m / 70 % / long side (67.16 s); here 40 m / 70 % / long side (64.78 s)
- Fastest setting for GSD ≤ 2.0 cm/px: report 30 m / 80 % / long side (125.42 s); here 30 m / 70 % / short side (172.96 s)

The GSD ≤ 2.0 cm/px choice is the least stable result: it hinges on which settings clear the 99 % coverage
bar in *every* seed, and that depends on edge-strip misses that differ between the real and synthetic
canopy masks and between PRNG streams. Treat it as sensitive to modelling details, as the report itself warns.

| Alt | Fwd | Dir | Report mean s | Repo mean s | Report Wh | Repo Wh | Report min cov % | Repo min cov % |
|--:|--:|:-:|--:|--:|--:|--:|--:|--:|
| 40 | 70 | L | 67.16 | 64.78 | 3.81 | 3.72 | 100.00 | 99.87 |
| 60 | 70 | L | 71.14 | 66.60 | 4.14 | 3.93 | 100.00 | 100.00 |
| 40 | 80 | L | 79.72 | 76.62 | 4.44 | 4.31 | 100.00 | 100.00 |
| 60 | 80 | L | 80.06 | 75.02 | 4.57 | 4.34 | 100.00 | 100.00 |
| 60 | 70 | S | 90.84 | 98.10 | 5.17 | 5.59 | 96.65 | 98.08 |
| 30 | 70 | L | 96.96 | 96.02 | 5.22 | 5.20 | 96.62 | 98.05 |
| 60 | 80 | S | 98.24 | 106.28 | 5.51 | 5.97 | 97.92 | 97.65 |
| 60 | 90 | L | 103.64 | 95.26 | 5.76 | 5.33 | 100.00 | 100.00 |
| 40 | 70 | S | 111.00 | 113.70 | 6.11 | 6.31 | 97.86 | 97.77 |
| 40 | 90 | L | 113.46 | 109.88 | 6.15 | 5.98 | 100.00 | 100.00 |
| 30 | 80 | L | 125.42 | 116.34 | 6.64 | 6.18 | 99.34 | 98.09 |
| 60 | 90 | S | 129.84 | 128.86 | 7.09 | 7.08 | 98.60 | 99.41 |
| 40 | 80 | S | 132.92 | 139.04 | 7.18 | 7.55 | 98.50 | 99.17 |
| 30 | 70 | S | 163.50 | 172.96 | 8.74 | 9.32 | 98.41 | 99.67 |
| 40 | 90 | S | 196.18 | 212.72 | 10.36 | 11.26 | 98.82 | 99.69 |
| 30 | 90 | L | 214.48 | 212.02 | 11.15 | 11.03 | 98.80 | 99.28 |
| 30 | 80 | S | 215.26 | 221.80 | 11.32 | 11.73 | 97.89 | 99.79 |
| 20 | 70 | L | 217.68 | 206.58 | 11.34 | 10.80 | 99.15 | 95.32 |
| 20 | 80 | L | 282.70 | 310.56 | 14.60 | 16.03 | 99.02 | 98.28 |
| 20 | 70 | S | 319.14 | 311.74 | 16.55 | 16.29 | 98.09 | 98.73 |
| 30 | 90 | S | 375.74 | 372.92 | 19.43 | 19.36 | 98.82 | 99.04 |
| 20 | 80 | S | 429.50 | 452.04 | 22.10 | 23.41 | 98.77 | 98.73 |
| 20 | 90 | L | 580.34 | 598.36 | 29.68 | 30.65 | 99.40 | 98.51 |
| 20 | 90 | S | 912.68 | 884.48 | 46.66 | 45.42 | 98.90 | 99.32 |
