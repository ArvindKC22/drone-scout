"""Drone Scout: provenance-aware agricultural UAV survey simulation."""
from .config import Config
from .field import FieldMap, Coverage
from .planner import plan_survey, gsd_m, footprint, Plan
from .sim import simulate, Result, power_w

__all__ = ["Config", "FieldMap", "Coverage", "plan_survey", "gsd_m", "footprint", "Plan",
           "simulate", "Result", "power_w"]
__version__ = "1.0.0"
