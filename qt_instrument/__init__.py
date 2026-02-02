"""
PyQt6 Instrumentation Library

Provides runtime instrumentation for PyQt6 applications to enable
testing and automation through Claude Code.

Usage:
    from qt_instrument import enable_instrumentation

    app = QApplication(sys.argv)
    enable_instrumentation(app)
"""

from .core import enable_instrumentation, InstrumentationServer

__version__ = "0.1.0"
__all__ = ["enable_instrumentation", "InstrumentationServer"]
