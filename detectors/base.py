#!/usr/bin/env python3
"""
Base detector class for RLHF quality detection signals.
"""

# ----------------- Futures ---------------
from __future__ import annotations

# -------------------- Standard Library ---------------
import logging
from abc import ABC, abstractmethod

# ---------------- Third Party Library ---------------
# N/A

# ------------------ Application Import ---------------
# N/A

# ------------------ Module Level Configuration ---------
logger = logging.getLogger(__name__)

class BaseDetector(ABC):

    @abstractmethod
    def detect(self, chosen: str, rejected: str) -> dict:
        """ Child classes impelent the actual detection logic"""
        pass

    @property
    @abstractmethod
    def signal_type(self) -> str:
        """ Returns the name of the detector"""
        pass
    
    def get_severity_level(self, severity: float) -> str:
        """ Classifies the severity level """
        if not (0.0 <= severity <= 1.0):
            raise ValueError(f"Severity must be between 0.0 and 1.0,got {severity}")
        if severity >= 0.90:
            return "critical"
        elif severity >= 0.70:
            return "high"
        elif severity >= 0.50:
            return "medium"
        else:
            return "low"