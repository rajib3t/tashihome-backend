import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.seeders.admin import main


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
