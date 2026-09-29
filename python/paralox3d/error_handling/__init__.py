"""Paralox3D's built-in error engine.

This package turns Python and Paralox3D errors into explanations that game
developers can understand, while preserving the normal traceback when
developer mode is enabled.
"""

from .handler import install, report_error, explain_error

__all__ = ["install", "report_error", "explain_error"]
