"""Allow ``python -m core.noahlink ...`` to invoke the CLI."""

from __future__ import annotations

import sys

from core.noahlink import main

if __name__ == "__main__":  # pragma: no cover - module entry point
    sys.exit(main())
