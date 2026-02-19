"""Estimator base class and auto-discovery mechanism."""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod

from crack_time.types import EstimateResult, PasswordAnalysis


class Estimator(ABC):
    """Base class for all attack estimators."""
    name: str = ""
    display_name: str = ""
    phase: int = 1
    estimator_type: str = "segment_level"  # or "whole_password"
    enabled: bool = True

    @abstractmethod
    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        """Estimate guess number for this attack strategy."""
        ...


def discover_estimators() -> list[Estimator]:
    """Auto-discover all Estimator subclasses in the estimators package."""
    package = importlib.import_module("crack_time.estimators")
    estimators = []

    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package.__path__):
        if module_name == "base" or module_name == "scoring":
            continue
        module = importlib.import_module(f"crack_time.estimators.{module_name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, Estimator)
                    and attr is not Estimator
                    and getattr(attr, "enabled", True)):
                estimators.append(attr())

    return estimators
