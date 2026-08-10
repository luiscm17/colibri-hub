"""Warehouse adapter tests share the production adapter namespace during discovery."""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
