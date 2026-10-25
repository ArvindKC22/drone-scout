"""Tests anchored to values published in the technical report.

Plain ``unittest`` so they run with ``python -m unittest`` and under pytest alike.
"""
import unittest

import numpy as np

from dronescout import Config, FieldMap, footprint, gsd_m, plan_survey, power_w, simulate
from dronescout.benchmark import run_grid, select_best, summarize

FMAP = FieldMap.synthetic_potato()


class PlannerTests(unittest.TestCase):
    def test_gsd_and_footprint_eq1_eq2(self):
        cfg = Config()
        self.assertAlmostEqual(gsd_m(30), 0.015873, places=6)            # Section 6
        fw, fl = footprint(30, cfg)
        self.assertAlmostEqual(fw, 25.397, places=3)
        self.assertAlmostEqual(fl, 20.635, places=3)

    def test_baseline_plan_matches_report(self):
        p = plan_survey(Config(), FMAP.width, FMAP.height)
        self.assertEqual(p.n_lanes, 2)
        self.assertAlmostEqual(p.survey_speed, 1.965, places=3)           # Eq. 4
        self.assertEqual(p.est_photos, 42)                                # Section 9 / 11
        self.assertAlmostEqual(p.est_time, 134.97, delta=0.05)            # Eq. 17
        self.assertAlmostEqual(p.path_length, 215, delta=0.5)             # Fig. 3 plan panel

    def test_fast_plan_matches_report(self):
        p = plan_survey(Config(alt=40, fwd=70), FMAP.width, FMAP.height)
        self.assertEqual(p.n_lanes, 1)                                    # footprint spans the field
        self.assertAlmostEqual(p.survey_speed, 3.930, places=3)
        self.assertEqual(p.est_photos, 11)

    def test_energy_and_power_model(self):
        cfg = Config()
        self.assertAlmostEqual(cfg.energy_wh, 89.224, places=3)           # Eq. 8
        self.assertAlmostEqual(power_w(cfg, 0, 0), 177.0, places=2)       # implied stationary draw
        self.assertAlmostEqual(cfg.energy_wh / (power_w(cfg, 0, 0) / 60), 30.25, delta=0.1)


class SimulationTests(unittest.TestCase):
    def test_determinism(self):
        a = simulate(Config(seed=7), FMAP).captures_csv()
        self.assertEqual(a, simulate(Config(seed=7), FMAP).captures_csv())
        self.assertNotEqual(a, simulate(Config(seed=8), FMAP).captures_csv())

    def test_baseline_mission_is_plausible(self):
        r = simulate(Config(seed=7), FMAP)
        self.assertTrue(r.completed)
        self.assertTrue(100 < r.duration_s < 160)
        self.assertTrue(35 <= len(r.captures) <= 45)
        self.assertGreater(r.coverage_pct, 98)
        self.assertTrue(6 < r.energy_wh < 9)
        self.assertLess(r.telemetry["alt"].max(), 33)
        self.assertEqual(r.telemetry["alt"][-1], 0)

    def test_capture_spacing_respects_minimum_interval(self):
        ts = np.array([c.t_s for c in simulate(Config(seed=7), FMAP).captures])
        self.assertTrue(np.all(np.diff(ts) >= 2.0 - 1e-6))

    def test_coverage_is_monotonic(self):
        cov = [c.coverage_pct for c in simulate(Config(seed=1), FMAP).captures]
        self.assertEqual(cov, sorted(cov))
        self.assertLessEqual(cov[-1], 100.0)

    def test_higher_altitude_is_faster_up_to_one_lane(self):
        d = {a: simulate(Config(alt=a, fwd=70, seed=7), FMAP).duration_s for a in (20, 30, 40)}
        self.assertTrue(d[20] > d[30] > d[40])

    def test_low_battery_return_and_resume(self):
        cfg = Config(alt=20, fwd=90, dir=1, start=30.0)
        r = simulate(cfg, FMAP)
        self.assertEqual(r.outcome, "low_battery_landing")
        self.assertGreater(r.battery_pct, 0)
        r2 = simulate(cfg, FMAP, swap_and_resume=True)
        self.assertEqual(r2.outcome, "landed")
        self.assertGreaterEqual(r2.battery_swaps, 1)
        self.assertGreater(r2.coverage_pct, r.coverage_pct)

    def test_selection_rule(self):
        best = select_best(summarize(run_grid(FMAP, seeds=(1, 7))), 2.5)
        self.assertIsNotNone(best)
        self.assertLessEqual(best["gsd_cm"], 2.5)
        self.assertGreaterEqual(best["min_cover_pct"], 99)


if __name__ == "__main__":
    unittest.main()
