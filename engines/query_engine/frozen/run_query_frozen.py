import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from mae_query_engine.cli import main  # noqa

if __name__ == "__main__":
    main()
