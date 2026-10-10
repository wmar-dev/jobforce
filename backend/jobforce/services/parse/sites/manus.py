# ---------------------------------------------------------------------------
# Manus (careers.manus.im) — custom SPA. h1 title is picked up generically; the
# page has no JSON-LD / og:site_name (so company_name is fixed) and no location.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

HOSTNAME = "careers.manus.im"


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Manus",
}
