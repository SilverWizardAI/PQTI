"""
Framework adapters for GUI Instrumentation Protocol.

Each adapter implements the protocol for a specific framework
(PyQt6, Electron, Playwright, etc.).
"""

from .base import FrameworkAdapter

__all__ = ["FrameworkAdapter"]
