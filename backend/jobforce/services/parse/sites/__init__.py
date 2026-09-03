"""Auto-discovery registry — every module here contributes its own adapter.

Adding a new site adapter means dropping a new module in this package that
defines an ``ADAPTER`` dict plus either ``HOSTNAME`` or ``HOSTNAMES``. No
shared registry literal to edit, so concurrent adapter work never conflicts.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

SITE_ADAPTERS: dict[str, dict[str, Any]] = {}


def _discover() -> None:
    for _finder, module_name, _ispkg in pkgutil.iter_modules(__path__):
        if module_name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{module_name}")
        adapter: dict[str, Any] | None = getattr(module, "ADAPTER", None)
        if adapter is None:
            continue
        hostnames: list[str] = getattr(module, "HOSTNAMES", None) or [module.HOSTNAME]
        for hostname in hostnames:
            SITE_ADAPTERS[hostname] = adapter


_discover()
