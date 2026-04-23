"""Compatibility package redirecting legacy imports to ``src.investing_workbench``."""

from src import investing_workbench as _investing_workbench

__all__ = getattr(_investing_workbench, "__all__", [])
__doc__ = _investing_workbench.__doc__
__path__ = _investing_workbench.__path__


def __getattr__(name: str):
    return getattr(_investing_workbench, name)
